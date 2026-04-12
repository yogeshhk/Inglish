"""
Audio generator — converts a Bunty/Bubly podcast script into MP3 and MP4.

Uses edge-tts (Microsoft Edge TTS, free, no API key) to synthesise each
dialogue turn with speaker-appropriate voices, then concatenates the segments
using pydub with a short silence gap between turns.

Extras:
  - SRT subtitle file generated automatically alongside the MP3
  - Title card PNG generated via Pillow (topic + Bunty/Bubly branding)
  - mp3_to_mp4() wraps audio into a video with title card + soft subtitles

Dependencies:
  pip install edge-tts pydub Pillow
  System: ffmpeg must be on PATH (required by pydub and mp3_to_mp4).

Voice selection:
  Voices are read from the slangs skill YAML (data/slangs/<language>.yaml).
  Defaults: Bunty → en-IN-PrabhatNeural, Bubly → en-IN-NeerjaNeural

Usage:
    import asyncio
    from podgen.audio_generator import AudioGenerator

    gen = AudioGenerator(target_language="hi")
    mp3 = asyncio.run(gen.generate(script, output_path="podcast.mp3"))
    # SRT is saved automatically as podcast.srt

    card = AudioGenerator.generate_title_card("Python Generators")
    mp4  = AudioGenerator.mp3_to_mp4(mp3, title_card_path=card, srt_path="podcast.srt")
"""

import asyncio
import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from shared.utils import load_slangs

logger = logging.getLogger(__name__)

# Defaults used when slangs YAML has no voice configured
_DEFAULT_VOICES: Dict[str, str] = {
    "Bunty": "en-IN-PrabhatNeural",
    "Bubly": "en-IN-NeerjaNeural",
}

# Silence between turns (milliseconds)
_TURN_SILENCE_MS = 600

# Speaker brand colours (RGB)
_BUNTY_COLOR = (21, 101, 192)   # deep blue
_BUBLY_COLOR = (173, 20, 87)    # deep pink


