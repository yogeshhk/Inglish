"""
DocGen Streamlit page — translation UI.

Rendered by src/app.py. Provides text input, translation controls,
and output display (intermediate bracketed, Roman, Devanagari).
"""

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANGUAGE_MAP  = {"Hindi": "hi", "Marathi": "mr"}
DOMAIN_ICONS  = {"programming": "💻", "physics": "⚛️", "finance": "📈"}
PROVIDERS = {
    "gemini":    ("Google Gemini",  "gemini-2.0-flash",          "GEMINI_API_KEY"),
    "groq":      ("Groq",           "llama-3.1-8b-instant",      "GROQ_API_KEY"),
    "openai":    ("OpenAI",         "gpt-4o-mini",               "OPENAI_API_KEY"),
    "anthropic": ("Anthropic",      "claude-3-5-haiku-20241022", "ANTHROPIC_API_KEY"),
    "ollama":    ("Ollama (local)", "llama3.1",                  "(none)"),
    "lmstudio":  ("LM Studio",      "local-model",               "(none)"),
}

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
<style>
.main-title { font-size:1.9rem; font-weight:700; color:#1a1a1a; margin-bottom:0.15rem; }
.main-subtitle { color:#6c757d; font-size:0.9rem; margin-bottom:2rem; font-weight:300; }
.section-label {
  font-size:0.75rem; font-weight:600; letter-spacing:0.1em;
  text-transform:uppercase; color:#495057; margin-bottom:0.4rem;
}
.stTextArea textarea {
  background:#f8f9fa !important; border:1px solid #ced4da !important;
  border-radius:10px !important; color:#1a1a1a !important;
  font-family:'JetBrains Mono',monospace !important; font-size:0.88rem !important;
}
.output-box {
  background:#f8f9fa; border:1px solid #ced4da; border-radius:10px;
  padding:1rem 1.1rem; font-family:'JetBrains Mono',monospace;
  font-size:0.88rem; line-height:1.7; color:#1a1a1a;
  min-height:80px; max-height:150px; overflow-y:auto;
  white-space:pre-wrap; word-break:break-word; margin-bottom:0.5rem;
}
.output-box.has-content { border-color:#198754; }
.output-placeholder { color:#adb5bd; font-style:italic; font-size:0.88rem; }
.status-badge {
  display:inline-flex; align-items:center; gap:0.35rem;
  font-size:0.75rem; font-weight:500; padding:0.2rem 0.6rem;
  border-radius:20px; margin-bottom:0.6rem;
}
.status-badge.success { background:rgba(25,135,84,.15); border:1px solid #198754; color:#198754; }
.status-badge.error   { background:rgba(220,53,69,.15);  border:1px solid #dc3545; color:#dc3545; }
.status-badge.info    { background:rgba(13,110,253,.15); border:1px solid #0d6efd; color:#0d6efd; }
.term-pill {
  display:inline-block; background:#e7f1ff; border:1px solid #b6d4fe;
  color:#0d6efd; font-family:'JetBrains Mono',monospace;
  font-size:0.75rem; padding:0.15rem 0.55rem; border-radius:20px;
}
.terms-container { margin-top:0.6rem; display:flex; flex-wrap:wrap; gap:0.4rem; }
</style>
"""


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

def _init_state():
    defaults = {
        "doc_output_roman": "",
        "doc_output_devanagari": "",
        "doc_intermediate": "",
        "doc_tech_terms": [],
        "doc_last_error": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

def render_sidebar_controls():
    """Render DocGen sidebar controls. Returns config dict."""
    st.markdown('<p class="section-label">Domain</p>', unsafe_allow_html=True)
    domain = st.selectbox(
        "doc_domain", options=list(DOMAIN_ICONS), index=0,
        label_visibility="collapsed",
        format_func=lambda d: f"{DOMAIN_ICONS[d]}  {d.capitalize()}",
        key="doc_domain",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Target Language</p>', unsafe_allow_html=True)
    lang_label = st.radio("doc_lang", options=list(LANGUAGE_MAP),
                          index=0, label_visibility="collapsed", key="doc_lang")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">LLM Provider</p>', unsafe_allow_html=True)
    provider_key = st.selectbox(
        "doc_provider", options=list(PROVIDERS), index=0,
        label_visibility="collapsed",
        format_func=lambda k: PROVIDERS[k][0],
        key="doc_provider",
    )
    _, default_model, env_hint = PROVIDERS[provider_key]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Model</p>', unsafe_allow_html=True)
    llm_model = st.text_input("doc_model", value=default_model,
                               label_visibility="collapsed", key="doc_model")

    if env_hint != "(none)":
        key_set = bool(os.environ.get(env_hint))
        cls = "success" if key_set else "error"
        txt = f"✓ {env_hint} set" if key_set else f"✗ {env_hint} missing"
        st.markdown(f'<div class="status-badge {cls}">{txt}</div>', unsafe_allow_html=True)

    return {
        "domain": domain,
        "target_language": LANGUAGE_MAP[lang_label],
        "lang_label": lang_label,
        "llm_provider": provider_key,
        "llm_model": llm_model,
    }


# ---------------------------------------------------------------------------
# Main page renderer
# ---------------------------------------------------------------------------

def render(cfg: dict):
    """Render the full DocGen translation page."""
    _init_state()
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">English → Inglish</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="main-subtitle">Translate technical English into code-mixed '
        'Hindi/Marathi while preserving domain terminology.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-label">Input Text</p>', unsafe_allow_html=True)
    input_text = st.text_area(
        "Input",
        placeholder="Type or paste English text here…\n\n"
                    "Example: The for loop iterates over the array of integers.",
        height=150,
        label_visibility="collapsed",
    )

    col_translate, col_clear, _ = st.columns([1, 1, 4])
    with col_translate:
        translate_clicked = st.button("⟳  Translate", use_container_width=True)
    with col_clear:
        clear_clicked = st.button("✕  Clear", use_container_width=True)

    if clear_clicked:
        for k in ("doc_output_roman", "doc_output_devanagari", "doc_intermediate", "doc_last_error"):
            st.session_state[k] = ""
        st.session_state.doc_tech_terms = []
        st.rerun()

    if translate_clicked:
        text = input_text.strip()
        st.session_state.doc_last_error = ""
        for k in ("doc_output_roman", "doc_output_devanagari", "doc_intermediate"):
            st.session_state[k] = ""
        st.session_state.doc_tech_terms = []

        if not text:
            st.session_state.doc_last_error = "Please enter some text before translating."
        else:
            try:
                from docgen.pipeline import InglishtranslationPipeline, TranslationConfig

                config = TranslationConfig(
                    domain=cfg["domain"],
                    target_language=cfg["target_language"],
                    llm_provider=cfg["llm_provider"],
                    llm_model=cfg["llm_model"] or None,
                )
                pipeline = InglishtranslationPipeline(config)
                result   = pipeline.translate(text, verbose=False)

                st.session_state.doc_intermediate      = result.get("intermediate_bracketed", "")
                st.session_state.doc_output_roman      = result.get("hinglish_roman", "")
                st.session_state.doc_output_devanagari = result.get("hinglish_devanagari", "")
                st.session_state.doc_tech_terms        = result.get("metadata", {}).get("technical_terms", [])

            except FileNotFoundError as e:
                st.session_state.doc_last_error = f"Glossary file not found: {e}"
            except EnvironmentError as e:
                st.session_state.doc_last_error = str(e)
            except Exception as e:
                st.session_state.doc_last_error = f"Translation error: {e}"

    # ------------------------------------------------------------------
    # Output display
    # ------------------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.doc_last_error:
        st.markdown(
            f'<div class="status-badge error">⚠ {st.session_state.doc_last_error}</div>',
            unsafe_allow_html=True,
        )

    def _box(content, placeholder, extra=""):
        if content:
            st.markdown(f'<div class="output-box {extra}">{content}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="output-box"><span class="output-placeholder">'
                f'{placeholder}</span></div>',
                unsafe_allow_html=True,
            )

    if st.session_state.doc_intermediate:
        st.markdown('<div class="status-badge info">✓ Translation complete</div>',
                    unsafe_allow_html=True)

    st.markdown('<p class="section-label">Intermediate (Terms Bracketed)</p>',
                unsafe_allow_html=True)
    _box(st.session_state.doc_intermediate, "Bracketed terms will appear here...")

    col_roman, col_deva = st.columns(2)
    with col_roman:
        st.markdown('<p class="section-label">Roman Script</p>', unsafe_allow_html=True)
        _box(st.session_state.doc_output_roman, "Roman translation will appear here...", "has-content")
    with col_deva:
        st.markdown('<p class="section-label">Devanagari Script</p>', unsafe_allow_html=True)
        _box(st.session_state.doc_output_devanagari, "Devanagari translation will appear here...", "has-content")

    if st.session_state.doc_tech_terms:
        pills = "".join(
            f'<span class="term-pill">{t}</span>' for t in st.session_state.doc_tech_terms
        )
        st.markdown(
            f'<div class="terms-container">'
            f'<span style="font-size:0.72rem;color:#495057;font-weight:600;'
            f'text-transform:uppercase;letter-spacing:0.07em;margin-right:0.2rem;">'
            f'Preserved terms</span>{pills}</div>',
            unsafe_allow_html=True,
        )
