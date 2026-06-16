import streamlit as st
import openai
import base64
from PIL import Image
import io

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

def analyze_id_card(api_key: str, image_b64: str, media_type: str, user_question: str = None):
    """Envoie l'image à GPT-4o Vision et retourne l'extraction structurée."""
    client = openai.OpenAI(api_key=api_key)

    system_prompt = """Tu es un expert OCR spécialisé dans la reconnaissance de pièces d'identité officielles.
Quand on te soumet une image de document d'identité, tu dois :
1. Identifier le TYPE de document (CNI française, passeport, permis de conduire, titre de séjour, etc.)
2. Extraire TOUTES les informations visibles de manière structurée en Markdown
3. Signaler si des champs sont illisibles ou absents
4. Ne JAMAIS inventer d'informations — si c'est illisible, écris [illisible]
5. Respecter la vie privée : rappelle à l'utilisateur de ne partager des documents que dans un contexte de confiance

Format de réponse :
## 📄 Type de document : [type]

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
| [autres champs pertinents] | ... |

### 🔍 Observations
[Qualité de l'image, champs manquants, remarques]

### ⚠️ Rappel vie privée
Ce document contient des données sensibles. Assurez-vous de l'utiliser dans un cadre sécurisé."""

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{image_b64}",
                        "detail": "high"
                    }
                },
                {
                    "type": "text",
                    "text": user_question if user_question else "Analyse cette pièce d'identité et extrais toutes les informations disponibles."
                }
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        max_tokens=1500,
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

                    # Appel API
                    result = analyze_id_card(api_key, image_b64, media_type)

                    # Stocke le résultat
                    st.session_state.extracted_data = result

                    # Ajoute au chat
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "📎 *[Document uploadé pour analyse]*"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result
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
                        {"role": "system", "content": "Tu es un assistant expert en documents d'identité. Réponds aux questions en te basant sur les données extraites fournies."},
                        {"role": "user", "content": f"Voici les données extraites du document :\n\n{st.session_state.extracted_data}\n\nQuestion : {prompt}"}
                    ]
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=follow_up_messages,
                        max_tokens=500,
                        temperature=0.3
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

# ─── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🔒 Les images ne sont pas stockées. Elles sont envoyées à l'API OpenAI uniquement pour l'analyse.")