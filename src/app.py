"""
Inglish — unified Streamlit application entry point.

Two modules:
  📄 DocGen — English → Hinglish translation (three-tier pipeline)
  🎙 PodGen — Document → Bunty & Bubly Hinglish podcast

Run with:
    streamlit run src/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="Inglish",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styles
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #ffffff; color: #1a1a1a; }
section[data-testid="stSidebar"] { background: #f8f9fa; border-right: 1px solid #e9ecef; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p {
  color: #495057 !important; font-size: 0.78rem;
  letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
  color: #1a1a1a !important; text-transform: none;
  letter-spacing: 0; font-size: 0.92rem; font-weight: 400;
}
.section-label {
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: #495057; margin-bottom: 0.4rem;
}
div[data-testid="column"] .stButton button {
  width: 100%; border-radius: 8px; font-family: 'Sora', sans-serif;
  font-weight: 600; font-size: 0.9rem; padding: 0.55rem 1rem; border: none;
}
div[data-testid="column"]:first-child .stButton button {
  background: linear-gradient(135deg, #0d6efd, #0d6efd); color: #ffffff;
}
div[data-testid="column"]:last-child .stButton button {
  background: #f8f9fa; color: #495057; border: 1px solid #ced4da;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — logo + module selector
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div style="font-size:1.5rem;font-weight:700;color:#0d6efd;'
        'letter-spacing:-0.02em;margin-bottom:0.1rem;">🔤 Inglish</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:0.72rem;color:#adb5bd;margin-bottom:1.2rem;">'
        'Code-mixed translation engine</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    module = st.radio(
        "Module",
        options=["📄 DocGen — Translation", "🎙 PodGen — Podcast"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Render module-specific sidebar controls
    if module.startswith("📄"):
        from docgen.streamlit_page import render_sidebar_controls as _doc_sidebar, render as _doc_render
        cfg = _doc_sidebar()
    else:
        from podgen.streamlit_page import render_sidebar_controls as _pod_sidebar, render as _pod_render
        cfg = _pod_sidebar()

# ---------------------------------------------------------------------------
# Main area — delegate to the selected module page
# ---------------------------------------------------------------------------

if module.startswith("📄"):
    _doc_render(cfg)
else:
    _pod_render(cfg)