class AudioGenerator:
    """
    Synthesise podcast audio from a dialogue script using edge-tts.

    The generator reads voice IDs from the language-specific slangs YAML
    so voices stay consistent with the podcast persona definitions.
    """

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language
        self._voices = self._load_voices()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def generate(
        self,
        script: List[Dict[str, str]],
        output_path: Optional[str] = None,
        save_srt: bool = True,
    ) -> str:
        """
        Synthesise audio for each turn and merge into one MP3.

        An SRT subtitle file is written alongside the MP3 when save_srt=True.

        Args:
            script:      List of {"speaker": str, "text": str} dicts.
            output_path: Destination MP3 path. If None, a temp file is created.
            save_srt:    Write an SRT file at the same path with .srt extension.

        Returns:
            Absolute path to the generated MP3 file.
        """
        if not script:
            raise ValueError("Script is empty — nothing to synthesise.")

        _check_edge_tts()
        _check_pydub()

        # Filter out empty turns before synthesis so indices align with script
        valid_script = [t for t in script if t.get("text", "").strip()]

        segments = await self._synthesise_all(valid_script)
        merged, timings = self._merge_segments(segments)

        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            output_path = tmp.name
            tmp.close()

        merged.export(output_path, format="mp3")
        logger.info("Podcast audio saved to %s", output_path)

        if save_srt and timings:
            srt_path = str(Path(output_path).with_suffix(".srt"))
            _write_srt(valid_script, timings, srt_path)
            logger.info("SRT subtitles saved to %s", srt_path)

        return output_path

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    async def _synthesise_all(
        self, script: List[Dict[str, str]]
    ) -> List[bytes]:
        """Synthesise each turn sequentially (edge-tts rate limits parallel calls)."""
        segments: List[bytes] = []
        for turn in script:
            speaker = turn.get("speaker", "Bunty")
            text = turn.get("text", "").strip()
            voice = self._voices.get(speaker, _DEFAULT_VOICES.get(speaker, "en-IN-PrabhatNeural"))
            audio_bytes = await self._tts_line(text, voice)
            segments.append(audio_bytes)
        return segments

    @staticmethod
    async def _tts_line(text: str, voice: str) -> bytes:
        """Synthesise a single line with edge-tts, return raw audio bytes."""
        import edge_tts  # type: ignore

        mp3_buffer = io.BytesIO()
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.write(chunk["data"])
        return mp3_buffer.getvalue()

    # ------------------------------------------------------------------
    # Merging
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_segments(
        segments: List[bytes],
    ) -> Tuple[object, List[Tuple[int, int]]]:
        """
        Concatenate audio segments with silence between turns.

        Returns:
            (merged AudioSegment, [(start_ms, end_ms), ...] per segment)
        """
        from pydub import AudioSegment  # type: ignore

        silence = AudioSegment.silent(duration=_TURN_SILENCE_MS)
        merged = AudioSegment.empty()
        timings: List[Tuple[int, int]] = []
        pos_ms = 0

        for i, seg_bytes in enumerate(segments):
            if i > 0:
                merged += silence
                pos_ms += _TURN_SILENCE_MS
            audio = AudioSegment.from_file(io.BytesIO(seg_bytes), format="mp3")
            start = pos_ms
            end = pos_ms + len(audio)
            timings.append((start, end))
            merged += audio
            pos_ms = end

        return merged, timings

    # ------------------------------------------------------------------
    # Voice loading
    # ------------------------------------------------------------------

    def _load_voices(self) -> Dict[str, str]:
        """Read voice IDs from slangs YAML; fall back to defaults."""
        lang_key_map = {"hi": "hindi", "mr": "marathi"}
        lang_key = lang_key_map.get(self.target_language, "hindi")
        try:
            skill = load_slangs(lang_key)
            speakers = skill.get("speakers", {})
            return {
                "Bunty": speakers.get("bunty", {}).get("edge_tts_voice",
                                                        _DEFAULT_VOICES["Bunty"]),
                "Bubly": speakers.get("bubly", {}).get("edge_tts_voice",
                                                        _DEFAULT_VOICES["Bubly"]),
            }
        except FileNotFoundError:
            logger.warning("Slangs YAML not found for '%s'; using default voices.", lang_key)
            return dict(_DEFAULT_VOICES)

    # ------------------------------------------------------------------
    # Convenience: synchronous wrapper
    # ------------------------------------------------------------------

    def generate_sync(
        self,
        script: List[Dict[str, str]],
        output_path: Optional[str] = None,
        save_srt: bool = True,
    ) -> str:
        """Synchronous wrapper around generate() for non-async contexts."""
        return asyncio.run(self.generate(script, output_path, save_srt=save_srt))

    # ------------------------------------------------------------------
    # Title card generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_title_card(
        topic: str,
        output_path: Optional[str] = None,
        width: int = 1280,
        height: int = 720,
    ) -> str:
        """
        Generate a 1280×720 PNG title card for the podcast episode.

        Includes: podcast branding, episode topic, Bunty & Bubly speaker labels.

        Args:
            topic:       Episode topic string (e.g. "Python Generators").
            output_path: Destination PNG path. Defaults to a temp file.
            width/height: Image dimensions (default 1280×720).

        Returns:
            Absolute path to the generated PNG file.
        """
        _check_pillow()
        from PIL import Image, ImageDraw, ImageFont  # type: ignore

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Background: vertical gradient from dark navy to dark slate
        top_color    = (10, 15, 35)
        bottom_color = (25, 30, 55)
        for y in range(height):
            t = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Accent bar at top
        draw.rectangle([(0, 0), (width, 6)], fill=_BUNTY_COLOR)
        draw.rectangle([(0, 6), (width, 12)], fill=_BUBLY_COLOR)

        # Load fonts — try common system fonts, fall back to PIL default
        def _font(size: int):
            candidates = [
                "C:/Windows/Fonts/calibrib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
            for path in candidates:
                if Path(path).exists():
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        pass
            return ImageFont.load_default()

        def _font_regular(size: int):
            candidates = [
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            for path in candidates:
                if Path(path).exists():
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        pass
            return ImageFont.load_default()

        # Podcast title
        title_font = _font(52)
        podcast_label = "Inglish Podcast"
        draw.text((width // 2, 80), podcast_label, font=title_font,
                  fill=(220, 220, 255), anchor="mm")

        # Divider line
        draw.line([(width // 2 - 300, 130), (width // 2 + 300, 130)],
                  fill=(80, 80, 120), width=2)

        # Episode topic (may be long — wrap at ~40 chars per line)
        topic_font = _font(64)
        topic_lines = _wrap_text(topic, max_chars=36)
        line_h = 80
        total_h = len(topic_lines) * line_h
        start_y = height // 2 - total_h // 2
        for i, line in enumerate(topic_lines):
            draw.text((width // 2, start_y + i * line_h), line,
                      font=topic_font, fill=(255, 255, 255), anchor="mm")

        # Speaker badges at bottom
        badge_y = height - 120
        badge_w, badge_h, badge_r = 220, 56, 12
        label_font = _font_regular(28)

        # Bunty badge (left)
        bx = width // 2 - 240
        _rounded_rect(draw, bx - badge_w // 2, badge_y - badge_h // 2,
                      bx + badge_w // 2, badge_y + badge_h // 2,
                      badge_r, fill=_BUNTY_COLOR)
        draw.text((bx, badge_y), "Bunty", font=label_font,
                  fill=(255, 255, 255), anchor="mm")

        # Bubly badge (right)
        bx2 = width // 2 + 240
        _rounded_rect(draw, bx2 - badge_w // 2, badge_y - badge_h // 2,
                      bx2 + badge_w // 2, badge_y + badge_h // 2,
                      badge_r, fill=_BUBLY_COLOR)
        draw.text((bx2, badge_y), "Bubly", font=label_font,
                  fill=(255, 255, 255), anchor="mm")

        # Tagline
        tag_font = _font_regular(24)
        draw.text((width // 2, height - 40),
                  "English -> Hinglish | Technical made conversational",
                  font=tag_font, fill=(120, 120, 160), anchor="mm")

        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            output_path = tmp.name
            tmp.close()

        img.save(output_path)
        logger.info("Title card saved to %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # MP4 conversion (with optional title card + subtitles)
    # ------------------------------------------------------------------

    @staticmethod
    def mp3_to_mp4(
        mp3_path: str,
        mp4_path: Optional[str] = None,
        title_card_path: Optional[str] = None,
        srt_path: Optional[str] = None,
        background: str = "0a0f23",
    ) -> str:
        """
        Wrap an MP3 file into an MP4 video using ffmpeg.

        Args:
            mp3_path:        Path to the source MP3.
            mp4_path:        Destination MP4 path (default: same stem as MP3).
            title_card_path: PNG image to use as the video frame. If None,
                             a solid colour background is used instead.
            srt_path:        SRT subtitle file to embed as a soft subtitle
                             track (toggleable in any player). If None, no
                             subtitles are added.
            background:      Hex colour used when title_card_path is None.

        Returns:
            Absolute path to the generated MP4 file.
        """
        mp3 = Path(mp3_path)
        if mp4_path is None:
            mp4_path = str(mp3.with_suffix(".mp4"))

        # Build ffmpeg input arguments
        if title_card_path and Path(title_card_path).exists():
            video_inputs = ["-loop", "1", "-i", title_card_path]
        else:
            video_inputs = [
                "-f", "lavfi",
                "-i", f"color=c=#{background}:size=1280x720:rate=1",
            ]

        srt_inputs = ["-i", srt_path] if srt_path and Path(str(srt_path)).exists() else []
        has_srt = bool(srt_inputs)

        # Map streams and subtitle codec
        stream_mapping = ["-map", "0:v", "-map", "1:a"]
        subtitle_args: List[str] = []
        if has_srt:
            stream_mapping += ["-map", "2:s"]
            subtitle_args = ["-c:s", "mov_text",
                             "-metadata:s:s:0", "language=hin",
                             "-metadata:s:s:0", "title=Hinglish"]

        cmd = [
            "ffmpeg", "-y",
            *video_inputs,
            "-i", str(mp3),
            *srt_inputs,
            *stream_mapping,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            *subtitle_args,
            "-shortest",
            mp4_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            raise FileNotFoundError(
                "ffmpeg not found on PATH. "
                "Install: Windows: winget install ffmpeg  |  "
                "Mac: brew install ffmpeg  |  Linux: sudo apt install ffmpeg"
            )

        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg exited with code {result.returncode}:\n{result.stderr[-600:]}"
            )

        logger.info("MP4 saved to %s", mp4_path)
        return mp4_path


# ---------------------------------------------------------------------------
# SRT helpers
# ---------------------------------------------------------------------------

def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format HH:MM:SS,mmm."""
    h  = ms // 3_600_000
    ms -= h * 3_600_000
    m  = ms // 60_000
    ms -= m * 60_000
    s  = ms // 1_000
    ms -= s * 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_srt(
    script: List[Dict[str, str]],
    timings: List[Tuple[int, int]],
    srt_path: str,
) -> None:
    """Write an SRT subtitle file from script turns and their timings."""
    entries = []
    for i, (turn, (start_ms, end_ms)) in enumerate(zip(script, timings), 1):
        speaker = turn.get("speaker", "")
        text    = turn.get("text", "").strip()
        start   = _ms_to_srt_time(start_ms)
        end     = _ms_to_srt_time(end_ms)
        entries.append(f"{i}\n{start} --> {end}\n{speaker}: {text}")
    Path(srt_path).write_text("\n\n".join(entries), encoding="utf-8")


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _wrap_text(text: str, max_chars: int) -> List[str]:
    """Wrap text at word boundaries to fit within max_chars per line."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return lines or [text]


def _rounded_rect(
    draw, x0: int, y0: int, x1: int, y1: int, radius: int, fill
) -> None:
    """Draw a rounded rectangle on a PIL ImageDraw canvas."""
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2 * radius, y0 + 2 * radius], fill=fill)
    draw.ellipse([x1 - 2 * radius, y0, x1, y0 + 2 * radius], fill=fill)
    draw.ellipse([x0, y1 - 2 * radius, x0 + 2 * radius, y1], fill=fill)
    draw.ellipse([x1 - 2 * radius, y1 - 2 * radius, x1, y1], fill=fill)


# ---------------------------------------------------------------------------
# Dependency guards
# ---------------------------------------------------------------------------

def _check_edge_tts() -> None:
    try:
        import edge_tts  # noqa: F401  type: ignore
    except ImportError:
        raise ImportError(
            "edge-tts is required for audio generation.\n"
            "Install with:  pip install edge-tts"
        )


def _check_pydub() -> None:
    try:
        import pydub  # noqa: F401  type: ignore
    except ImportError:
        raise ImportError(
            "pydub is required for audio merging.\n"
            "Install with:  pip install pydub\n"
            "Also ensure ffmpeg is on your PATH."
        )


def _check_pillow() -> None:
    try:
        from PIL import Image  # noqa: F401  type: ignore
    except ImportError:
        raise ImportError(
            "Pillow is required for title card generation.\n"
            "Install with:  pip install Pillow"
        )
