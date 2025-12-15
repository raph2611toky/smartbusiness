# from googletrans import Translator

# def traduire_texte(texte, source_lang='fr', cible_lang='mg'):
#     try:
#         traducteur = Translator()
#         resultat = traducteur.translate(texte, src=source_lang, dest=cible_lang)
#         print("✅ Traduction réussie")
#         return resultat.text
#     except Exception as e:
#         return f"Erreur lors de la traduction : {e}"

# print(traduire_texte("miarahaba tompoko, tsy mandeha intsony ny fadimbolanako", source_lang='mg', cible_lang='fr'))

from deep_translator import GoogleTranslator

def traduire_texte(texte, source_lang="fr", cible_lang="mg"):
    try:
        return GoogleTranslator(source=source_lang, target=cible_lang).translate(texte)
    except Exception as e:
        return f"Erreur lors de la traduction: {e}"

