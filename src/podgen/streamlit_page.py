"""
PodGen Streamlit page — podcast generation UI.

Rendered by src/app.py as a Streamlit page. Provides:
  - Text paste OR file upload (PDF / DOCX) input
  - Step-by-step generation progress
  - Color-coded Bunty / Bubly script display
  - Audio player + download buttons for script and MP3
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

import streamlit as st

# Ensure src/ is importable when run from anywhere
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANGUAGE_MAP = {"Hindi": "hi", "Marathi": "mr"}
DOMAIN_ICONS = {"programming": "💻", "physics": "⚛️", "finance": "📈"}
PROVIDERS = {
    "gemini":    ("Google Gemini",  "gemini-2.0-flash",          "GEMINI_API_KEY"),
    "groq":      ("Groq",           "llama-3.1-8b-instant",      "GROQ_API_KEY"),
    "openai":    ("OpenAI",         "gpt-4o-mini",               "OPENAI_API_KEY"),
    "anthropic": ("Anthropic",      "claude-3-5-haiku-20241022", "ANTHROPIC_API_KEY"),
    "ollama":    ("Ollama (local)", "llama3.1",                  "(none)"),
    "lmstudio":  ("LM Studio",      "local-model",               "(none)"),
}

BUNTY_COLOR = "#1565C0"   # deep blue
BUBLY_COLOR = "#AD1457"   # deep pink

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
<style>
.pod-title { font-size:1.6rem; font-weight:700; color:#1a1a1a; margin-bottom:0.1rem; }
.pod-subtitle { color:#6c757d; font-size:0.88rem; margin-bottom:1.5rem; }
.step-badge {
  display:inline-flex; align-items:center; gap:0.4rem;
  font-size:0.75rem; font-weight:600; padding:0.25rem 0.7rem;
  border-radius:20px; margin-bottom:0.5rem;
}
.step-ok  { background:rgba(25,135,84,.12); border:1px solid #198754; color:#198754; }
.step-run { background:rgba(13,110,253,.12); border:1px solid #0d6efd;  color:#0d6efd; }
.step-err { background:rgba(220,53,69,.12);  border:1px solid #dc3545;  color:#dc3545; }
.script-box {
  border:1px solid #e9ecef; border-radius:12px; padding:1rem 1.2rem;
  max-height:420px; overflow-y:auto; background:#fafafa;
  font-family:'JetBrains Mono',monospace; font-size:0.85rem; line-height:1.8;
}
.turn-bunty { color:#1565C0; font-weight:600; }
.turn-bubly { color:#AD1457; font-weight:600; }
.turn-text  { color:#1a1a1a; font-weight:400; margin-left:0.4rem; }
</style>
"""


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

