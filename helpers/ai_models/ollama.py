# helpers/ai_models/mistral.py
import os
from datetime import datetime
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"

import ollama
import asyncio


MODEL_DEFAULT = "mistral" # qwen2.5:7b-instruct-q5_K_M, mistral:badest
PROMPT_LANG = {"en":"Response only in english : ", "fr": f"Nous somme aujourd'hui le {datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S')}\nRéponds uniquement en francais : "}#, "mg": "Valio amin'ny teny gasy ny fanontaniana : "}


def generer_texte(texte_entree, modele=MODEL_DEFAULT, max_tokens=1000, temperature=0.7, lang="fr"):
    MODEL_IDS = {"mistral-7b-instruct":"mistral", "qwen2.5-7b-instruct-q5":"qwen2.5:7b-instruct-q5_K_M", "mistral-badest":"mistral:badest", "mistral-phishing":"mistral:phishing"}
    if modele in MODEL_IDS.keys():
        modele = MODEL_IDS[modele]
    else:
        modele = MODEL_DEFAULT
    try:
        if lang not in ["fr", "en"]: raise Exception("Language non accepté.")
        
        prompt_francais = f"{PROMPT_LANG[lang]}{texte_entree}"
        reponse = ollama.generate(
            model=modele,
            prompt=prompt_francais,
            options={
                # "num_predict": max_tokens,
                "temperature": temperature
            }
        )
        return reponse['response'].strip()
    except Exception as e:
        return f"Erreur lors de la génération : {str(e)}"


async def generer_texte_stream_websocket(texte_entree, modele=MODEL_DEFAULT, send_callback=None, lang="fr"):
    prompt_francais = f"{PROMPT_LANG[lang]}{texte_entree}"
    flux = ollama.generate(model=modele, prompt=prompt_francais, stream=True)
    
    texte_accumule = ""
    ponctuations = ".!?,;:"
    
    for morceau in flux:
        contenu = morceau['response']
        texte_accumule += contenu
        
        if contenu and contenu[-1] in ponctuations:
            if send_callback:
                await send_callback(texte_accumule)
            texte_accumule = ""
        
        await asyncio.sleep(0.01)
    if texte_accumule and send_callback:
        await send_callback(texte_accumule)
    return texte_accumule
