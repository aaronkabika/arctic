"""
Fonctions utilitaires pour l'application Arctic
"""
import unicodedata
import re
from werkzeug.utils import secure_filename
from config import Config


# ==============================
# NORMALISATION DE TEXTE
# ==============================

def normaliser_texte(texte):
    """Normalise un texte en enlevant les accents et en le mettant en minuscules."""
    if texte is None:
        return ""
    
    texte = unicodedata.normalize("NFD", str(texte))
    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )
    return texte.casefold()


# ==============================
# VALIDATION D'EMAIL
# ==============================

def verifier_email(email):
    """
    Valide une adresse email selon les règles RFC 5322.
    Retourne None si valide, un message d'erreur sinon.
    """
    if not email or not email.strip():
        return "Vous devez donner l'email."
    
    email = email.strip()
    
    if any(caractere.isspace() for caractere in email):
        return "Votre email ne doit pas contenir d'espaces."
    
    if email.count("@") != 1:
        return "Votre email est incorrect."
    
    partie_locale, domaine = email.split("@")
    
    if not partie_locale or not domaine:
        return "Votre email est incorrect."
    
    # Validation de la partie locale
    if (partie_locale.startswith(".") or partie_locale.endswith(".") or ".." in partie_locale):
        return "Votre email est incorrect."
    
    caracteres_locaux_autorises = set(
        "abcdefghijklmnopqrstuvwxyz0123456789.!#$%&'*+/=?^_`{|}~-"
    )
    if any(caractere.lower() not in caracteres_locaux_autorises for caractere in partie_locale):
        return "Votre email est incorrect."
    
    # Validation du domaine
    if "." not in domaine or domaine.startswith(".") or domaine.endswith("."):
        return "Votre email est incorrect."
    
    etiquettes_domaine = domaine.split(".")
    if any(not etiquette for etiquette in etiquettes_domaine):
        return "Votre email est incorrect."
    
    for etiquette in etiquettes_domaine:
        if (etiquette.startswith("-") or etiquette.endswith("-") or
                not all(c.isalnum() or c == "-" for c in etiquette)):
            return "Votre email est incorrect."
    
    extension = etiquettes_domaine[-1]
    if len(extension) < 2 or not extension.isalpha():
        return "Votre email est incorrect."
    
    return None


# ==============================
# VALIDATION DE TÉLÉPHONE
# ==============================

def verifier_telephone(telephone):
    """
    Valide un numéro de téléphone (9 chiffres).
    Retourne None si valide, un message d'erreur sinon.
    """
    if not telephone or not telephone.strip():
        return "Vous devez fournir un numéro de téléphone."
    
    telephone = telephone.strip()
    
    if not telephone.isdigit():
        return "Votre numéro est incorrect."
    
    if len(telephone) != Config.PHONE_LENGTH:
        return f"Votre numéro doit contenir {Config.PHONE_LENGTH} chiffres."
    
    return None


# ==============================
# VALIDATION DE MOT DE PASSE
# ==============================

def verifier_mot_de_passe(password):
    """
    Valide un mot de passe selon les règles de sécurité.
    Retourne None si valide, un message d'erreur sinon.
    """
    if not password:
        return "Vous devez fournir un mot de passe."
    
    if len(password) < Config.MIN_PASSWORD_LENGTH or len(password) > Config.MAX_PASSWORD_LENGTH:
        return f"Le mot de passe doit contenir entre {Config.MIN_PASSWORD_LENGTH} et {Config.MAX_PASSWORD_LENGTH} caractères."
    
    if not any(caractere.isdigit() for caractere in password):
        return "Votre mot de passe doit contenir au moins un chiffre."
    
    if not any(caractere.isupper() for caractere in password):
        return "Votre mot de passe doit contenir au moins un caractère majuscule."
    
    if not any(caractere in "!@#$%^&*" for caractere in password):
        return "Votre mot de passe doit contenir au moins un caractère spécial (!@#$%^&*)."
    
    return None


# ==============================
# VALIDATION D'ÂGE
# ==============================

def calculer_age(date_naissance):
    """Calcule l'âge à partir d'une date de naissance."""
    from datetime import date
    aujourd_hui = date.today()
    age = aujourd_hui.year - date_naissance.year
    if (aujourd_hui.month, aujourd_hui.day) < (date_naissance.month, date_naissance.day):
        age -= 1
    return age


def verifier_age_minimum(date_naissance, age_minimum=None):
    """
    Vérifie si l'utilisateur a l'âge minimum requis.
    Retourne True si valide, False sinon.
    """
    if age_minimum is None:
        age_minimum = Config.MIN_AGE
    
    age = calculer_age(date_naissance)
    return age >= age_minimum


# ==============================
# VALIDATION DE FICHIERS
# ==============================

def verifier_extension(fichier, extensions_autorisees):
    """
    Vérifie la présence d'un fichier et son extension autorisée.
    Retourne True si valide, False sinon.
    """
    if fichier is None or not fichier.filename:
        return False
    
    nom_securise = secure_filename(fichier.filename)
    if not nom_securise or "." not in nom_securise:
        return False
    
    extension = nom_securise.rsplit(".", 1)[1].lower()
    return extension in extensions_autorisees


def verifier_taille_fichier(fichier, taille_max_mo):
    """
    Vérifie que le fichier n'est ni vide ni trop volumineux.
    Retourne True si valide, False sinon.
    """
    if fichier is None or not fichier.filename:
        return False
    
    try:
        position_initiale = fichier.stream.tell()
        fichier.stream.seek(0, 2)  # SEEK_END
        taille_octets = fichier.stream.tell()
        fichier.stream.seek(position_initiale)
    except (AttributeError, OSError):
        return False
    
    taille_max_octets = taille_max_mo * 1024 * 1024
    return 0 < taille_octets <= taille_max_octets


def obtenir_extension_fichier(nom_fichier):
    """Obtient l'extension d'un fichier."""
    nom_securise = secure_filename(nom_fichier)
    if "." in nom_securise:
        return nom_securise.rsplit(".", 1)[1].lower()
    return ""


# ==============================
# FORMATAGE DE DONNÉES
# ==============================

def formater_prix(prix):
    """Formate un prix pour l'affichage."""
    return f"{prix:,.2f} $"


def formater_date(date_str):
    """Formate une date ISO pour l'affichage."""
    from datetime import datetime
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return date_str


def formater_taille_fichier(taille_octets):
    """Formate une taille de fichier en octets vers une unité lisible."""
    for unite in ['o', 'Ko', 'Mo', 'Go']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.1f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.1f} To"


# ==============================
# SANITIZATION
# ==============================

def sanitize_input(texte, max_length=None):
    """Nettoie une entrée utilisateur."""
    if not texte:
        return ""
    
    texte = texte.strip()
    
    if max_length and len(texte) > max_length:
        texte = texte[:max_length]
    
    return texte


def sanitize_html(texte):
    """Échappe les caractères HTML dangereux."""
    if not texte:
        return ""
    
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    return "".join(html_escape_table.get(c, c) for c in texte)
