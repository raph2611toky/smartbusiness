# apps/chatbot/helpers/ai_models/gemini.py
from django.core.management.base import BaseCommand
from openai import OpenAI
from dotenv import load_dotenv
import os
import traceback
from apps.chatbot.models import MessageChat
from helpers.ai_models.ollama import generer_texte
from apps.users.models import User
from helpers.ai_models.perplexity import p_chat

from datetime import datetime

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

CHAT_CONTENT = {
    "FR": (
        f"Nous somme aujourd'hui le {datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S')}"
    )
}

def prepare_messages(conversation_id: int, user_message: str, lang: str, user: User) -> list:
    system_content = CHAT_CONTENT["FR"]

    total_people = 0
    restrictions = ""
    
    system_msg = {
        "role": "system",
        "content": f"{system_content}\n\nInformations utilisateur: \n\t- Nom: {user.nom_complet}\n\t-Sexe: {user.sexe}"
    }

    msgs = MessageChat.objects.filter(conversation__id_conversation=conversation_id).order_by('-created_at')[:20]
    history = []
    for m in reversed(msgs):
        role = "user" if m.from_user else "assistant"
        history.append({"role": role, "content": m.contenu})

    user_msg = {"role": "user", "content": user_message}

    return [system_msg] + [user_msg]


def simple_chat(message: str, lang='FR') -> str:
    if not message:
        return "Message requis"
    # if lang.upper() == 'MG':
    #     message = traduire_texte(message, source_lang='mg', cible_lang='fr')
    try:
        chat_content = CHAT_CONTENT["FR"]
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": chat_content},
                {"role": "user", "content": message}
            ]
        )
        reponse_chat = response.choices[0].message.content
        # if lang.upper() == 'MG':
        #     reponse_chat = traduire_texte(reponse_chat, source_lang='fr', cible_lang='mg')
        print("✔✅ Génération réussie.")
        return reponse_chat
    except Exception as e:
        try:
            reponse_chat = generer_texte(message, modele="qwen2.5:7b-instruct-q5_K_M")
            print(("✅ Géneration réussie."))
            return reponse_chat
        except Exception as e:
            print(traceback.format_exc())
            raise Exception(f"Erreur lors de la communication avec l’IA : {str(e)}")

async def websocket_chat(message: str, lang='FR') -> str:
    if not message:
        raise Exception("Message requis pour le chat")
    # if lang.upper() == 'MG':
    #     message = traduire_texte(message, source_lang='mg', cible_lang='fr')
    try:
        chat_content = CHAT_CONTENT["FR"]
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": chat_content},
                {"role": "user", "content": message}
            ]
        )
        reponse_chat = response.choices[0].message.content
        # if lang.upper() == 'MG':
        #     reponse_chat = traduire_texte(reponse_chat, source_lang='fr', cible_lang='mg')
        return reponse_chat
    except Exception as e:
        raise Exception(f"Erreur lors de la communication avec l'IA: {str(e)}")

def conversation_chat(conversation_id: int, message: str, lang='FR', user: User = None) -> str:
    if not message:
        return "Message requis"
    if not user:
        raise ValueError("Utilisateur requis pour le contexte personnalisé")
    # if lang.upper() == 'MG':
    #     message = traduire_texte(message, source_lang='mg', cible_lang='fr')
    try:
        messages = prepare_messages(conversation_id, message, lang, user)
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=messages
        )
        reponse_chat = response.choices[0].message.content
        # if lang.upper() == 'MG':
        #     reponse_chat = traduire_texte(reponse_chat, source_lang='fr', cible_lang='mg')
        return reponse_chat
    except Exception as e:
        try:
            reponse_chat = generer_texte(messages, modele="qwen2.5:7b-instruct-q5_K_M")
            print(("✅ Géneration réussie."))
            return reponse_chat
        except Exception as e:
            print(traceback.format_exc())
            raise Exception(f"Erreur lors de la communication avec l’IA : {str(e)}")