"""
Streamlit UI for the English → Inglish Translation System.

Run with:  streamlit run streamlit_main.py
"""

import os
import sys
import streamlit as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="English → Inglish",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #ffffff; color: #1a1a1a; }
section[data-testid="stSidebar"] { background: #f8f9fa; border-right: 1px solid #e9ecef; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p { color: #495057 !important; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { color: #1a1a1a !important; text-transform: none; letter-spacing: 0; font-size: 0.92rem; font-weight: 400; }
.main-title { font-family: 'Sora', sans-serif; font-size: 2.1rem; font-weight: 700; color: #1a1a1a; margin-bottom: 0.15rem; }
.main-subtitle { color: #6c757d; font-size: 0.9rem; margin-bottom: 2rem; font-weight: 300; }
.section-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #495057; margin-bottom: 0.4rem; }
.stTextArea textarea { background: #f8f9fa !important; border: 1px solid #ced4da !important; border-radius: 10px !important; color: #1a1a1a !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.88rem !important; }
.output-box { background: #f8f9fa; border: 1px solid #ced4da; border-radius: 10px; padding: 1rem 1.1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; line-height: 1.7; color: #1a1a1a; min-height: 80px; max-height: 150px; overflow-y: auto; white-space: pre-wrap; word-break: break-word; margin-bottom: 0.5rem; }
.output-box.has-content { border-color: #198754; }
.output-placeholder { color: #adb5bd; font-style: italic; font-family: 'Sora', sans-serif; font-size: 0.88rem; }
div[data-testid="column"] .stButton button { width: 100%; border-radius: 8px; font-family: 'Sora', sans-serif; font-weight: 600; font-size: 0.9rem; padding: 0.55rem 1rem; border: none; }
div[data-testid="column"]:first-child .stButton button { background: linear-gradient(135deg, #0d6efd, #0d6efd); color: #ffffff; }
div[data-testid="column"]:last-child .stButton button { background: #f8f9fa; color: #495057; border: 1px solid #ced4da; }
.terms-container { margin-top: 0.6rem; display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.terms-label { font-size: 0.72rem; color: #495057; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; margin-right: 0.2rem; }
.term-pill { display: inline-block; background: #e7f1ff; border: 1px solid #b6d4fe; color: #0d6efd; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; padding: 0.15rem 0.55rem; border-radius: 20px; }
.status-badge { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.75rem; font-weight: 500; padding: 0.2rem 0.6rem; border-radius: 20px; margin-bottom: 0.6rem; }
.status-badge.success { background: rgba(25,135,84,0.15); border: 1px solid #198754; color: #198754; }
.status-badge.error { background: rgba(220,53,69,0.15); border: 1px solid #dc3545; color: #dc3545; }
.status-badge.info { background: rgba(13,110,253,0.15); border: 1px solid #0d6efd; color: #0d6efd; }
.sidebar-logo { font-size: 1.4rem; font-weight: 700; color: #0d6efd; letter-spacing: -0.02em; margin-bottom: 0.2rem; }
.sidebar-tagline { font-size: 0.72rem; color: #adb5bd; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANGUAGE_MAP  = {"Hindi": "hi", "Marathi": "mr"}
DOMAIN_ICONS  = {"programming": "💻", "physics": "⚛️", "finance": "📈"}

# Provider → (display label, default model, env key hint)
PROVIDERS = {
    "gemini":    ("Google Gemini",  "gemini-2.0-flash",            "GEMINI_API_KEY"),
    "groq":      ("Groq",           "llama-3.1-8b-instant",        "GROQ_API_KEY"),
    "openai":    ("OpenAI",         "gpt-4o-mini",                 "OPENAI_API_KEY"),
    "anthropic": ("Anthropic",      "claude-3-5-haiku-20241022",   "ANTHROPIC_API_KEY"),
    "ollama":    ("Ollama (local)", "llama3.1",                    "(none)"),
}

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

for key, default in [
    ("output_roman", ""), ("output_devanagari", ""),
    ("intermediate", ""), ("tech_terms", []), ("last_error", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="sidebar-logo">🔤 Inglish</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Code-mixed translation engine</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p class="section-label">Domain</p>', unsafe_allow_html=True)
    domain = st.selectbox(
        "Domain", options=list(DOMAIN_ICONS), index=0,
        label_visibility="collapsed",
        format_func=lambda d: f"{DOMAIN_ICONS[d]}  {d.capitalize()}",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Target Language</p>', unsafe_allow_html=True)
    lang_label = st.radio("Target Language", options=list(LANGUAGE_MAP),
                          index=0, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">LLM Provider</p>', unsafe_allow_html=True)
    provider_key = st.selectbox(
        "Provider", options=list(PROVIDERS), index=0,
        label_visibility="collapsed",
        format_func=lambda k: PROVIDERS[k][0],
    )

    provider_label, default_model, env_hint = PROVIDERS[provider_key]
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Model</p>', unsafe_allow_html=True)
    llm_model = st.text_input("Model", value=default_model, label_visibility="collapsed")

    # Key hint
    if env_hint != "(none)":
        key_set = bool(os.environ.get(env_hint))
        badge_cls = "success" if key_set else "error"
        badge_txt = f"✓ {env_hint} set" if key_set else f"✗ {env_hint} missing"
        st.markdown(f'<div class="status-badge {badge_cls}">{badge_txt}</div>',
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f'<div style="font-size:0.72rem;color:#484f58;line-height:1.7;">'
        f'<b style="color:#8b949e;">Provider</b><br>{provider_label}<br><br>'
        f'<b style="color:#8b949e;">Model</b><br>{llm_model}<br><br>'
        f'<b style="color:#8b949e;">Language</b><br>{lang_label}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

target_language = LANGUAGE_MAP[lang_label]

st.markdown('<h1 class="main-title">English → Inglish Translation</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">Translate technical English into code-mixed Hindi/Marathi '
    'while preserving domain terminology.</p>',
    unsafe_allow_html=True,
)

st.markdown('<p class="section-label">Input Text</p>', unsafe_allow_html=True)
input_text = st.text_area(
    "Input",
    placeholder="Type or paste English text here…\n\nExample: The for loop iterates over the array of integers.",
    height=150, label_visibility="collapsed",
)

col_translate, col_clear, _ = st.columns([1, 1, 4])

with col_translate:
    translate_clicked = st.button("⟳  Translate", use_container_width=True)
with col_clear:
    clear_clicked = st.button("✕  Clear", use_container_width=True)

if clear_clicked:
    for k in ("output_roman", "output_devanagari", "intermediate", "last_error"):
        st.session_state[k] = ""
    st.session_state.tech_terms = []
    st.rerun()

if translate_clicked:
    text = input_text.strip()
    st.session_state.last_error = ""
    for k in ("output_roman", "output_devanagari", "intermediate"):
        st.session_state[k] = ""
    st.session_state.tech_terms = []

    if not text:
        st.session_state.last_error = "Please enter some text before translating."
    else:
        try:
            from pipeline import InglishtranslationPipeline, TranslationConfig

            config = TranslationConfig(
                domain=domain,
                target_language=target_language,
                llm_provider=provider_key,
                llm_model=llm_model or None,
            )
            pipeline = InglishtranslationPipeline(config)
            result   = pipeline.translate(text, verbose=False)

            st.session_state.intermediate      = result.get("intermediate_bracketed", "")
            st.session_state.output_roman      = result.get("hinglish_roman", "")
            st.session_state.output_devanagari = result.get("hinglish_devanagari", "")
            st.session_state.tech_terms        = result.get("metadata", {}).get("technical_terms", [])

        except FileNotFoundError as e:
            st.session_state.last_error = f"Glossary file not found: {e}"
        except EnvironmentError as e:
            st.session_state.last_error = str(e)
        except Exception as e:
            st.session_state.last_error = f"Translation error: {e}"

# ---------------------------------------------------------------------------
# Output display
# ---------------------------------------------------------------------------

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.last_error:
    st.markdown(
        f'<div class="status-badge error">⚠ {st.session_state.last_error}</div>',
        unsafe_allow_html=True,
    )

def _output_box(content: str, placeholder: str, extra_class: str = "") -> None:
    if content:
        st.markdown(
            f'<div class="output-box {extra_class}">{content}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="output-box"><span class="output-placeholder">{placeholder}</span></div>',
            unsafe_allow_html=True,
        )

if st.session_state.intermediate:
    st.markdown('<div class="status-badge info">✓ Translation complete</div>',
                unsafe_allow_html=True)

st.markdown('<p class="section-label">Intermediate (Terms Bracketed)</p>', unsafe_allow_html=True)
_output_box(st.session_state.intermediate, "Bracketed terms will appear here...")

col_roman, col_deva = st.columns(2)
with col_roman:
    st.markdown('<p class="section-label">Roman Script</p>', unsafe_allow_html=True)
    _output_box(st.session_state.output_roman, "Roman translation will appear here...", "has-content")
with col_deva:
    st.markdown('<p class="section-label">Devanagari Script</p>', unsafe_allow_html=True)
    _output_box(st.session_state.output_devanagari, "Devanagari translation will appear here...", "has-content")

if st.session_state.tech_terms:
    pills = "".join(f'<span class="term-pill">{t}</span>' for t in st.session_state.tech_terms)
    st.markdown(
        f'<div class="terms-container"><span class="terms-label">Preserved terms</span>{pills}</div>',
        unsafe_allow_html=True,
    )
