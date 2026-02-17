"""
Streamlit UI for the English to Inglish Translation System.
Run with: streamlit run app.py
"""

import sys
import streamlit as st
from pathlib import Path

# Add src directory to path so pipeline modules are importable
sys.path.insert(0, str(Path(__file__).parent))

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="English → Inglish",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

/* ── Background ── */
.stApp {
    background: #0d1117;
    color: #e6edf3;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #21262d;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label {
    color: #8b949e !important;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600;
}

section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: #c9d1d9 !important;
    text-transform: none;
    letter-spacing: 0;
    font-size: 0.92rem;
    font-weight: 400;
}

/* Sidebar selectbox */
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #c9d1d9;
}

/* ── Main title ── */
.main-title {
    font-family: 'Sora', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff 0%, #bc8cff 50%, #ff7b72 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.15rem;
    line-height: 1.2;
}

.main-subtitle {
    color: #8b949e;
    font-size: 0.9rem;
    margin-bottom: 2rem;
    font-weight: 300;
    letter-spacing: 0.02em;
}

/* ── Section labels ── */
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 0.4rem;
}

/* ── Text areas ── */
.stTextArea textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    line-height: 1.6 !important;
    resize: none !important;
    transition: border-color 0.2s ease;
}

.stTextArea textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.12) !important;
}

/* Output box */
.output-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #c9d1d9;
    min-height: 220px;
    max-height: 220px;
    overflow-y: auto;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    pointer-events: none;
    white-space: pre-wrap;
    word-break: break-word;
}

.output-box.has-content {
    border-color: #238636;
}

.output-placeholder {
    color: #484f58;
    font-style: italic;
    font-family: 'Sora', sans-serif;
    font-size: 0.88rem;
}

/* ── Buttons ── */
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

/* Translate button */
div[data-testid="column"]:first-child .stButton button {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: #ffffff;
}

div[data-testid="column"]:first-child .stButton button:hover {
    background: linear-gradient(135deg, #388bfd, #58a6ff);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(56, 139, 253, 0.35);
}

/* Clear button */
div[data-testid="column"]:last-child .stButton button {
    background: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
}

div[data-testid="column"]:last-child .stButton button:hover {
    background: #30363d;
    color: #c9d1d9;
    transform: translateY(-1px);
}

/* ── Terms pill ── */
.terms-container {
    margin-top: 0.6rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
}

.terms-label {
    font-size: 0.72rem;
    color: #8b949e;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-right: 0.2rem;
}

.term-pill {
    display: inline-block;
    background: #1f2937;
    border: 1px solid #374151;
    color: #93c5fd;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
}

/* ── Divider ── */
hr {
    border: none;
    border-top: 1px solid #21262d;
    margin: 1.5rem 0;
}

/* ── Sidebar logo area ── */
.sidebar-logo {
    font-size: 1.4rem;
    font-weight: 700;
    color: #58a6ff;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}
.sidebar-tagline {
    font-size: 0.72rem;
    color: #484f58;
    margin-bottom: 1.5rem;
}

/* ── Status badge ── */
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
    background: rgba(35, 134, 54, 0.15);
    border: 1px solid #238636;
    color: #3fb950;
}
.status-badge.error {
    background: rgba(218, 54, 51, 0.12);
    border: 1px solid #da3633;
    color: #ff7b72;
}
</style>
""", unsafe_allow_html=True)


# ── Language / script maps ─────────────────────────────────────────────────────
LANGUAGE_MAP = {
    "Hindi":   "hi",
    "Marathi": "mr",
}

SCRIPT_MAP = {
    "Devanagari": "hinglish_devanagari",
    "Roman":      "hinglish_roman",
}

DOMAIN_ICONS = {
    "programming": "💻",
    "physics":     "⚛️",
    "finance":     "📈",
}


# ── Session state defaults ─────────────────────────────────────────────────────
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "output_text" not in st.session_state:
    st.session_state.output_text = ""
if "tech_terms" not in st.session_state:
    st.session_state.tech_terms = []
if "last_error" not in st.session_state:
    st.session_state.last_error = ""


# ── Sidebar ────────────────────────────────────────────────────────────────────
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
    st.markdown('<p class="section-label">Output Script</p>', unsafe_allow_html=True)
    output_script_label = st.radio(
        label="Output Script",
        options=["Devanagari", "Roman"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        f"""
        <div style="font-size:0.72rem; color:#484f58; line-height:1.7;">
        <b style="color:#8b949e;">Domain</b><br>{domain.capitalize()}<br><br>
        <b style="color:#8b949e;">Language</b><br>{target_language_label}<br><br>
        <b style="color:#8b949e;">Script</b><br>{output_script_label}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Derive config values ───────────────────────────────────────────────────────
target_language = LANGUAGE_MAP[target_language_label]
output_key      = SCRIPT_MAP[output_script_label]


# ── Main panel ────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-title">English → Inglish Translation</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">Translate technical English into code-mixed Hindi/Marathi '
    'while preserving domain terminology.</p>',
    unsafe_allow_html=True,
)

