import streamlit as st
import openai
import base64
from PIL import Image
import io
import json
import os
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

# ─── STORAGE HELPERS ──────────────────────────────────────────────────────────
SESSIONS_DIR = "chat_sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def list_sessions():
    sessions = []
    for fname in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if fname.endswith(".json"):
            path = os.path.join(SESSIONS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "title": data.get("title", "Sans titre"),
                    "created_at": data.get("created_at", ""),
                    "doc_type": data.get("doc_type", ""),
                    "path": path
                })
            except Exception:
                pass
    return sessions

def load_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_session(session_id, data):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)

def new_session_id():
    return str(uuid.uuid4())[:8]

# ─── PYDANTIC MODELS ─────────────────────────────────────────────────────────
class DocumentClassification(BaseModel):
    type_document: str = Field(description="Type exact du document parmi : CNI, PASSEPORT, PERMIS, TITRE_SEJOUR, AUTRE")
    pays_emission: str = Field(description="Pays d'émission du document détecté")
    langue_document: str = Field(description="Langue principale du document")
    confiance_classification: float = Field(description="Niveau de confiance de la classification entre 0.0 et 1.0")
    justification: str = Field(description="Courte justification du type de document détecté")

class ExtractionCNI(BaseModel):
    Nom: str = Field(description="Nom de famille extrait du document")
    Prenoms: str = Field(description="Prénom(s) extrait(s) du document")
    Date_de_naissance: str = Field(description="Date de naissance de l'individu")
    Lieu_de_naissance: str = Field(description="Lieu de naissance de l'individu")
    Nationalite: str = Field(description="Nationalité mentionnée")
    Numero_de_document: str = Field(description="Numéro de la pièce d'identité")
    Date_de_delivrance: str = Field(description="Date d'émission du document")
    Date_d_expiration: str = Field(description="Date de fin de validité du document")
    Autorite_de_delivrance: str = Field(description="Organisme ayant délivré la pièce")
    Sexe: str = Field(description="Sexe de l'individu M/F")
    Taille: str = Field(description="Taille en cm si présente, sinon [non présent]")
    MRZ_ligne1: str = Field(description="Première ligne MRZ si visible, sinon [non visible]")
    MRZ_ligne2: str = Field(description="Deuxième ligne MRZ si visible, sinon [non visible]")
    Document_valide: bool = Field(description="True si le document n'est pas expiré")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits")
    Score_fiabilite_ocr: float = Field(description="Score de confiance de l'extraction 0.0-1.0")

class ExtractionPasseport(BaseModel):
    Nom: str = Field(description="Nom de famille extrait du document")
    Prenoms: str = Field(description="Prénom(s) extrait(s) du document")
    Date_de_naissance: str = Field(description="Date de naissance de l'individu")
    Lieu_de_naissance: str = Field(description="Lieu de naissance de l'individu")
    Nationalite: str = Field(description="Nationalité mentionnée")
    Code_pays: str = Field(description="Code pays ISO 3 lettres (ex: FRA, LUX)")
    Numero_de_document: str = Field(description="Numéro de passeport")
    Date_de_delivrance: str = Field(description="Date d'émission du document")
    Date_d_expiration: str = Field(description="Date de fin de validité du document")
    Autorite_de_delivrance: str = Field(description="Organisme ayant délivré la pièce")
    Lieu_de_delivrance: str = Field(description="Lieu de délivrance si présent, sinon [non présent]")
    Sexe: str = Field(description="Sexe de l'individu M/F")
    MRZ_ligne1: str = Field(description="Première ligne MRZ du passeport")
    MRZ_ligne2: str = Field(description="Deuxième ligne MRZ du passeport")
    Document_valide: bool = Field(description="True si le document n'est pas expiré")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits")
    Score_fiabilite_ocr: float = Field(description="Score de confiance de l'extraction 0.0-1.0")

