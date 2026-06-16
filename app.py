import streamlit as st
import openai
import base64

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PwC | ID Document Intelligence",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── PwC GLOBAL CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Charter:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');

  /* ── RESET & BASE ── */
  html, body, [class*="css"] {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    color: #2D2D2D;
  }

  /* ── HIDE STREAMLIT DEFAULTS ── */
  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }
  .block-container {
    padding: 0 !important;
    max-width: 100% !important;
  }

  /* ── PwC TOP NAV BAR ── */
  .pwc-topbar {
    background: #FFFFFF;
    border-bottom: 3px solid #E0301E;
    padding: 0 40px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 1px 8px rgba(0,0,0,0.08);
  }
  .pwc-topbar-left {
    display: flex;
    align-items: center;
    gap: 32px;
  }
  .pwc-logo-placeholder {
    width: 56px;
    height: 40px;
    background: #E0301E;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.5px;
    cursor: pointer;
  }
  .pwc-nav-divider {
    width: 1px;
    height: 28px;
    background: #D8D8D8;
  }
  .pwc-nav-title {
    font-size: 15px;
    font-weight: 600;
    color: #2D2D2D;
    letter-spacing: -0.01em;
  }
  .pwc-nav-subtitle {
    font-size: 11px;
    color: #767676;
    font-weight: 400;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .pwc-nav-badge {
    background: #E0301E;
    color: white;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 2px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] {
    background: #F5F5F5 !important;
    border-right: 1px solid #E0E0E0;
  }
  [data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
  }

  .sidebar-header {
    background: #2D2D2D;
    padding: 24px 20px 20px;
    margin-bottom: 0;
  }
  .sidebar-section {
    padding: 20px;
    border-bottom: 1px solid #E0E0E0;
  }
  .sidebar-label {
    font-size: 10px;
    font-weight: 700;
    color: #767676;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: block;
  }
  .sidebar-status-ok {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: #F0FFF4;
    border: 1px solid #68D391;
    border-radius: 3px;
    font-size: 12px;
    color: #276749;
    font-weight: 500;
  }
  .sidebar-status-warn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: #FFF5F5;
    border: 1px solid #FC8181;
    border-radius: 3px;
    font-size: 12px;
    color: #C53030;
    font-weight: 500;
  }
  .doc-type-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    background: white;
    border: 1px solid #D8D8D8;
    border-radius: 2px;
    font-size: 11px;
    color: #2D2D2D;
    margin: 3px 3px 3px 0;
    font-weight: 500;
  }

  /* ── MAIN LAYOUT ── */
  .main-wrapper {
    display: flex;
    min-height: calc(100vh - 64px);
  }

  /* ── HERO SECTION ── */
  .pwc-hero {
    background: linear-gradient(135deg, #2D2D2D 0%, #1A1A1A 100%);
    padding: 48px 48px 40px;
    border-bottom: 4px solid #E0301E;
    position: relative;
    overflow: hidden;
  }
  .pwc-hero::before {
    content: '';
    position: absolute;
    top: -30px;
    right: -30px;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(224,48,30,0.15) 0%, transparent 70%);
    pointer-events: none;
  }
  .pwc-hero-eyebrow {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #E0301E;
    margin-bottom: 12px;
  }
  .pwc-hero-title {
    font-size: 36px;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin-bottom: 12px;
  }
  .pwc-hero-title span {
    color: #E0301E;
  }
  .pwc-hero-desc {
    font-size: 15px;
    color: #AAAAAA;
    font-weight: 400;
    line-height: 1.6;
    max-width: 520px;
  }
  .pwc-hero-stats {
    display: flex;
    gap: 32px;
    margin-top: 28px;
    padding-top: 28px;
    border-top: 1px solid #3A3A3A;
  }
  .stat-item {
    text-align: left;
  }
  .stat-number {
    font-size: 24px;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1;
  }
  .stat-label {
    font-size: 11px;
    color: #767676;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  /* ── STEP INDICATOR ── */
  .step-bar {
    background: white;
    border-bottom: 1px solid #E0E0E0;
    padding: 0 48px;
    display: flex;
    align-items: center;
    gap: 0;
  }
  .step-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 24px 16px 0;
    margin-right: 24px;
    position: relative;
    font-size: 13px;
    color: #AAAAAA;
    font-weight: 500;
    cursor: default;
  }
  .step-item.active {
    color: #E0301E;
    border-bottom: 2px solid #E0301E;
    margin-bottom: -1px;
  }
  .step-item.done {
    color: #2D2D2D;
  }
  .step-num {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    background: #E8E8E8;
    color: #AAAAAA;
    flex-shrink: 0;
  }
  .step-item.active .step-num {
    background: #E0301E;
    color: white;
  }
  .step-item.done .step-num {
    background: #2D2D2D;
    color: white;
  }
  .step-arrow {
    color: #D8D8D8;
    margin-right: 24px;
    font-size: 16px;
  }

  /* ── CONTENT AREA ── */
  .content-area {
    padding: 36px 48px;
    background: #FAFAFA;
    min-height: 500px;
  }

  /* ── UPLOAD ZONE ── */
  .upload-zone {
    background: white;
    border: 2px dashed #D8D8D8;
    border-radius: 4px;
    padding: 48px 32px;
    text-align: center;
    transition: border-color 0.2s;
    margin-bottom: 24px;
  }
  .upload-zone:hover {
    border-color: #E0301E;
  }
  .upload-icon {
    font-size: 40px;
    margin-bottom: 16px;
  }
  .upload-title {
    font-size: 17px;
    font-weight: 600;
    color: #2D2D2D;
    margin-bottom: 6px;
  }
  .upload-sub {
    font-size: 13px;
    color: #767676;
    margin-bottom: 4px;
  }
  .upload-formats {
    font-size: 11px;
    color: #AAAAAA;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
  }

  /* ── RESULT CARD ── */
  .result-card {
    background: white;
    border: 1px solid #E0E0E0;
    border-top: 3px solid #E0301E;
    border-radius: 0 0 4px 4px;
    padding: 28px 32px;
    margin-top: 24px;
  }
  .result-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #F0F0F0;
  }
  .result-title {
    font-size: 16px;
    font-weight: 700;
    color: #2D2D2D;
    letter-spacing: -0.01em;
  }
  .result-badge {
    background: #F0FFF4;
    color: #276749;
    border: 1px solid #9AE6B4;
    padding: 4px 12px;
    border-radius: 2px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  /* ── CHAT AREA ── */
  .chat-container {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 24px;
  }
  .chat-header {
    background: #2D2D2D;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .chat-header-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #E0301E;
  }
  .chat-header-text {
    font-size: 13px;
    font-weight: 600;
    color: white;
    letter-spacing: 0.01em;
  }

  /* ── STREAMLIT WIDGET OVERRIDES ── */
  .stTextInput > div > div > input {
    border: 1px solid #D8D8D8 !important;
    border-radius: 3px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
    background: white !important;
    color: #2D2D2D !important;
    transition: border-color 0.2s !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #E0301E !important;
    box-shadow: 0 0 0 2px rgba(224,48,30,0.12) !important;
  }

  .stButton > button {
    background: #E0301E !important;
    color: white !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    letter-spacing: 0.02em !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    width: 100%;
  }
  .stButton > button:hover {
    background: #C0251A !important;
  }
  .stButton > button:disabled {
    background: #D8D8D8 !important;
    cursor: not-allowed !important;
  }

  /* Secondary button */
  .stButton.secondary > button {
    background: white !important;
    color: #2D2D2D !important;
    border: 1px solid #D8D8D8 !important;
  }
  .stButton.secondary > button:hover {
    background: #F5F5F5 !important;
  }

  [data-testid="stFileUploader"] {
    background: white;
  }
  [data-testid="stFileUploader"] > div {
    border: 1px solid #E0E0E0 !important;
    border-radius: 3px !important;
    background: white !important;
  }

  .stSpinner > div {
    border-top-color: #E0301E !important;
  }

  /* ── CHAT MESSAGES ── */
  [data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 8px 0 !important;
  }
  [data-testid="stChatMessage"][data-testid*="user"] {
    background: #FFF5F5 !important;
    border-left: 3px solid #E0301E !important;
    padding: 12px 16px !important;
    border-radius: 0 3px 3px 0 !important;
  }

  .stChatInput > div {
    border: 1px solid #D8D8D8 !important;
    border-radius: 3px !important;
    background: white !important;
  }
  .stChatInput > div:focus-within {
    border-color: #E0301E !important;
    box-shadow: 0 0 0 2px rgba(224,48,30,0.12) !important;
  }

  /* ── ALERT BOXES ── */
  .stAlert {
    border-radius: 3px !important;
    border-left: 3px solid !important;
  }

  /* ── DIVIDERS ── */
  hr {
    border: none;
    border-top: 1px solid #E0E0E0;
    margin: 24px 0;
  }

  /* ── FOOTER ── */
  .pwc-footer {
    background: #2D2D2D;
    color: #767676;
    font-size: 11px;
    padding: 16px 48px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 48px;
    border-top: 3px solid #E0301E;
  }
  .pwc-footer a {
    color: #767676;
    text-decoration: none;
  }
  .pwc-footer a:hover {
    color: #E0301E;
  }

  /* ── SECTION LABELS ── */
  .section-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #E0301E;
    margin-bottom: 8px;
    display: block;
  }
  .section-title {
    font-size: 22px;
    font-weight: 700;
    color: #2D2D2D;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
  }
  .section-desc {
    font-size: 14px;
    color: #767676;
    line-height: 1.6;
    margin-bottom: 24px;
  }

  /* ── PRIVACY NOTICE ── */
  .privacy-notice {
    background: #FFFBF0;
    border: 1px solid #F6E05E;
    border-left: 3px solid #D69E2E;
    border-radius: 0 3px 3px 0;
    padding: 12px 16px;
    font-size: 12px;
    color: #744210;
    display: flex;
    gap: 10px;
    align-items: flex-start;
    margin-top: 16px;
  }

  /* ── IMAGE PREVIEW ── */
  .img-preview-wrapper {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
  }
  .img-preview-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(45,45,45,0.85);
    color: white;
    font-size: 10px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 2px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* ── RESPONSIVE TABS EMULATION ── */
  .action-tabs {
    display: flex;
    gap: 0;
    border-bottom: 2px solid #E0E0E0;
    margin-bottom: 24px;
  }
  .action-tab {
    padding: 12px 20px;
    font-size: 13px;
    font-weight: 600;
    color: #767676;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: color 0.15s;
  }
  .action-tab.active {
    color: #E0301E;
    border-bottom-color: #E0301E;
  }

  /* ── TABLE OVERRIDE ── */
  table {
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
  }
  th {
    background: #F5F5F5;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    color: #2D2D2D;
    border-bottom: 2px solid #E0E0E0;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  td {
    padding: 10px 14px;
    border-bottom: 1px solid #F0F0F0;
    color: #2D2D2D;
  }
  tr:last-child td {
    border-bottom: none;
  }
  tr:hover td {
    background: #FAFAFA;
  }