# Input area
st.markdown('<p class="section-label">Input Text</p>', unsafe_allow_html=True)
input_text = st.text_area(
    label="Input",
    value=st.session_state.input_text,
    placeholder="Type or paste English text here…\n\nExample: The for loop iterates over the array of integers.",
    height=200,
    label_visibility="collapsed",
    key="input_area",
)

# Buttons
col_translate, col_clear, col_spacer = st.columns([1, 1, 4])

with col_translate:
    translate_clicked = st.button("⟳  Translate", use_container_width=True)

with col_clear:
    clear_clicked = st.button("✕  Clear", use_container_width=True)

# Handle Clear
if clear_clicked:
    st.session_state.input_text  = ""
    st.session_state.output_text = ""
    st.session_state.tech_terms  = []
    st.session_state.last_error  = ""
    st.rerun()

# Handle Translate
if translate_clicked:
    text = input_text.strip()
    st.session_state.last_error  = ""
    st.session_state.output_text = ""
    st.session_state.tech_terms  = []

    if not text:
        st.session_state.last_error = "Please enter some text before translating."
    else:
        try:
            from pipeline import InglishtranslationPipeline, TranslationConfig

            config = TranslationConfig(
                domain=domain,
                target_language=target_language,
                translator_type="baseline",
                output_format="both",
            )
            pipeline = InglishtranslationPipeline(config)
            result   = pipeline.translate(text, verbose=False)

            st.session_state.output_text = result.get(output_key, "")
            st.session_state.tech_terms  = result.get("metadata", {}).get("technical_terms", [])

        except FileNotFoundError as e:
            st.session_state.last_error = f"Glossary file not found: {e}"
        except Exception as e:
            st.session_state.last_error = f"Translation error: {e}"

# ── Output area ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p class="section-label">Output — ' + output_script_label + '</p>', unsafe_allow_html=True)

if st.session_state.last_error:
    st.markdown(
        f'<div class="status-badge error">⚠ {st.session_state.last_error}</div>',
        unsafe_allow_html=True,
    )

if st.session_state.output_text:
    st.markdown(
        f'<div class="status-badge success">✓ Translation complete</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="output-box has-content">{st.session_state.output_text}</div>',
        unsafe_allow_html=True,
    )

    # Technical terms pills
    if st.session_state.tech_terms:
        pills_html = '<div class="terms-container"><span class="terms-label">Preserved terms</span>'
        for term in st.session_state.tech_terms:
            pills_html += f'<span class="term-pill">{term}</span>'
        pills_html += '</div>'
        st.markdown(pills_html, unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="output-box"><span class="output-placeholder">'
        'Translation will appear here…'
        '</span></div>',
        unsafe_allow_html=True,
    )