class ExtractionPermis(BaseModel):
    Nom: str = Field(description="Nom de famille extrait du document")
    Prenoms: str = Field(description="Prénom(s) extrait(s) du document")
    Date_de_naissance: str = Field(description="Date de naissance de l'individu")
    Lieu_de_naissance: str = Field(description="Lieu de naissance de l'individu")
    Numero_de_document: str = Field(description="Numéro du permis de conduire")
    Date_de_delivrance: str = Field(description="Date d'émission du document")
    Date_d_expiration: str = Field(description="Date de fin de validité du document")
    Autorite_de_delivrance: str = Field(description="Organisme ayant délivré la pièce")
    Categories: str = Field(description="Catégories de conduite autorisées (ex: B, A, C...)")
    Restrictions: str = Field(description="Restrictions ou codes spéciaux si présents, sinon [aucune]")
    Adresse: str = Field(description="Adresse si présente sur le permis, sinon [non présent]")
    Document_valide: bool = Field(description="True si le document n'est pas expiré")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits")
    Score_fiabilite_ocr: float = Field(description="Score de confiance de l'extraction 0.0-1.0")

class ExtractionTitreSejour(BaseModel):
    Nom: str = Field(description="Nom de famille extrait du document")
    Prenoms: str = Field(description="Prénom(s) extrait(s) du document")
    Date_de_naissance: str = Field(description="Date de naissance de l'individu")
    Lieu_de_naissance: str = Field(description="Lieu de naissance de l'individu")
    Nationalite: str = Field(description="Nationalité mentionnée")
    Sexe: str = Field(description="Sexe de l'individu M/F")
    Numero_de_document: str = Field(description="Numéro du titre de séjour")
    Type_titre: str = Field(description="Type de titre (ex: Résident, Etudiant, Travailleur...)")
    Date_de_delivrance: str = Field(description="Date d'émission du document")
    Date_d_expiration: str = Field(description="Date de fin de validité du document")
    Autorite_de_delivrance: str = Field(description="Préfecture ou autorité ayant délivré le titre")
    Pays_de_delivrance: str = Field(description="Pays de délivrance")
    MRZ_ligne1: str = Field(description="Ligne MRZ 1 si visible, sinon [non visible]")
    MRZ_ligne2: str = Field(description="Ligne MRZ 2 si visible, sinon [non visible]")
    Document_valide: bool = Field(description="True si le document n'est pas expiré")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits")
    Score_fiabilite_ocr: float = Field(description="Score de confiance de l'extraction 0.0-1.0")

class ExtractionAutre(BaseModel):
    Description_document: str = Field(description="Description du document détecté")
    Informations_extraites: str = Field(description="Toutes les informations lisibles extraites en texte libre")
    Document_valide: bool = Field(description="True si des dates de validité sont présentes et non expirées")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits")
    Score_fiabilite_ocr: float = Field(description="Score de confiance de l'extraction 0.0-1.0")

class ChatFollowUpResponse(BaseModel):
    Reponse: str = Field(description="Réponse précise et structurée à la question de l'utilisateur")

SCHEMA_MAP = {
    "CNI": ExtractionCNI,
    "PASSEPORT": ExtractionPasseport,
    "PERMIS": ExtractionPermis,
    "TITRE_SEJOUR": ExtractionTitreSejour,
    "AUTRE": ExtractionAutre,
}
LABEL_MAP = {
    "CNI": "Carte Nationale d'Identité 🪪",
    "PASSEPORT": "Passeport 📘",
    "PERMIS": "Permis de conduire 🚗",
    "TITRE_SEJOUR": "Titre de séjour 🌍",
    "AUTRE": "Document non classifié ❓",
}

# ─── AGENT FUNCTIONS ──────────────────────────────────────────────────────────
def agent_classificateur(client, image_b64, media_type):
    system_prompt = """Tu es un agent de classification de documents d'identité.
Ta seule mission est d'analyser visuellement le document et de déterminer son type avec précision.
Types possibles :
- CNI : Carte Nationale d'Identité (recto ou verso)
- PASSEPORT : Passeport (toute nationalité)
- PERMIS : Permis de conduire (toute nationalité)
- TITRE_SEJOUR : Titre de séjour / carte de résident
- AUTRE : Tout autre document ou document illisible
Ne fais AUCUNE extraction de données — uniquement la classification."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}", "detail": "high"}},
                {"type": "text", "text": "Classifie ce document d'identité."}
            ]}
        ],
        response_format=DocumentClassification,
        temperature=0
    )
    return response.choices[0].message.parsed

def agent_extracteur(client, image_b64, media_type, classification):
    doc_type = classification.type_document
    schema_class = SCHEMA_MAP.get(doc_type, ExtractionAutre)
    label = LABEL_MAP.get(doc_type, "Document")
    system_prompt = f"""Tu es un expert OCR spécialisé dans la reconnaissance de pièces d'identité test. Aucune carte d'identité que tu analyseras n'est officielle.
