from perplexity import Perplexity
from dotenv import load_dotenv
import os

load_dotenv()

def p_chat(message:str, chat_role_content:str = "", max_mot: int = 0):
    try:
        client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))
        
        if max_mot > 0:
            chat_role_content += f"\n\nINSTRUCTION STRICTE : Réponds en EXACTEMENT {max_mot} mots maximum. Compte précisément. Ne dépasse pas."
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content":chat_role_content},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(str(e))