</style>
""", unsafe_allow_html=True)

# ─── TOP NAV BAR ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="pwc-topbar">
  <div class="pwc-topbar-left">
    <div class="pwc-logo-placeholder">
      <img src="logo.png" height="36">
      PwC
    </div>
    <div class="pwc-nav-divider"></div>
    <div>
      <div class="pwc-nav-title">Document Intelligence</div>
      <div class="pwc-nav-subtitle">Identity Verification Suite</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:16px;">
    <span style="font-size:12px;color:#767676;">Tax & Legal Services</span>
    <div class="pwc-nav-badge">Beta</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "step" not in st.session_state:
    st.session_state.step = 1  # 1=upload, 2=analyse, 3=chat

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
      <div style="font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#E0301E;margin-bottom:8px;">Configuration</div>
      <div style="font-size:20px;font-weight:700;color:white;line-height:1.2;">API & Settings</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<span class="sidebar-label">OpenAI API Key</span>', unsafe_allow_html=True)
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-...",
            label_visibility="collapsed"
        )
        if api_key:
            if api_key.startswith("sk-"):
                st.markdown('<div class="sidebar-status-ok">✓ &nbsp;Clé API détectée</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="sidebar-status-warn">⚠ &nbsp;Format invalide</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="sidebar-status-warn">○ &nbsp;Clé requise pour analyser</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
      <span class="sidebar-label">Documents supportés</span>
      <div class="doc-type-pill">🇫🇷 Carte Nationale d'Identité</div>
      <div class="doc-type-pill">📘 Passeport</div>
      <div class="doc-type-pill">🚗 Permis de conduire</div>
      <div class="doc-type-pill">🌍 Titre de séjour</div>
      <div class="doc-type-pill">🏢 Carte pro / Visa</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
      <span class="sidebar-label">Modèle IA</span>
      <div style="font-size:13px;font-weight:600;color:#2D2D2D;">GPT-4o Vision</div>
      <div style="font-size:11px;color:#767676;margin-top:2px;">Extraction haute précision</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
      <span class="sidebar-label">Confidentialité</span>
      <div style="font-size:11px;color:#767676;line-height:1.6;">
        Les images ne sont pas stockées.<br>
        Transmission chiffrée TLS 1.3.<br>
        Conforme RGPD · Usage interne uniquement.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Reset button
    st.markdown("<div style='padding:16px 20px;'>", unsafe_allow_html=True)
    if st.button("↺ Nouvelle analyse", key="reset_btn"):
        st.session_state.messages = []
        st.session_state.extracted_data = None
        st.session_state.analysis_done = False
        st.session_state.step = 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── HERO ──────────────────────────────────────────────────────────────────────
step = st.session_state.step
step1_done = step > 1
step2_done = step > 2

st.markdown("""
<div class="pwc-hero">
  <div class="pwc-hero-eyebrow">PwC · Document Intelligence</div>
  <div class="pwc-hero-title">Vérification automatisée<br>des <span>pièces d'identité</span></div>
  <div class="pwc-hero-desc">
    Extrayez instantanément les données structurées de tout document d'identité officiel grâce à l'IA générative. Précision maximale, traçabilité complète.
  </div>
  <div class="pwc-hero-stats">
    <div class="stat-item">
      <div class="stat-number">+20</div>
      <div class="stat-label">Types de documents</div>
    </div>
    <div class="stat-item">
      <div class="stat-number">GPT-4o</div>
      <div class="stat-label">Vision IA</div>
    </div>
    <div class="stat-item">
      <div class="stat-number">RGPD</div>
      <div class="stat-label">Conforme</div>
    </div>
    <div class="stat-item">
      <div class="stat-number">&lt;10s</div>
      <div class="stat-label">Temps d'analyse</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── STEP INDICATOR ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="step-bar">
  <div class="step-item {'done' if step1_done else 'active'}">
    <div class="step-num">{'✓' if step1_done else '1'}</div>
    Importer le document
  </div>
  <span class="step-arrow">›</span>
  <div class="step-item {'done' if step2_done else ('active' if step == 2 else '')}">
    <div class="step-num">{'✓' if step2_done else '2'}</div>
    Analyser
  </div>
  <span class="step-arrow">›</span>
  <div class="step-item {'active' if step == 3 else ''}">
    <div class="step-num">3</div>
    Interroger les données
  </div>