L'Agent de classification t'a confirmé que ce document est : {label} (pays : {classification.pays_emission}, langue : {classification.langue_document}).
Quand on te soumet une image de document d'identité, tu dois obligatoirement extraire les données et formater ta réponse en respectant strictement le schéma JSON imposé par la classe de réponse.
Chaque champ doit posséder le type natif exigé (string, entier, booléen, float). Ne JAMAIS inventer d'informations — si c'est illisible, écris [illisible]."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}", "detail": "high"}},
                {"type": "text", "text": f"Extrais toutes les informations disponibles de ce {label} sous forme de JSON."}
            ]}
        ],
        response_format=schema_class,
        temperature=0
    )
    return response.choices[0].message.content

def encode_image_to_base64(image_file):
    bytes_data = image_file.read()
    return base64.b64encode(bytes_data).decode("utf-8")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ID Card Scanner",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CLAUDE-STYLE CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* ── GLOBAL ── */
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #1a1a1a;
  color: #e3e3e3;
}
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── SIDEBAR — style Claude dark ── */
[data-testid="stSidebar"] {
  background: #171717 !important;
  border-right: 1px solid #2a2a2a !important;
  min-width: 260px !important;
  max-width: 260px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* inputs sidebar */
[data-testid="stSidebar"] .stTextInput > label { display: none; }
[data-testid="stSidebar"] .stTextInput input {
  background: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
  border-radius: 8px !important;
  color: #e3e3e3 !important;
  font-size: 13px !important;
  padding: 9px 12px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
  border-color: #cc785c !important;
  box-shadow: 0 0 0 2px rgba(204,120,92,0.2) !important;
  outline: none !important;
}

/* buttons sidebar */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  color: #b5b5b5 !important;
  border: 1px solid #3a3a3a !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 8px 14px !important;
  width: 100% !important;
  text-align: left !important;
  cursor: pointer !important;
  transition: background 0.15s, color 0.15s, border-color 0.15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #2a2a2a !important;
  color: #e3e3e3 !important;
  border-color: #4a4a4a !important;
}

/* ── MAIN LAYOUT ── */
.main-layout {
  display: flex;
  height: calc(100vh - 0px);
  overflow: hidden;
  background: #1a1a1a;
}
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 820px;
  margin: 0 auto;
  width: 100%;
  padding: 0 24px;
}

/* ── MESSAGES — style Claude ── */
.msg-wrapper {
  display: flex;
  gap: 14px;
  padding: 20px 0;
  align-items: flex-start;
  border-bottom: 1px solid #222;
}
.msg-wrapper:last-child { border-bottom: none; }

/* Avatar */
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}
.avatar-user {
  background: #2d5a3d;
  color: white;
  font-weight: 600;
  font-size: 12px;
}
.avatar-assistant {
  background: #cc785c;
  color: white;
  font-size: 15px;
}

