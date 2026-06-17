import streamlit as st
import openai
import base64
from PIL import Image
import io
from pydantic import BaseModel, Field

# ─── CLASSES DE VALIDATION STRICTE POUR LES RÉPONSES DU CHATBOT ────────────────

# ── AGENT 1 : Classificateur ──────────────────────────────────────────────────
class DocumentClassification(BaseModel):
    type_document: str = Field(description="Type exact du document parmi : CNI, PASSEPORT, PERMIS, TITRE_SEJOUR, AUTRE")
    pays_emission: str = Field(description="Pays d'émission du document détecté")
    langue_document: str = Field(description="Langue principale du document")
    confiance_classification: float = Field(description="Niveau de confiance de la classification entre 0.0 et 1.0")
    justification: str = Field(description="Courte justification du type de document détecté")

# ── AGENT 2 : Schémas spécialisés par type ───────────────────────────────────
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
    Document_valide: bool = Field(description="Indicateur booléen : True si le document n'est pas expiré, False s'il l'est")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits avec succès")
    Score_fiabilite_ocr: float = Field(description="Note flottante de confiance globale de l'extraction de 0.0 à 1.0")

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
    Document_valide: bool = Field(description="Indicateur booléen : True si le document n'est pas expiré, False s'il l'est")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits avec succès")
    Score_fiabilite_ocr: float = Field(description="Note flottante de confiance globale de l'extraction de 0.0 à 1.0")

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
    Document_valide: bool = Field(description="Indicateur booléen : True si le document n'est pas expiré, False s'il l'est")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits avec succès")
    Score_fiabilite_ocr: float = Field(description="Note flottante de confiance globale de l'extraction de 0.0 à 1.0")

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
    Document_valide: bool = Field(description="Indicateur booléen : True si le document n'est pas expiré, False s'il l'est")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits avec succès")
    Score_fiabilite_ocr: float = Field(description="Note flottante de confiance globale de l'extraction de 0.0 à 1.0")

class ExtractionAutre(BaseModel):
    Description_document: str = Field(description="Description du document détecté")
    Informations_extraites: str = Field(description="Toutes les informations lisibles extraites en texte libre")
    Document_valide: bool = Field(description="True si des dates de validité sont présentes et non expirées")
    Nombre_champs_lus: int = Field(description="Nombre total de champs identifiés et extraits avec succès")
    Score_fiabilite_ocr: float = Field(description="Note flottante de confiance globale de l'extraction de 0.0 à 1.0")

class ChatFollowUpResponse(BaseModel):
    Reponse: str = Field(description="Réponse précise et structurée à la question de l'utilisateur")

# Maps
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

# ─── CONFIG PAGE ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ID Card Scanner",
    page_icon="🪪",
    layout="centered"
)

st.title("🪪 Chatbot – Reconnaissance de pièces d'identité")
st.caption("Uploade une photo de ta carte d'identité, passeport ou permis de conduire. Les données sont analysées localement via GPT-4o.")

# ─── SIDEBAR : CLEF API ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password", placeholder="sk-...")
    st.markdown("---")
    st.markdown("**Types de documents supportés :**")
    st.markdown("- 🇫🇷 Carte Nationale d'Identité")
    st.markdown("- 📘 Passeport")
    st.markdown("- 🚗 Permis de conduire")
    st.markdown("- 🌍 Titre de séjour")

# ─── INIT SESSION ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Bonjour ! 👋 Uploade une photo d'une pièce d'identité et je vais en extraire toutes les informations automatiquement."
        }
    ]

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

if "classification" not in st.session_state:
    st.session_state.classification = None

# ─── AFFICHAGE HISTORIQUE ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── UPLOAD IMAGE ──────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📎 Uploade ta pièce d'identité",
    type=["jpg", "jpeg", "png", "webp"],
    help="La photo doit être nette et bien éclairée."
)

def encode_image_to_base64(image_file):
    """Encode l'image en base64 pour l'API OpenAI."""
    bytes_data = image_file.read()
    return base64.b64encode(bytes_data).decode("utf-8")

