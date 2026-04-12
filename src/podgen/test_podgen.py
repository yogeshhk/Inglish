"""Unit tests for the PodGen podcast generation module.

No API keys or audio hardware required — all external calls are mocked.

Run from src/:
    pytest podgen/test_podgen.py -v
"""

import sys
import asyncio
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from podgen.document_loader import DocumentLoader, _normalise
from podgen.script_generator import (
    PodcastScriptGenerator,
    PodcastConfig,
    SPEAKER_BUNTY,
    SPEAKER_BUBLY,
)
from podgen.audio_generator import AudioGenerator, _DEFAULT_VOICES
from shared.utils import load_slangs


# ===========================================================================
# DocumentLoader tests
# ===========================================================================

class TestDocumentLoaderText:
    def test_plain_text_passthrough(self):
        text = "The for loop iterates over the array."
        result = DocumentLoader.load_text(text)
        assert result == text

    def test_normalise_collapses_blank_lines(self):
        text = "line one\n\n\n\nline two"
        result = DocumentLoader.load_text(text)
        assert "\n\n\n" not in result

    def test_empty_string(self):
        assert DocumentLoader.load_text("") == ""

    def test_strips_surrounding_whitespace(self):
        assert DocumentLoader.load_text("  hello  ") == "hello"


class TestDocumentLoaderPDF:
    def test_pdf_bytes_extraction(self):
        """Mock pypdf.PdfReader to test extraction without a real PDF."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "This is page one content."
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("podgen.document_loader.DocumentLoader._extract_pdf_bytes") as mock_extract:
            mock_extract.return_value = "This is page one content."
            result = DocumentLoader.load_uploaded(_make_uploaded_file(b"fakepdf", "doc.pdf"))
        assert "page one" in result

    def test_pdf_missing_dependency_raises(self):
        """If pypdf is not installed, raise ImportError with install hint."""
        with patch.dict("sys.modules", {"pypdf": None}):
            with pytest.raises((ImportError, ModuleNotFoundError)):
                DocumentLoader._extract_pdf_bytes(b"not-a-real-pdf")


class TestDocumentLoaderDOCX:
    def test_docx_bytes_extraction(self):
        """Mock python-docx to test extraction without a real DOCX."""
        with patch("podgen.document_loader.DocumentLoader._extract_docx_bytes") as mock_extract:
            mock_extract.return_value = "Paragraph one.\nParagraph two."
            result = DocumentLoader.load_uploaded(_make_uploaded_file(b"fakedocx", "report.docx"))
        assert "Paragraph" in result

    def test_unknown_extension_treated_as_text(self):
        content = "Just some text content"
        f = _make_uploaded_file(content.encode(), "notes.txt")
        result = DocumentLoader.load_uploaded(f)
        assert result == content


# ===========================================================================
# PodcastScriptGenerator tests
# ===========================================================================

class TestPodcastScriptGenerator:
    """Tests use provider='none' pattern — mock the LLM adapter directly."""

    def _make_gen(self, num_turns: int = 4) -> PodcastScriptGenerator:
        config = PodcastConfig(
            domain="programming",
            target_language="hi",
            llm_provider="gemini",
            num_turns=num_turns,
        )
        gen = PodcastScriptGenerator.__new__(PodcastScriptGenerator)
        gen.config = config
        gen._slangs_key = "hindi"
        gen._skill = load_slangs("hindi")
        return gen

    def test_validate_turns_structure(self):
        gen = self._make_gen()
        raw = [
            {"speaker": "Bubly", "text": "Arey Bunty, aaj mast topic hai!"},
            {"speaker": "Bunty", "text": "Haan yaar, kya hoga aaj?"},
        ]
        result = gen._validate_turns(raw)
        assert len(result) == 2
        assert result[0]["speaker"] == SPEAKER_BUBLY
        assert result[1]["speaker"] == SPEAKER_BUNTY

    def test_validate_turns_normalises_case(self):
        gen = self._make_gen()
        raw = [{"speaker": "BUNTY", "text": "yaar!"}, {"speaker": "bubly", "text": "arre!"}]
        result = gen._validate_turns(raw)
        assert result[0]["speaker"] == SPEAKER_BUNTY
        assert result[1]["speaker"] == SPEAKER_BUBLY

    def test_validate_turns_skips_empty_text(self):
        gen = self._make_gen()
        raw = [{"speaker": "Bunty", "text": ""}, {"speaker": "Bubly", "text": "hello"}]
        result = gen._validate_turns(raw)
        assert len(result) == 1

    def test_parse_script_valid_json(self):
        gen = self._make_gen()
        json_str = '[{"speaker": "Bubly", "text": "Arey!"}, {"speaker": "Bunty", "text": "Haan!"}]'
        result = gen._parse_script(json_str)
        assert len(result) == 2

    def test_parse_script_with_code_fences(self):
        gen = self._make_gen()
        raw = '```json\n[{"speaker": "Bubly", "text": "Hi!"}]\n```'
        result = gen._parse_script(raw)
        assert len(result) == 1
        assert result[0]["speaker"] == SPEAKER_BUBLY

    def test_parse_script_line_fallback(self):
        gen = self._make_gen()
        raw = "Bunty: Yaar kya hoga?\nBubly: Arre sunno sunno!"
        result = gen._parse_script(raw)
        assert len(result) == 2

    def test_technical_terms_preserved_in_script(self):
        """Ensure technical terms are not modified by the script parser."""
        gen = self._make_gen()
        json_str = '[{"speaker": "Bubly", "text": "for loop array ke upar iterate karta hai"}]'
        result = gen._parse_script(json_str)
        assert "for loop" in result[0]["text"]
        assert "array" in result[0]["text"]

    def test_generate_calls_llm_and_returns_list(self):
        """Integration: mock the LLM adapter and verify generate() returns a list."""
        gen = self._make_gen(num_turns=4)
        mock_response = '[{"speaker": "Bubly", "text": "Arey!"}, {"speaker": "Bunty", "text": "Haan!"}]'
        gen._adapter = MagicMock()
        gen._adapter.generate.return_value = mock_response

        result = gen.generate("The for loop iterates over the array.")
        assert isinstance(result, list)
        assert all("speaker" in t and "text" in t for t in result)


# ===========================================================================
# AudioGenerator tests
# ===========================================================================

class TestAudioGenerator:
    def test_voice_mapping_hindi(self):
        gen = AudioGenerator(target_language="hi")
        assert "Bunty" in gen._voices
        assert "Bubly" in gen._voices
        assert gen._voices["Bunty"] != gen._voices["Bubly"]

    def test_voice_mapping_marathi(self):
        gen = AudioGenerator(target_language="mr")
        assert gen._voices["Bunty"] == load_slangs("marathi")["speakers"]["bunty"]["edge_tts_voice"]

    def test_voice_fallback_unknown_language(self):
        gen = AudioGenerator(target_language="xx")
        assert gen._voices["Bunty"] == _DEFAULT_VOICES["Bunty"]
        assert gen._voices["Bubly"] == _DEFAULT_VOICES["Bubly"]

    def test_generate_raises_on_empty_script(self):
        gen = AudioGenerator(target_language="hi")
        with pytest.raises(ValueError, match="empty"):
            asyncio.run(gen.generate([]))

    def test_generate_produces_file(self, tmp_path):
        """Mock edge-tts and pydub to test the generation pipeline."""
        gen = AudioGenerator(target_language="hi")
        script = [
            {"speaker": "Bubly", "text": "Arey Bunty!"},
            {"speaker": "Bunty", "text": "Haan yaar!"},
        ]
        fake_mp3 = b"\xff\xfb\x90\x00" * 100  # fake MP3 bytes

        async def mock_tts(text, voice):
            return fake_mp3

        mock_segment = MagicMock()
        mock_segment.__add__ = MagicMock(return_value=mock_segment)
        mock_segment.__radd__ = MagicMock(return_value=mock_segment)
        mock_segment.export = MagicMock()

        out_path = str(tmp_path / "test_podcast.mp3")

        with patch.object(AudioGenerator, "_tts_line", side_effect=mock_tts), \
             patch("podgen.audio_generator._check_edge_tts"), \
             patch("podgen.audio_generator._check_pydub"), \
             patch("podgen.audio_generator.AudioGenerator._merge_segments",
                   return_value=mock_segment):
            result = asyncio.run(gen.generate(script, output_path=out_path))

        mock_segment.export.assert_called_once_with(out_path, format="mp3")
        assert result == out_path

    def test_segment_count_matches_script_length(self):
        """_synthesise_all should return one segment per non-empty turn."""
        gen = AudioGenerator(target_language="hi")
        script = [
            {"speaker": "Bubly", "text": "Hello!"},
            {"speaker": "Bunty", "text": ""},       # empty — should be skipped
            {"speaker": "Bubly", "text": "Goodbye!"},
        ]
        fake_audio = b"\xff\xfb" * 50

        async def run():
            with patch.object(AudioGenerator, "_tts_line", return_value=fake_audio):
                return await gen._synthesise_all(script)

        segments = asyncio.run(run())
        assert len(segments) == 2  # empty turn skipped


# ===========================================================================
# Slangs YAML integrity tests
# ===========================================================================

class TestSlangYAML:
    @pytest.mark.parametrize("lang", ["hindi", "marathi"])
    def test_yaml_loads_without_error(self, lang):
        skill = load_slangs(lang)
        assert skill is not None

    @pytest.mark.parametrize("lang", ["hindi", "marathi"])
    def test_required_keys_present(self, lang):
        skill = load_slangs(lang)
        assert "language" in skill
        assert "speakers" in skill
        assert "bunty" in skill["speakers"]
        assert "bubly" in skill["speakers"]
        assert "slangs" in skill
        assert "podcast_prompt_template" in skill

    @pytest.mark.parametrize("lang", ["hindi", "marathi"])
    def test_speaker_voices_defined(self, lang):
        skill = load_slangs(lang)
        assert "edge_tts_voice" in skill["speakers"]["bunty"]
        assert "edge_tts_voice" in skill["speakers"]["bubly"]

    @pytest.mark.parametrize("lang", ["hindi", "marathi"])
    def test_prompt_template_has_placeholders(self, lang):
        skill = load_slangs(lang)
        template = skill["podcast_prompt_template"]
        for key in ("{content}", "{num_turns}", "{domain}", "{slangs_list}"):
            assert key in template, f"Missing placeholder {key} in {lang} template"


# ===========================================================================
# Helpers
# ===========================================================================

def _make_uploaded_file(data: bytes, name: str):
    """Create a mock Streamlit UploadedFile object."""
    f = MagicMock()
    f.name = name
    f.read.return_value = data
    return f


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
