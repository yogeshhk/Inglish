"""
Streamlit UI for the English to Inglish Translation System.
Run with: streamlit run streamlit_main.py
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

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

.stApp {
    background: #ffffff;
    color: #1a1a1a;
}

section[data-testid="stSidebar"] {
    background: #f8f9fa;
    border-right: 1px solid #e9ecef;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label {
    color: #495057 !important;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600;
}

section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: #1a1a1a !important;
    text-transform: none;
    letter-spacing: 0;
    font-size: 0.92rem;
    font-weight: 400;
}

section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 8px;
    color: #1a1a1a;
}

.main-title {
    font-family: 'Sora', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.15rem;
    line-height: 1.2;
}

.main-subtitle {
    color: #6c757d;
    font-size: 0.9rem;
    margin-bottom: 2rem;
    font-weight: 300;
    letter-spacing: 0.02em;
}

.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #495057;
    margin-bottom: 0.4rem;
}

.stTextArea textarea {
    background: #f8f9fa !important;
    border: 1px solid #ced4da !important;
    border-radius: 10px !important;
    color: #1a1a1a !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    line-height: 1.6 !important;
    resize: none !important;
    transition: border-color 0.2s ease;
}

.stTextArea textarea:focus {
    border-color: #0d6efd !important;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.12) !important;
}

.output-box {
    background: #f8f9fa;
    border: 1px solid #ced4da;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #1a1a1a;
    min-height: 80px;
    max-height: 150px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin-bottom: 0.5rem;
}

.output-box.has-content {
    border-color: #198754;
}

.output-placeholder {
    color: #adb5bd;
    font-style: italic;
    font-family: 'Sora', sans-serif;
    font-size: 0.88rem;
}

div[data-testid="column"] .stButton button {
    width: 100%;
    border-radius: 8px;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    padding: 0.55rem 1rem;
    transition: all 0.18s ease;
    cursor: pointer;
    border: none;
}

div[data-testid="column"]:first-child .stButton button {
    background: linear-gradient(135deg, #0d6efd, #0d6efd);
    color: #ffffff;
}

div[data-testid="column"]:first-child .stButton button:hover {
    background: linear-gradient(135deg, #0b5ed7, #0d6efd);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(13, 110, 253, 0.35);
}

div[data-testid="column"]:last-child .stButton button {
    background: #f8f9fa;
    color: #495057;
    border: 1px solid #ced4da;
}

div[data-testid="column"]:last-child .stButton button:hover {
    background: #e9ecef;
    color: #1a1a1a;
    transform: translateY(-1px);
}

.terms-container {
    margin-top: 0.6rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
}

.terms-label {
    font-size: 0.72rem;
    color: #495057;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-right: 0.2rem;
}

.term-pill {
    display: inline-block;
    background: #e7f1ff;
    border: 1px solid #b6d4fe;
    color: #0d6efd;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
}

hr {
    border: none;
    border-top: 1px solid #e9ecef;
    margin: 1.5rem 0;
}

.sidebar-logo {
    font-size: 1.4rem;
    font-weight: 700;
    color: #0d6efd;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}
.sidebar-tagline {
    font-size: 0.72rem;
    color: #adb5bd;
    margin-bottom: 1.5rem;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    margin-bottom: 0.6rem;
}
.status-badge.success {
    background: rgba(25, 135, 84, 0.15);
    border: 1px solid #198754;
    color: #198754;
}
.status-badge.error {
    background: rgba(220, 53, 69, 0.15);
    border: 1px solid #dc3545;
    color: #dc3545;
}
.status-badge.info {
    background: rgba(13, 110, 253, 0.15);
    border: 1px solid #0d6efd;
    color: #0d6efd;
}
</style>
""", unsafe_allow_html=True)
LANGUAGE_MAP = {
    "Hindi": "hi",
    "Marathi": "mr",
}

DOMAIN_ICONS = {
    "programming": "💻",
    "physics": "⚛️",
    "finance": "📈",
}


if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "output_roman" not in st.session_state:
    st.session_state.output_roman = ""
if "output_devanagari" not in st.session_state:
    st.session_state.output_devanagari = ""
if "intermediate" not in st.session_state:
    st.session_state.intermediate = ""
if "tech_terms" not in st.session_state:
    st.session_state.tech_terms = []
if "last_error" not in st.session_state:
    st.session_state.last_error = ""


