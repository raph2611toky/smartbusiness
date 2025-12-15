TEMPLATES_EMAIL = {
    "verify_email":"emails/otp_verification.html",
    "reinitialiser_mot_de_passe":"emails/reset_password.html",
    'support_message': 'emails/support_message.html',
}

RISK_MAPPING = {
    "violence": {
        "label": "Violence",
        "image_name": "/risks/violence.png",
        "indication": "Contenu montrant ou incitant à la violence physique"
    },
    "pornographie": {
        "label": "Pornographie / NSFW",
        "image_name": "/risks/nsfw.png",
        "indication": "Contenu sexuel explicite ou suggestif (images, textes, liens)"
    },
    "illegal": {
        "label": "Contenu illégal",
        "image_name": "/risks/illegal.png",
        "indication": "Promotion ou description d'activités illégales (drogue, armes, etc.)"
    },
    "harcelement": {
        "label": "Harcèlement",
        "image_name": "/risks/harassment.png",
        "indication": "Attaques personnelles répétées, menaces ou intimidation"
    },
    "automutilation": {
        "label": "Automutilation",
        "image_name": "/risks/self_harm.png",
        "indication": "Encouragement ou description d'actes d'automutilation ou de suicide"
    },
    "discours_haine": {
        "label": "Discours de haine",
        "image_name": "/risks/hate_speech.png",
        "indication": "Attaques basées sur la race, religion, genre, orientation sexuelle, etc."
    },
    "jailbreak": {
        "label": "Tentatives de jailbreak",
        "image_name": "/risks/jailbreak.png",
        "indication": "Tentatives de contourner les garde-fous ou d'obtenir des réponses interdites"
    },
    "arnaque": {
        "label": "Arnaques / Fraude",
        "image_name": "/risks/scam.png",
        "indication": "Tentatives d'escroquerie, phishing, faux concours, etc."
    },
    "hallucination": {
        "label": "Hallucinations probables",
        "image_name": "/risks/hallucination.png",
        "indication": "Informations manifestement fausses ou inventées par l'IA"
    },
    "fake_news": {
        "label": "Informations douteuses / Fake news",
        "image_name": "/risks/fake_news.png",
        "indication": "Contenu trompeur présenté comme factuel"
    },
    "vulgarite": {
        "label": "Langage vulgaire",
        "image_name": "/risks/vulgar.png",
        "indication": "Utilisation excessive d'insultes ou de grossièretés"
    },
    "controverse": {
        "label": "Sujets controversés",
        "image_name": "/risks/controversy.png",
        "indication": "Sujets politiques, religieux ou sociaux très clivants"
    },
    "desinformation": {
        "label": "Désinformation légère",
        "image_name": "/risks/misinformation.png",
        "indication": "Informations inexactes mais non malveillantes"
    },
    "publicite": {
        "label": "Contenu publicitaire",
        "image_name": "/risks/advertising.png",
        "indication": "Promotion déguisée de produits ou services"
    },
    "basse_qualite": {
        "label": "Réponse de faible qualité",
        "image_name": "/risks/low_quality.png",
        "indication": "Réponse hors-sujet, trop courte ou sans valeur ajoutée"
    },
    "autre": {
        "label": "Autre",
        "image_name": "/risks/other.png",
        "indication": "Problème ne rentrant dans aucune catégorie précédente"
    },
}