def _init_state():
    defaults = {
        "pod_script": [],
        "pod_audio_path": None,
        "pod_hinglish": "",
        "pod_error": "",
        "pod_running": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar controls (called from app.py shared sidebar)
# ---------------------------------------------------------------------------

def render_sidebar_controls():
    """Render PodGen-specific sidebar controls. Returns a config dict."""
    st.markdown('<p class="section-label">Domain</p>', unsafe_allow_html=True)
    domain = st.selectbox(
        "pod_domain", options=list(DOMAIN_ICONS), index=0,
        label_visibility="collapsed",
        format_func=lambda d: f"{DOMAIN_ICONS[d]}  {d.capitalize()}",
        key="pod_domain",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Target Language</p>', unsafe_allow_html=True)
    lang_label = st.radio("pod_lang", options=list(LANGUAGE_MAP),
                          index=0, label_visibility="collapsed", key="pod_lang")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">LLM Provider</p>', unsafe_allow_html=True)
    provider_key = st.selectbox(
        "pod_provider", options=list(PROVIDERS), index=0,
        label_visibility="collapsed",
        format_func=lambda k: PROVIDERS[k][0],
        key="pod_provider",
    )
    _, default_model, env_hint = PROVIDERS[provider_key]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Model</p>', unsafe_allow_html=True)
    llm_model = st.text_input("pod_model", value=default_model,
                               label_visibility="collapsed", key="pod_model")

    if env_hint != "(none)":
        key_set = bool(os.environ.get(env_hint))
        cls = "step-ok" if key_set else "step-err"
        txt = f"✓ {env_hint} set" if key_set else f"✗ {env_hint} missing"
        st.markdown(f'<div class="step-badge {cls}">{txt}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Podcast Turns</p>', unsafe_allow_html=True)
    num_turns = st.slider("pod_turns", min_value=4, max_value=20, value=10, step=2,
                           label_visibility="collapsed", key="pod_turns")

    return {
        "domain": domain,
        "target_language": LANGUAGE_MAP[lang_label],
        "lang_label": lang_label,
        "llm_provider": provider_key,
        "llm_model": llm_model,
        "num_turns": num_turns,
    }


# ---------------------------------------------------------------------------
# Main page renderer
# ---------------------------------------------------------------------------

def render(cfg: dict):
    """Render the full PodGen page. cfg comes from render_sidebar_controls()."""
    _init_state()
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown('<h1 class="pod-title">🎙 PodGen</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="pod-subtitle">Turn any document into a Bunty & Bubly Hinglish podcast.</p>',
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Input section
    # ------------------------------------------------------------------
    input_tab, upload_tab = st.tabs(["✏️ Paste Text", "📎 Upload File"])

    raw_text = ""
    uploaded_file = None

    with input_tab:
        raw_text = st.text_area(
            "Content",
            placeholder="Paste any English text, article, or technical content here…",
            height=180,
            label_visibility="collapsed",
        )

    with upload_tab:
        uploaded_file = st.file_uploader(
            "Upload PDF or DOCX",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            st.caption(f"Loaded: **{uploaded_file.name}**")

    # ------------------------------------------------------------------
    # Action buttons
    # ------------------------------------------------------------------
    col_gen, col_clear, _ = st.columns([1, 1, 4])
    with col_gen:
        generate_clicked = st.button("🎙 Generate Podcast", use_container_width=True)
    with col_clear:
        clear_clicked = st.button("✕  Clear", use_container_width=True)

    if clear_clicked:
        st.session_state.pod_script = []
        st.session_state.pod_audio_path = None
        st.session_state.pod_hinglish = ""
        st.session_state.pod_error = ""
        st.rerun()

    # ------------------------------------------------------------------
    # Generation pipeline
    # ------------------------------------------------------------------
    if generate_clicked:
        st.session_state.pod_error = ""
        st.session_state.pod_script = []
        st.session_state.pod_audio_path = None
        st.session_state.pod_hinglish = ""

        try:
            _run_pipeline(raw_text, uploaded_file, cfg)
        except Exception as exc:
            st.session_state.pod_error = str(exc)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    if st.session_state.pod_error:
        st.markdown(
            f'<div class="step-badge step-err">⚠ {st.session_state.pod_error}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.pod_hinglish:
        with st.expander("📄 Translated Hinglish content (DocGen output)", expanded=False):
            st.text(st.session_state.pod_hinglish[:1500] + (
                "…" if len(st.session_state.pod_hinglish) > 1500 else ""
            ))

    if st.session_state.pod_script:
        _render_script(st.session_state.pod_script)
        _render_downloads(st.session_state.pod_script, st.session_state.pod_audio_path)

    if st.session_state.pod_audio_path:
        st.markdown("### 🎵 Listen")
        with open(st.session_state.pod_audio_path, "rb") as f:
            st.audio(f.read(), format="audio/mp3")


# ---------------------------------------------------------------------------
# Pipeline runner (inside Streamlit execution context)
# ---------------------------------------------------------------------------

def _run_pipeline(raw_text: str, uploaded_file, cfg: dict):
    from podgen.document_loader import DocumentLoader
    from docgen.pipeline import InglishtranslationPipeline, TranslationConfig
    from podgen.script_generator import PodcastScriptGenerator, PodcastConfig
    from podgen.audio_generator import AudioGenerator
    from shared.utils import preprocess_for_translation

    # Step 1: Extract text
    with st.status("Step 1/4 — Extracting text…", expanded=False) as status:
        if uploaded_file:
            content = DocumentLoader.load_uploaded(uploaded_file)
        elif raw_text.strip():
            content = DocumentLoader.load_text(raw_text)
        else:
            raise ValueError("Please paste some text or upload a file.")
        # Flatten any bullet/labeled-list structure into prose before translation
        content = preprocess_for_translation(content)
        status.update(label=f"Step 1/4 — Text extracted ({len(content)} chars)", state="complete")

    # Step 2: Translate via DocGen
    with st.status("Step 2/4 — Translating to Hinglish…", expanded=False) as status:
        doc_cfg = TranslationConfig(
            domain=cfg["domain"],
            target_language=cfg["target_language"],
            llm_provider=cfg["llm_provider"],
            llm_model=cfg["llm_model"] or None,
        )
        doc_pipeline = InglishtranslationPipeline(doc_cfg)

        # Translate paragraph by paragraph (split on double newline)
        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
        translated_parts = []
        for chunk in chunks[:20]:  # cap to 20 paragraphs to avoid very long prompts
            result = doc_pipeline.translate(chunk)
            translated_parts.append(result["hinglish_roman"])

        hinglish_text = "\n\n".join(translated_parts)
        st.session_state.pod_hinglish = hinglish_text
        status.update(label="Step 2/4 — Translation complete", state="complete")

    # Step 3: Generate podcast script
    with st.status("Step 3/4 — Generating Bunty & Bubly script…", expanded=False) as status:
        pod_cfg = PodcastConfig(
            domain=cfg["domain"],
            target_language=cfg["target_language"],
            llm_provider=cfg["llm_provider"],
            llm_model=cfg["llm_model"] or None,
            num_turns=cfg["num_turns"],
        )
        gen = PodcastScriptGenerator(pod_cfg)
        script = gen.generate(hinglish_text)
        st.session_state.pod_script = script
        status.update(label=f"Step 3/4 — Script ready ({len(script)} turns)", state="complete")

    # Step 4: Synthesise audio
    with st.status("Step 4/4 — Synthesising audio with edge-tts…", expanded=False) as status:
        audio_gen = AudioGenerator(target_language=cfg["target_language"])
        tmp_path = tempfile.mktemp(suffix=".mp3")
        asyncio.run(audio_gen.generate(script, output_path=tmp_path))
        st.session_state.pod_audio_path = tmp_path
        status.update(label="Step 4/4 — Audio ready!", state="complete")


# ---------------------------------------------------------------------------
# Script display
# ---------------------------------------------------------------------------

def _render_script(script: list):
    st.markdown("### 📜 Podcast Script")
    turns_html = []
    for turn in script:
        speaker = turn.get("speaker", "")
        text = turn.get("text", "")
        color = BUNTY_COLOR if speaker == "Bunty" else BUBLY_COLOR
        turns_html.append(
            f'<div style="margin-bottom:0.6rem;">'
            f'<span style="color:{color};font-weight:700;font-family:monospace;">{speaker}:</span>'
            f'<span style="color:#1a1a1a;margin-left:0.5rem;">{text}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="script-box">{"".join(turns_html)}</div>',
        unsafe_allow_html=True,
    )


def _render_downloads(script: list, audio_path: str | None):
    st.markdown("### ⬇️ Downloads")
    col_txt, col_mp3 = st.columns(2)

    # Script TXT download
    script_txt = "\n\n".join(
        f"{t['speaker'].upper()}: {t['text']}" for t in script
    )
    with col_txt:
        st.download_button(
            "📄 Download Script (.txt)",
            data=script_txt,
            file_name="inglish_podcast.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Audio MP3 download
    with col_mp3:
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                st.download_button(
                    "🎵 Download Audio (.mp3)",
                    data=f.read(),
                    file_name="inglish_podcast.mp3",
                    mime="audio/mpeg",
                    use_container_width=True,
                )
        else:
            st.button("🎵 Audio not available", disabled=True, use_container_width=True)