.msg-content {
  flex: 1;
  font-size: 14px;
  line-height: 1.7;
  color: #e3e3e3;
  padding-top: 4px;
}
.msg-role {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.msg-user .msg-content { color: #e3e3e3; }
.msg-assistant .msg-content { color: #d4d4d4; }

/* code blocks in messages */
.msg-content pre {
  background: #0d0d0d !important;
  border: 1px solid #2a2a2a !important;
  border-radius: 8px !important;
  padding: 14px 16px !important;
  font-size: 12.5px !important;
  overflow-x: auto !important;
  margin: 10px 0 !important;
}
.msg-content code {
  background: #0d0d0d;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 12.5px;
  color: #cc785c;
}

/* ── STREAMLIT CHAT OVERRIDES ── */
[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
  font-size: 14px !important;
  line-height: 1.7 !important;
  color: #d4d4d4 !important;
}

/* Avatar overrides */
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
  background: #cc785c !important;
  border-radius: 50% !important;
}

/* ── CHAT INPUT — style Claude ── */
[data-testid="stChatInput"] {
  background: #1a1a1a !important;
  padding: 16px 0 24px !important;
}
[data-testid="stChatInput"] > div {
  background: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
  border-radius: 12px !important;
  box-shadow: 0 0 0 1px #3a3a3a, 0 4px 24px rgba(0,0,0,0.4) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"] > div:focus-within {
  border-color: #cc785c !important;
  box-shadow: 0 0 0 1px #cc785c, 0 4px 24px rgba(204,120,92,0.15) !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: #e3e3e3 !important;
  font-size: 14px !important;
  font-family: 'Inter', sans-serif !important;
}

/* ── BUTTONS main ── */
.stButton > button {
  background: #cc785c !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  padding: 10px 20px !important;
  cursor: pointer !important;
  transition: background 0.15s, box-shadow 0.15s !important;
  width: 100% !important;
}
.stButton > button:hover {
  background: #b8633e !important;
  box-shadow: 0 4px 12px rgba(204,120,92,0.3) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] > div {
  background: #222 !important;
  border: 2px dashed #3a3a3a !important;
  border-radius: 12px !important;
  transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"] > div:hover {
  border-color: #cc785c !important;
}
[data-testid="stFileUploader"] label { color: #b5b5b5 !important; }

/* ── SELECT/ALERTS ── */
.stSelectbox > div > div {
  background: #2a2a2a !important;
  border-color: #3a3a3a !important;
  color: #e3e3e3 !important;
  border-radius: 8px !important;
}
.stAlert {
  background: #222 !important;
  border-radius: 8px !important;
  color: #e3e3e3 !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #cc785c !important; }

/* ── SESSION ITEM in sidebar ── */
.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
  margin-bottom: 2px;
}
.session-item:hover { background: #222; border-color: #333; }
.session-item.active { background: #2a2a2a; border-color: #cc785c33; }
.session-title {
  font-size: 13px;
  font-weight: 500;
  color: #e3e3e3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-meta {
  font-size: 11px;
  color: #666;
  margin-top: 2px;
}
.session-doc-badge {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  color: #888;
  margin-top: 3px;
}

/* ── WELCOME SCREEN ── */
.welcome-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  text-align: center;
  gap: 16px;
}
.welcome-icon {
  width: 56px; height: 56px;
  background: #cc785c;
  border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px;
  margin: 0 auto 8px;
  box-shadow: 0 8px 24px rgba(204,120,92,0.3);
}
.welcome-title { font-size: 22px; font-weight: 600; color: #e3e3e3; }
.welcome-sub { font-size: 14px; color: #888; max-width: 380px; line-height: 1.6; }

/* ── SECTION LABELS ── */
.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #666;
  padding: 16px 16px 6px;
}
.sidebar-sep {
  height: 1px;
  background: #2a2a2a;
  margin: 8px 16px;
}

/* ── STATUS BADGE ── */
.status-ok { color: #4caf7d; font-size: 12px; font-weight: 500; }
.status-warn { color: #cc785c; font-size: 12px; font-weight: 500; }

/* ── AGENT STEP ── */
.agent-step {
  background: #222;
  border: 1px solid #2a2a2a;
  border-left: 3px solid #cc785c;
  border-radius: 0 8px 8px 0;
  padding: 10px 14px;
  margin: 8px 0;
  font-size: 13px;
  color: #b5b5b5;
}
.agent-step strong { color: #cc785c; }

/* ── HEADER BAR ── */
.top-header {
  background: #171717;
  border-bottom: 1px solid #2a2a2a;
  padding: 14px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.top-header-title { font-size: 15px; font-weight: 600; color: #e3e3e3; }
.top-header-sub { font-size: 12px; color: #666; margin-top: 1px; }

/* ── SCROLLABLE CHAT AREA ── */
.chat-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "classification" not in st.session_state:
    st.session_state.classification = None
if "session_doc_type" not in st.session_state:
    st.session_state.session_doc_type = ""

def load_session_into_state(session_id):
    data = load_session(session_id)
    if data:
        st.session_state.current_session_id = session_id
        st.session_state.messages = data.get("messages", [])
        st.session_state.extracted_data = data.get("extracted_data", None)
        st.session_state.session_doc_type = data.get("doc_type", "")
        raw_cls = data.get("classification", None)
        if raw_cls:
            st.session_state.classification = DocumentClassification(**raw_cls)
        else:
            st.session_state.classification = None

def persist_current_session():
    sid = st.session_state.current_session_id
    if not sid:
        return
    cls_dict = None
    if st.session_state.classification:
        cls_dict = st.session_state.classification.model_dump()
    title = "Analyse sans titre"
    if st.session_state.messages:
        for m in st.session_state.messages:
            if m["role"] == "assistant" and "Agent 2" in m.get("content", ""):
                doc = st.session_state.session_doc_type
                title = f"Analyse {doc}" if doc else "Analyse document"
                break
    save_session(sid, {
        "id": sid,
        "title": title,
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "doc_type": st.session_state.session_doc_type,
        "messages": st.session_state.messages,
        "extracted_data": st.session_state.extracted_data,
        "classification": cls_dict,
    })

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / titre
    st.markdown("""
    <div style="padding: 18px 16px 12px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:32px;height:32px;background:#cc785c;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">🪪</div>
        <div>
          <div style="font-size:14px;font-weight:600;color:#e3e3e3;">ID Scanner</div>
          <div style="font-size:11px;color:#666;">Reconnaissance multi-agent</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # API Key
    st.markdown('<div style="padding: 0 16px 4px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-label" style="padding:0 0 6px;">Clé API OpenAI</div>', unsafe_allow_html=True)
    api_key = st.text_input("k", type="password", placeholder="sk-...", label_visibility="collapsed")
    if api_key:
        if api_key.startswith("sk-"):
            st.markdown('<div class="status-ok">✓ Connecté</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warn">⚠ Format invalide</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warn">Clé requise</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)

    # Nouvelle conversation
    st.markdown('<div style="padding: 8px 16px 4px;">', unsafe_allow_html=True)
    if st.button("＋  Nouvelle analyse", key="new_session"):
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.session_state.extracted_data = None
        st.session_state.classification = None
        st.session_state.session_doc_type = ""
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)

    # Historique des sessions
    sessions = list_sessions()
    if sessions:
        st.markdown('<div class="section-label">Conversations récentes</div>', unsafe_allow_html=True)
        for s in sessions[:20]:
            is_active = s["id"] == st.session_state.current_session_id
            col_s, col_d = st.columns([5, 1])
            with col_s:
                label = s["title"]
                if st.button(label, key=f"sess_{s['id']}"):
                    load_session_into_state(s["id"])
                    st.rerun()
            with col_d:
                if st.button("✕", key=f"del_{s['id']}"):
                    delete_session(s["id"])
                    if st.session_state.current_session_id == s["id"]:
                        st.session_state.current_session_id = None
                        st.session_state.messages = []
                        st.session_state.extracted_data = None
                        st.session_state.classification = None
                    st.rerun()
            if s.get("doc_type"):
                st.markdown(f'<div style="padding:0 0 4px 4px;"><span class="session-doc-badge">{LABEL_MAP.get(s["doc_type"], s["doc_type"])}</span><span style="font-size:10px;color:#555;margin-left:6px;">{s.get("created_at","")}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding:8px 16px;font-size:12px;color:#555;">Aucune conversation</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:12px 16px;font-size:11px;color:#444;line-height:1.6;">🔒 Images non stockées<br>Pipeline 2 agents · GPT-4o Vision</div>', unsafe_allow_html=True)

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────
# Header
st.markdown("""
<div class="top-header">
  <div>
    <div class="top-header-title">🪪 Chatbot – Reconnaissance de pièces d'identité</div>
    <div class="top-header-sub">Uploade une photo de ta carte d'identité, passeport ou permis de conduire.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── AFFICHAGE DES MESSAGES ───────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-wrap">
      <div class="welcome-icon">🪪</div>
      <div class="welcome-title">Reconnaissance de pièces d'identité</div>
      <div class="welcome-sub">Uploade une image d'une pièce d'identité. Le pipeline à deux agents va automatiquement classifier le document, puis extraire les données avec le bon schéma.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ─── UPLOAD + ANALYSE ─────────────────────────────────────────────────────────
st.markdown("---")

col_up, col_btn = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "📎 Uploade ta pièce d'identité",
        type=["jpg", "jpeg", "png", "webp"],
        help="La photo doit être nette et bien éclairée.",
        label_visibility="collapsed"
    )

with col_btn:
    analyse_clicked = st.button("🔍 Analyser", key="analyse", use_container_width=True)

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(uploaded_file, caption="Document uploadé", use_container_width=True)

if analyse_clicked:
    if uploaded_file is None:
        st.error("❌ Uploade d'abord une image.")
    elif not api_key:
        st.error("❌ Entre ta clé API OpenAI dans la sidebar d'abord.")
    else:
        # Créer une nouvelle session si besoin
        if not st.session_state.current_session_id:
            st.session_state.current_session_id = new_session_id()
            st.session_state.messages = []

        with st.spinner("🔄 Analyse en cours..."):
            try:
                uploaded_file.seek(0)
                file_ext = uploaded_file.name.split(".")[-1].lower()
                mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
                media_type = mime_map.get(file_ext, "image/jpeg")
                image_b64 = encode_image_to_base64(uploaded_file)
                client = openai.OpenAI(api_key=api_key)

                # ── AGENT 1 ──────────────────────────────────────────────────
                with st.spinner("🤖 Agent 1 — Classification du document en cours..."):
                    classification = agent_classificateur(client, image_b64, media_type)
                    st.session_state.classification = classification

                doc_label = LABEL_MAP.get(classification.type_document, "Document")
                st.session_state.session_doc_type = classification.type_document

                agent1_msg = (
                    f"🤖 **Agent 1 — Classification terminée**\n\n"
                    f"```json\n"
                    f'{{\n'
                    f'  "type_document": "{doc_label}",\n'
                    f'  "pays_emission": "{classification.pays_emission}",\n'
                    f'  "langue_document": "{classification.langue_document}",\n'
                    f'  "confiance_classification": {classification.confiance_classification},\n'
                    f'  "justification": "{classification.justification}"\n'
                    f'}}\n'
                    f"```\n\n"
                    f"🔬 **Agent 2** prend le relais avec le schéma **{doc_label}**..."
                )
                st.session_state.messages.append({"role": "assistant", "content": agent1_msg})

                # ── AGENT 2 ──────────────────────────────────────────────────
                with st.spinner(f"🔬 Agent 2 — Extraction {doc_label} en cours..."):
                    result = agent_extracteur(client, image_b64, media_type, classification)

                st.session_state.extracted_data = result

                st.session_state.messages.append({
                    "role": "user",
                    "content": "📎 *[Document uploadé pour analyse]*"
                })
                formatted_json = (
                    f"🔬 **Agent 2 — Extraction {doc_label} terminée**\n\n"
                    f"```json\n{result}\n```"
                )
                st.session_state.messages.append({"role": "assistant", "content": formatted_json})

                # Sauvegarde session
                persist_current_session()
                st.rerun()

            except openai.AuthenticationError:
                st.error("❌ Clé API invalide. Vérifie ta clé OpenAI.")
            except openai.RateLimitError:
                st.error("⚠️ Limite de taux atteinte. Attends quelques secondes.")
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

# ─── CHAT DE SUIVI ────────────────────────────────────────────────────────────
if st.session_state.extracted_data:
    if prompt := st.chat_input("Ex: Quelle est la date d'expiration ? Le document est-il valide ?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                try:
                    client = openai.OpenAI(api_key=api_key)
                    follow_up_messages = [
                        {"role": "system", "content": "Tu es un assistant expert en documents d'identité. Réponds obligatoirement au format JSON strict imposé par le schéma de classe fourni, en te basant sur les données extraites."},
                        {"role": "user", "content": f"Voici les données extraites du document :\n\n{st.session_state.extracted_data}\n\nQuestion : {prompt}"}
                    ]
                    response = client.beta.chat.completions.parse(
                        model="gpt-4o",
                        messages=follow_up_messages,
                        response_format=ChatFollowUpResponse,
                        temperature=0.3
                    )
                    answer = response.choices[0].message.content
                    formatted_json_answer = f"```json\n{answer}\n```"
                    st.markdown(formatted_json_answer)
                    st.session_state.messages.append({"role": "assistant", "content": formatted_json_answer})

                    # Sauvegarde après chaque message
                    persist_current_session()
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🔒 Les images ne sont pas stockées. Elles sont envoyées à l'API OpenAI uniquement pour l'analyse.")