</div>
""", unsafe_allow_html=True)

# ─── MAIN CONTENT AREA ─────────────────────────────────────────────────────────
st.markdown('<div class="content-area">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ÉTAPE 1 — UPLOAD
# ══════════════════════════════════════════════════════════════
if step == 1:
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown('<span class="section-label">Étape 1 — Import</span>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Importer un document</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-desc">Sélectionnez une photo nette du document à analyser. Assurez-vous que tous les champs sont lisibles et que l\'image n\'est pas floue.</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Déposer le fichier ici",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.session_state["uploaded_file_data"] = uploaded_file.read()
            st.session_state["uploaded_file_type"] = uploaded_file.type

            st.markdown('<div class="privacy-notice">⚠️ &nbsp;<div>Ce document contient des données à caractère personnel. Son traitement doit s\'inscrire dans un cadre légal défini. Usage strictement interne PwC.</div></div>', unsafe_allow_html=True)

            if st.button("Continuer vers l'analyse →", key="go_step2"):
                if not api_key:
                    st.error("Veuillez entrer votre clé API OpenAI dans la barre latérale avant de continuer.")
                else:
                    st.session_state.step = 2
                    st.rerun()

    with col_right:
        if uploaded_file or "uploaded_file_data" in st.session_state:
            st.markdown('<span class="section-label">Aperçu du document</span>', unsafe_allow_html=True)
            data = uploaded_file.read() if uploaded_file else st.session_state.get("uploaded_file_data", b"")
            if uploaded_file:
                uploaded_file.seek(0)
            if data:
                import io
                st.image(io.BytesIO(data), use_container_width=True)
                fname = getattr(uploaded_file, 'name', st.session_state.get("uploaded_file_name", "document"))
                st.markdown(f"""
                <div style="margin-top:12px;padding:10px 14px;background:white;border:1px solid #E0E0E0;border-radius:3px;">
                  <div style="font-size:11px;color:#767676;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;">Fichier</div>
                  <div style="font-size:13px;font-weight:600;color:#2D2D2D;margin-top:4px;">{fname}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:white;border:1px solid #E0E0E0;border-radius:4px;padding:40px 24px;text-align:center;color:#AAAAAA;">
              <div style="font-size:32px;margin-bottom:12px;">📄</div>
              <div style="font-size:13px;">L'aperçu apparaîtra ici</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ÉTAPE 2 — ANALYSE