def agent_classificateur(client: openai.OpenAI, image_b64: str, media_type: str) -> DocumentClassification:
    """
    AGENT 1 — Analyse l'image et classifie le type de document.
    Ne fait aucune extraction de données, uniquement la classification.
    """
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
                {"type": "image_url", "image_url": {
                    "url": f"data:{media_type};base64,{image_b64}",
                    "detail": "high"
                }},
                {"type": "text", "text": "Classifie ce document d'identité."}
            ]}
        ],
        response_format=DocumentClassification,
        temperature=0
    )
    return response.choices[0].message.parsed

def agent_extracteur(client: openai.OpenAI, image_b64: str, media_type: str, classification: DocumentClassification):
    """
    AGENT 2 — Reçoit la classification de l'Agent 1 et extrait les données
    avec le schéma Pydantic correspondant au type de document détecté.
    """
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
                {"type": "image_url", "image_url": {
                    "url": f"data:{media_type};base64,{image_b64}",
                    "detail": "high"
                }},
                {"type": "text", "text": f"Extrais toutes les informations disponibles de ce {label} sous forme de JSON."}
            ]}
        ],
        response_format=schema_class,
        temperature=0
    )
    return response.choices[0].message.content

# ─── LOGIQUE PRINCIPALE ────────────────────────────────────────────────────────
if uploaded_file is not None:
    # Affiche un aperçu de l'image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(uploaded_file, caption="Document uploadé", use_container_width=True)

    # Bouton d'analyse
    if st.button("🔍 Analyser le document", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ Entre ta clé API OpenAI dans la sidebar d'abord.")
        else:
            with st.spinner("🔄 Analyse en cours..."):
                try:
                    # Reset le curseur du fichier
                    uploaded_file.seek(0)

                    # Détermine le type MIME
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
                    media_type = mime_map.get(file_ext, "image/jpeg")

                    # Encode en base64
                    image_b64 = encode_image_to_base64(uploaded_file)

                    client = openai.OpenAI(api_key=api_key)

                    # ── AGENT 1 : Classification ──────────────────────────────
                    with st.spinner("🤖 Agent 1 — Classification du document en cours..."):
                        classification = agent_classificateur(client, image_b64, media_type)
                        st.session_state.classification = classification

                    doc_label = LABEL_MAP.get(classification.type_document, "Document")
                    confiance = f"{classification.confiance_classification:.0%}"

                    # Affiche le résultat de l'Agent 1 dans le chat
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
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": agent1_msg
                    })

                    # ── AGENT 2 : Extraction spécialisée ─────────────────────
                    with st.spinner(f"🔬 Agent 2 — Extraction {doc_label} en cours..."):
                        result = agent_extracteur(client, image_b64, media_type, classification)

                    # Stocke le résultat
                    st.session_state.extracted_data = result

                    # Ajoute au chat
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "📎 *[Document uploadé pour analyse]*"
                    })

                    formatted_json = (
                        f"🔬 **Agent 2 — Extraction {doc_label} terminée**\n\n"
                        f"```json\n{result}\n```"
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": formatted_json
                    })

                    st.rerun()

                except openai.AuthenticationError:
                    st.error("❌ Clé API invalide. Vérifie ta clé OpenAI.")
                except openai.RateLimitError:
                    st.error("⚠️ Limite de taux atteinte. Attends quelques secondes.")
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

# ─── CHAT DE SUIVI ─────────────────────────────────────────────────────────────
if st.session_state.extracted_data:
    st.markdown("---")
    st.markdown("💬 **Tu peux maintenant poser des questions sur le document analysé :**")

    if prompt := st.chat_input("Ex: Quelle est la date d'expiration ? Le document est-il valide ?"):
        # Message user
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Réponse assistant
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
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

# ─── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🔒 Les images ne sont pas stockées. Elles sont envoyées à l'API OpenAI uniquement pour l'analyse.")