with st.sidebar:
    st.markdown('<div class="sidebar-logo">🔤 Inglish</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Code-mixed translation engine</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p class="section-label">Domain</p>', unsafe_allow_html=True)
    domain = st.selectbox(
        label="Domain",
        options=["programming", "physics", "finance"],
        index=0,
        label_visibility="collapsed",
        format_func=lambda d: f"{DOMAIN_ICONS[d]}  {d.capitalize()}",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Target Language</p>', unsafe_allow_html=True)
    target_language_label = st.radio(
        label="Target Language",
        options=["Hindi", "Marathi"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">LLM Model</p>', unsafe_allow_html=True)
    llm_model = st.selectbox(
        label="Model",
        options=[
            "llama-3.1-8b-instant",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        f"""
        <div style="font-size:0.72rem; color:#484f58; line-height:1.7;">
        <b style="color:#8b949e;">Domain</b><br>{domain.capitalize()}<br><br>
        <b style="color:#8b949e;">Language</b><br>{target_language_label}<br><br>
        <b style="color:#8b949e;">Model</b><br>{llm_model}
        </div>
        """,
        unsafe_allow_html=True,
    )


target_language = LANGUAGE_MAP[target_language_label]


st.markdown('<h1 class="main-title">English → Inglish Translation</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">Translate technical English into code-mixed Hindi/Marathi '
    'while preserving domain terminology.</p>',
    unsafe_allow_html=True,
)

st.markdown('<p class="section-label">Input Text</p>', unsafe_allow_html=True)
input_text = st.text_area(
    label="Input",
    value=st.session_state.input_text,
    placeholder="Type or paste English text here…\n\nExample: The for loop iterates over the array of integers.",
    height=150,
    label_visibility="collapsed",
    key="input_area",
)

col_translate, col_clear, col_spacer = st.columns([1, 1, 4])

with col_translate:
    translate_clicked = st.button("⟳  Translate", use_container_width=True)

with col_clear:
    clear_clicked = st.button("✕  Clear", use_container_width=True)

if clear_clicked:
    st.session_state.input_text = ""
    st.session_state.output_roman = ""
    st.session_state.output_devanagari = ""
    st.session_state.intermediate = ""
    st.session_state.tech_terms = []
    st.session_state.last_error = ""
    st.rerun()

if translate_clicked:
    text = input_text.strip()
    st.session_state.last_error = ""
    st.session_state.output_roman = ""
    st.session_state.output_devanagari = ""
    st.session_state.intermediate = ""
    st.session_state.tech_terms = []

    if not text:
        st.session_state.last_error = "Please enter some text before translating."
    else:
        try:
            from pipeline import InglishtranslationPipeline, TranslationConfig

            config = TranslationConfig(
                domain=domain,
                target_language=target_language,
                llm_model=llm_model,
            )
            pipeline = InglishtranslationPipeline(config)
            result = pipeline.translate(text, verbose=False)

            st.session_state.intermediate = result.get("intermediate_bracketed", "")
            st.session_state.output_roman = result.get("hinglish_roman", "")
            st.session_state.output_devanagari = result.get("hinglish_devanagari", "")
            st.session_state.tech_terms = result.get("metadata", {}).get("technical_terms", [])

        except FileNotFoundError as e:
            st.session_state.last_error = f"Glossary file not found: {e}"
        except Exception as e:
            st.session_state.last_error = f"Translation error: {e}"

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.last_error:
    st.markdown(
        f'<div class="status-badge error">⚠ {st.session_state.last_error}</div>',
        unsafe_allow_html=True,
    )

if st.session_state.intermediate:
    st.markdown(
        '<div class="status-badge info">✓ Translation complete</div>',
        unsafe_allow_html=True,
    )
    
    st.markdown('<p class="section-label">Intermediate (Terms Bracketed)</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="output-box">{st.session_state.intermediate}</div>',
        unsafe_allow_html=True,
    )

    col_roman, col_deva = st.columns(2)
    
    with col_roman:
        st.markdown('<p class="section-label">Roman Script</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="output-box has-content">{st.session_state.output_roman}</div>',
            unsafe_allow_html=True,
        )
    
    with col_deva:
        st.markdown('<p class="section-label">Devanagari Script</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="output-box has-content">{st.session_state.output_devanagari}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.tech_terms:
        pills_html = '<div class="terms-container"><span class="terms-label">Preserved terms</span>'
        for term in st.session_state.tech_terms:
            pills_html += f'<span class="term-pill">{term}</span>'
        pills_html += '</div>'
        st.markdown(pills_html, unsafe_allow_html=True)
else:
    st.markdown('<p class="section-label">Intermediate (Terms Bracketed)</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="output-box"><span class="output-placeholder">'
        'Bracketed terms will appear here...'
        '</span></div>',
        unsafe_allow_html=True,
    )
    
    col_roman, col_deva = st.columns(2)
    
    with col_roman:
        st.markdown('<p class="section-label">Roman Script</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="output-box"><span class="output-placeholder">'
            'Roman translation will appear here...'
            '</span></div>',
            unsafe_allow_html=True,
        )
    
    with col_deva:
        st.markdown('<p class="section-label">Devanagari Script</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="output-box"><span class="output-placeholder">'
            'Devanagari translation will appear here...'
            '</span></div>',
            unsafe_allow_html=True,
        )