# ══════════════════════════════════════════════════════════════
elif step == 2:
    import io as _io

    file_data = st.session_state.get("uploaded_file_data")
    file_name = st.session_state.get("uploaded_file_name", "document.jpg")
    file_type = st.session_state.get("uploaded_file_type", "image/jpeg")

    col_left, col_right = st.columns([2, 3], gap="large")

    with col_left:
        st.markdown('<span class="section-label">Document importé</span>', unsafe_allow_html=True)
        if file_data:
            st.image(_io.BytesIO(file_data), use_container_width=True)
        st.markdown(f"""
        <div style="margin-top:12px;padding:10px 14px;background:white;border:1px solid #E0E0E0;border-radius:3px;">
          <div style="font-size:11px;color:#767676;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;">Fichier sélectionné</div>
          <div style="font-size:13px;font-weight:600;color:#2D2D2D;margin-top:4px;">{file_name}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:16px;'>", unsafe_allow_html=True)
        if st.button("← Changer de document", key="back_btn"):
            st.session_state.step = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<span class="section-label">Étape 2 — Extraction IA</span>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Lancer l\'analyse</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-desc">GPT-4o Vision va identifier le type de document et extraire tous les champs disponibles avec leur valeur.</div>', unsafe_allow_html=True)

        if not st.session_state.analysis_done:
            if st.button("🔍  Analyser le document", key="analyze_btn"):
                if not api_key:
                    st.error("Clé API manquante.")
                elif not file_data:
                    st.error("Aucun fichier trouvé. Revenez à l'étape précédente.")
                else:
                    with st.spinner("Analyse en cours — extraction des données identitaires…"):
                        try:
                            image_b64 = base64.b64encode(file_data).decode("utf-8")
                            client = openai.OpenAI(api_key=api_key)

                            system_prompt = """Tu es un expert OCR spécialisé dans la reconnaissance de pièces d'identité officielles pour PwC.
Quand on te soumet une image de document d'identité, tu dois :
1. Identifier le TYPE de document (CNI française, passeport, permis de conduire, titre de séjour, etc.)
2. Extraire TOUTES les informations visibles de manière structurée en Markdown avec un tableau
3. Signaler les champs illisibles avec [illisible]
4. Ne JAMAIS inventer d'informations
5. Ajouter une section "Observations" sur la qualité du document

Format OBLIGATOIRE :
## 📄 Type de document : [type précis]

| Champ | Valeur |
|-------|--------|
| Nom | ... |
| Prénom(s) | ... |
| Date de naissance | ... |
| Lieu de naissance | ... |
| Nationalité | ... |
| Numéro de document | ... |
| Date de délivrance | ... |
| Date d'expiration | ... |
| Autorité de délivrance | ... |

### 🔍 Observations qualité
[Qualité image, lisibilité, champs manquants, anomalies]

### ✅ Statut de validité apparente
[Document semble valide / expiré / illisible — basé uniquement sur les dates visibles]"""

                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": [
                                        {"type": "image_url", "image_url": {
                                            "url": f"data:{file_type};base64,{image_b64}",
                                            "detail": "high"
                                        }},
                                        {"type": "text", "text": "Analyse cette pièce d'identité et extrais toutes les informations disponibles selon le format demandé."}
                                    ]}
                                ],
                                max_tokens=1500,
                                temperature=0
                            )

                            result = response.choices[0].message.content
                            st.session_state.extracted_data = result
                            st.session_state.analysis_done = True
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result
                            })
                            st.session_state.step = 3
                            st.rerun()

                        except openai.AuthenticationError:
                            st.error("❌ Clé API invalide ou expirée.")
                        except openai.RateLimitError:
                            st.error("⚠️ Limite de taux OpenAI atteinte. Veuillez patienter.")
                        except Exception as e:
                            st.error(f"Erreur lors de l'analyse : {str(e)}")
        else:
            st.success("✓ Analyse déjà effectuée.")
            if st.button("Voir les résultats →"):
                st.session_state.step = 3
                st.rerun()

# ══════════════════════════════════════════════════════════════
# ÉTAPE 3 — RÉSULTATS & CHAT
# ══════════════════════════════════════════════════════════════
elif step == 3:
    import io as _io

    col_result, col_chat = st.columns([1, 1], gap="large")

    with col_result:
        st.markdown('<span class="section-label">Résultats d\'extraction</span>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Données identifiées</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="result-header">
          <div class="result-title">Extraction GPT-4o Vision</div>
          <div class="result-badge">✓ Complété</div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.extracted_data:
            st.markdown(st.session_state.extracted_data)
        st.markdown('</div>', unsafe_allow_html=True)

        file_data = st.session_state.get("uploaded_file_data")
        if file_data:
            st.markdown("<div style='margin-top:16px;'>", unsafe_allow_html=True)
            st.markdown('<span class="section-label" style="margin-top:16px">Document analysé</span>', unsafe_allow_html=True)
            st.image(_io.BytesIO(file_data), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_chat:
        st.markdown('<span class="section-label">Étape 3 — Interrogation</span>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Questions sur le document</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-desc">Posez des questions précises sur les données extraites.</div>', unsafe_allow_html=True)

        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown("""
        <div class="chat-header">
          <div class="chat-header-dot"></div>
          <div class="chat-header-text">Assistant PwC · Document Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        # Afficher les messages
        if not st.session_state.messages:
            st.markdown("""
            <div style="padding:24px;text-align:center;color:#AAAAAA;">
              <div style="font-size:28px;margin-bottom:10px;">💬</div>
              <div style="font-size:13px;">Les résultats d'analyse apparaissent à gauche.<br>Posez vos questions ici.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        st.markdown('</div>', unsafe_allow_html=True)

        # Suggestions rapides
        st.markdown("""
        <div style="margin-top:12px;margin-bottom:8px;">
          <span style="font-size:11px;font-weight:700;color:#767676;text-transform:uppercase;letter-spacing:0.1em;">Suggestions</span>
        </div>
        """, unsafe_allow_html=True)

        suggestions = [
            "Le document est-il encore valide ?",
            "Résume les informations clés en 3 points",
            "Y a-t-il des anomalies détectées ?",
        ]
        cols = st.columns(len(suggestions))
        for i, (col, sug) in enumerate(zip(cols, suggestions)):
            with col:
                if st.button(sug, key=f"sug_{i}"):
                    st.session_state.messages.append({"role": "user", "content": sug})
                    with st.spinner("Analyse…"):
                        try:
                            client = openai.OpenAI(api_key=api_key)
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "Tu es un assistant expert PwC en documents d'identité. Réponds en français, de manière concise et professionnelle, en te basant uniquement sur les données extraites fournies."},
                                    {"role": "user", "content": f"Données extraites :\n\n{st.session_state.extracted_data}\n\nQuestion : {sug}"}
                                ],
                                max_tokens=500,
                                temperature=0.2
                            )
                            answer = response.choices[0].message.content
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        # Chat input
        if prompt := st.chat_input("Posez votre question sur ce document…"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analyse en cours…"):
                    try:
                        client = openai.OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "Tu es un assistant expert PwC en documents d'identité. Réponds en français, de manière concise et professionnelle."},
                                {"role": "user", "content": f"Données extraites :\n\n{st.session_state.extracted_data}\n\nQuestion : {prompt}"}
                            ],
                            max_tokens=500,
                            temperature=0.2
                        )
                        answer = response.choices[0].message.content
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except openai.AuthenticationError:
                        st.error("Clé API invalide.")
                    except Exception as e:
                        st.error(str(e))

st.markdown('</div>', unsafe_allow_html=True)

# ─── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pwc-footer">
  <div>© 2026 PwC. Tous droits réservés. · Usage interne uniquement · <a href="#">Politique de confidentialité</a> · <a href="#">Conditions d'utilisation</a></div>
  <div>PwC Document Intelligence v1.0 · Propulsé par GPT-4o Vision</div>
</div>
""", unsafe_allow_html=True)