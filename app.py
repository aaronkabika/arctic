from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    send_from_directory,
    flash,
    jsonify,
    abort
)

from datetime import datetime, date, timedelta
import re
import sqlite3
import os
import uuid
import math
import unicodedata
import logging
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# ==============================
# CONFIGURATION DE L'APPLICATION
# ==============================

app = Flask(__name__)

# Configuration de la clé secrète
app.secret_key = os.environ.get("ARCTIC_SECRET_KEY")
if not app.secret_key:
    # En développement, utiliser une clé par défaut (À CHANGER EN PRODUCTION)
    app.secret_key = "dev_secret_key_change_in_production"
    app.logger.warning("Utilisation d'une clé secrète par défaut. Définir ARCTIC_SECRET_KEY en production.")

# Configuration de la base de données
app.config["DATABASE"] = os.path.join(app.root_path, "arctic.db")

# Configuration des fichiers uploadés
# Sur Vercel, utiliser /tmp car le système de fichiers est en lecture seule
if os.environ.get("VERCEL"):
    app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
else:
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 Mo max

# Configuration de la session
app.config["SESSION_COOKIE_SECURE"] = False  # True en production avec HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Configuration de la pagination
app.config["ITEMS_PER_PAGE"] = 12

# Créer le dossier uploads s'il n'existe pas
try:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
except OSError:
    # Sur Vercel, ignorer l'erreur si le dossier ne peut pas être créé
    pass

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ==============================
# DÉCORATEURS DE SÉCURITÉ
# ==============================

def login_required(f):
    """Décorateur pour protéger les routes nécessitant une connexion."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "utilisateur_id" not in session:
            flash("Vous devez être connecté pour accéder à cette page.", "warning")
            return redirect(url_for("connexion", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Décorateur pour vérifier le rôle de l'utilisateur."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "utilisateur_id" not in session:
                flash("Vous devez être connecté pour accéder à cette page.", "warning")
                return redirect(url_for("connexion"))
            
            user_role = session.get("role")
            if user_role not in roles:
                flash("Vous n'avez pas les droits nécessaires pour accéder à cette page.", "error")
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==============================
# FONCTIONS UTILITAIRES
# ==============================

def normaliser_texte(texte):
    if texte is None:
        return ""

    texte = unicodedata.normalize("NFD", str(texte))

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    return texte.casefold()

def ouvrir_base():
    """Ouvre la base Arctic et active les clés étrangères pour cette connexion."""
    try:
        connexion = sqlite3.connect(app.config["DATABASE"])
        connexion.create_function("SANS_ACCENTS", 1, normaliser_texte)
        connexion.execute("PRAGMA foreign_keys = ON")
        # Optimisation pour de meilleures performances
        connexion.execute("PRAGMA journal_mode=WAL")
        return connexion
    except sqlite3.Error as e:
        app.logger.error(f"Erreur lors de l'ouverture de la base de données : {e}")
        raise


def get_db_cursor():
    """Gestionnaire de contexte pour la base de données."""
    conn = ouvrir_base()
    try:
        cursor = conn.cursor()
        yield cursor, conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Erreur de base de données : {e}")
        raise
    finally:
        conn.close()


@app.errorhandler(413)
def fichier_trop_volumineux(_erreur):
    """Gestion de l'erreur fichier trop volumineux."""
    flash("Les fichiers envoyés dépassent la taille maximale de 25 Mo.", "error")
    return redirect(request.referrer or url_for("accueil")), 413


@app.errorhandler(404)
def page_non_trouvee(e):
    """Gestion de l'erreur 404."""
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def acces_interdit(e):
    """Gestion de l'erreur 403."""
    return render_template("errors/403.html"), 403


@app.errorhandler(500)
def erreur_serveur(e):
    """Gestion de l'erreur 500."""
    app.logger.error(f"Erreur serveur : {e}")
    return render_template("errors/500.html"), 500


# ==============================
# CREATION DE LA BASE
# ==============================

def creer_base():
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateur (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                date_naissance TEXT NOT NULL,
                sexe TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telephone TEXT NOT NULL,
                mot_de_passe TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS oeuvre (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artiste_id INTEGER NOT NULL,
                titre TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                date_creation TEXT NOT NULL,
                prix REAL NOT NULL,
                FOREIGN KEY (artiste_id) REFERENCES utilisateur(id)
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS fichier_oeuvre (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oeuvre_id INTEGER NOT NULL,
                chemin_fichier TEXT NOT NULL,
                type_fichier TEXT NOT NULL,
                FOREIGN KEY (oeuvre_id)
                    REFERENCES oeuvre(id)
                    ON DELETE CASCADE
            )
        """)

        connexion.commit()
    finally:
        connexion.close()


# ==============================
# VALIDATION DE L'EMAIL
# ==============================

def verifier_email(email):

    if not email.strip():
        return "Vous devez donner l'email."

    if any(caractere.isspace() for caractere in email):
        return "Votre email ne doit pas contenir d'espaces."

    if email.count("@") != 1:
        return "Votre email est incorrect."

    partie_locale, domaine = email.split("@")

    if not partie_locale or not domaine:
        return "Votre email est incorrect."

    # Refuser les points placés au début/à la fin ou répétés dans la partie locale.
    if (partie_locale.startswith(".") or partie_locale.endswith(".")
            or ".." in partie_locale):
        return "Votre email est incorrect."

    caracteres_locaux_autorises = set(
        "abcdefghijklmnopqrstuvwxyz0123456789.!#$%&'*+/=?^_`{|}~-"
    )
    if any(caractere.lower() not in caracteres_locaux_autorises
           for caractere in partie_locale):
        return "Votre email est incorrect."

    if "." not in domaine or domaine.startswith(".") or domaine.endswith("."):
        return "Votre email est incorrect."

    etiquettes_domaine = domaine.split(".")
    if any(not etiquette for etiquette in etiquettes_domaine):
        return "Votre email est incorrect."

    # Chaque partie du domaine doit contenir des lettres, chiffres ou tirets,
    # sans tiret au début ou à la fin.
    for etiquette in etiquettes_domaine:
        if (etiquette.startswith("-") or etiquette.endswith("-")
                or not all(c.isalnum() or c == "-" for c in etiquette)):
            return "Votre email est incorrect."

    extension = etiquettes_domaine[-1]
    if len(extension) < 2 or not extension.isalpha():
        return "Votre email est incorrect."

    return None


# ==============================
# VALIDATION DU TELEPHONE
# ==============================

def verifier_telephone(telephone):

    if not telephone.isdigit():
        return "Votre numéro est incorrect."

    if len(telephone) != 9:
        return "Votre numéro doit contenir 9 chiffres."

    return None


# ==============================
# VALIDATION DU MOT DE PASSE
# ==============================

def verifier_mot_de_passe(password):

    if len(password) < 8 or len(password) > 20:
        return "Le mot de passe doit contenir entre 8 et 20 caractères."

    contient_chiffre = False

    for caractere in password:
        if caractere.isdigit():
            contient_chiffre = True

    if not contient_chiffre:
        return "Votre mot de passe doit contenir au moins un chiffre."

    contient_maj = False

    for caractere in password:
        if caractere.isupper():
            contient_maj = True

    if not contient_maj:
        return "Votre mot de passe doit contenir au moins un caractère majuscule."

    caracteres_speciaux = "!@#$%^&*"
    contient_special = False

    for caractere in password:
        if caractere in caracteres_speciaux:
            contient_special = True

    if not contient_special:
        return "Votre mot de passe doit contenir au moins un caractère spécial."

    return None


# ==============================
# VERIFICATION DE L'EXTENSION
# ==============================

def verifier_extension(fichier, extensions_autorisees):
    """Vérifie la présence d'un fichier et son extension autorisée."""
    if fichier is None or not fichier.filename:
        return False

    nom_securise = secure_filename(fichier.filename)
    if not nom_securise or "." not in nom_securise:
        return False

    extension = nom_securise.rsplit(".", 1)[1].lower()
    return extension in extensions_autorisees


# ==============================
# VERIFICATION DE LA TAILLE
# ==============================

def verifier_taille_fichier(fichier, taille_max_mo):
    """Vérifie que le fichier n'est ni vide ni trop volumineux."""

    if fichier is None or not fichier.filename:
        return False

    try:
        position_initiale = fichier.stream.tell()

        fichier.stream.seek(0, os.SEEK_END)
        taille_octets = fichier.stream.tell()

        fichier.stream.seek(position_initiale)

    except (AttributeError, OSError):
        return False

    taille_max_octets = taille_max_mo * 1024 * 1024

    return 0 < taille_octets <= taille_max_octets


# ==============================
# PAGE D'ACCUEIL
# ==============================

@app.route("/")
def accueil():
    return render_template("index.html")


# ==============================
# PAGE CONNEXION
# ==============================

@app.route("/connexion", methods=["GET", "POST"])
def connexion():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return "Veuillez saisir votre adresse e-mail et votre mot de passe."

        connexion = ouvrir_base()
        try:
            curseur = connexion.cursor()
            curseur.execute("""
                SELECT id, nom, mot_de_passe, role
                FROM utilisateur
                WHERE lower(email) = ?
            """, (email,))
            utilisateur = curseur.fetchone()
        except sqlite3.Error:
            app.logger.exception("Erreur pendant la recherche du compte.")
            return "Impossible de vérifier le compte pour le moment.", 500
        finally:
            connexion.close()

        if utilisateur is None:
            return "Adresse e-mail ou mot de passe incorrect."

        if not check_password_hash(utilisateur[2], password):
            return "Adresse e-mail ou mot de passe incorrect."

        # Nettoyer une éventuelle ancienne session avant d'ouvrir la nouvelle.
        session.clear()
        session["utilisateur_id"] = utilisateur[0]
        session["nom"] = utilisateur[1]
        session["role"] = utilisateur[3]

        return redirect(url_for("espace"))

    return render_template("connexion.html")


# ==============================
# PAGE INSCRIPTION
# ==============================

@app.route("/inscription")
def inscription():
    return render_template("inscription.html")


# ==============================
# INSCRIPTION ARTISTE
# ==============================

@app.route("/inscription/artiste", methods=["GET", "POST"])
def inscription_artiste():

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        date_naissance = request.form.get("date_naissance", "")
        sexe = request.form.get("sexe", "").strip()
        email = request.form.get("email", "").strip().lower()
        telephone = request.form.get("telephone", "").strip()
        password = request.form.get("password", "")
        confirmation_password = request.form.get("confirmation_password", "")

        # ==============================
        # NOM
        # ==============================

        if not nom:
            return "Vous devez compléter le nom."

        if not sexe:
            return "Vous devez sélectionner votre sexe."

        # ==============================
        # EMAIL
        # ==============================

        erreur_email = verifier_email(email)

        if erreur_email:
            return erreur_email

        # ==============================
        # TELEPHONE
        # ==============================

        erreur_telephone = verifier_telephone(telephone)

        if erreur_telephone:
            return erreur_telephone

        # ==============================
        # DATE DE NAISSANCE
        # ==============================

        try:

            date_naissance = datetime.strptime(
                date_naissance,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return "La date de naissance est incorrecte."

        if date_naissance > date.today():
            return "La date de naissance ne peut pas être dans le futur."

        # ==============================
        # CALCUL DE L'AGE
        # ==============================

        aujourd_hui = date.today()

        age = aujourd_hui.year - date_naissance.year

        if (aujourd_hui.month, aujourd_hui.day) < (
            date_naissance.month,
            date_naissance.day
        ):
            age -= 1

        # ==============================
        # AGE MINIMUM
        # ==============================

        if age < 18:
            return "Vous devez avoir au moins 18 ans pour vous inscrire comme artiste."

        # ==============================
        # MOT DE PASSE
        # ==============================

        erreur_password = verifier_mot_de_passe(password)

        if erreur_password:
            return erreur_password

        # ==============================
        # CONFIRMATION DU MOT DE PASSE
        # ==============================

        if confirmation_password != password:
            return "Veuillez réécrire votre mot de passe."

        # ==============================
        # HACHAGE DU MOT DE PASSE
        # ==============================

        mot_de_passe_hache = generate_password_hash(password)

        # ==============================
        # CONNEXION A SQLITE
        # ==============================

        connexion = ouvrir_base()
        try:
            curseur = connexion.cursor()
            curseur.execute("""
                INSERT INTO utilisateur
                (nom, date_naissance, sexe, email, telephone, mot_de_passe, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nom,
                date_naissance.isoformat(),
                sexe,
                email,
                "+243" + telephone,
                mot_de_passe_hache,
                "artiste"
            ))
            nouvel_utilisateur_id = curseur.lastrowid
            connexion.commit()
        except sqlite3.IntegrityError:
            connexion.rollback()
            return "Cette adresse e-mail est déjà utilisée."
        except sqlite3.Error:
            connexion.rollback()
            app.logger.exception("Erreur pendant la création du compte.")
            return "Impossible de créer le compte pour le moment.", 500
        finally:
            connexion.close()

        app.logger.info("Inscription %s enregistrée.", "artiste")

        # Connecter automatiquement l'artiste
        session.clear()
        session["utilisateur_id"] = nouvel_utilisateur_id
        session["nom"] = nom
        session["role"] = "artiste"

        # Rediriger vers l'espace utilisateur
        return redirect(url_for("espace"))

    return render_template("inscription_artiste.html")


# ==============================
# INSCRIPTION VISITEUR
# ==============================

@app.route("/inscription/visiteur", methods=["GET", "POST"])
def inscription_visiteur():

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        date_naissance = request.form.get("date_naissance", "")
        sexe = request.form.get("sexe", "").strip()
        email = request.form.get("email", "").strip().lower()
        telephone = request.form.get("telephone", "").strip()
        password = request.form.get("password", "")
        confirmation_password = request.form.get("confirmation_password", "")

        # ==============================
        # NOM
        # ==============================

        if not nom:
            return "Vous devez compléter le nom."

        if not sexe:
            return "Vous devez sélectionner votre sexe."

        # ==============================
        # EMAIL
        # ==============================

        erreur_email = verifier_email(email)

        if erreur_email:
            return erreur_email

        # ==============================
        # TELEPHONE
        # ==============================

        erreur_telephone = verifier_telephone(telephone)

        if erreur_telephone:
            return erreur_telephone

        # ==============================
        # DATE DE NAISSANCE
        # ==============================

        try:

            date_naissance = datetime.strptime(
                date_naissance,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return "La date de naissance est incorrecte."

        if date_naissance > date.today():
            return "La date de naissance ne peut pas être dans le futur."

        # ==============================
        # CALCUL DE L'AGE
        # ==============================

        aujourd_hui = date.today()

        age = aujourd_hui.year - date_naissance.year

        if (aujourd_hui.month, aujourd_hui.day) < (
            date_naissance.month,
            date_naissance.day
        ):
            age -= 1

        # ==============================
        # AGE MINIMUM
        # ==============================

        if age < 18:
            return "Vous devez avoir au moins 18 ans pour vous inscrire comme visiteur."

        # ==============================
        # MOT DE PASSE
        # ==============================

        erreur_password = verifier_mot_de_passe(password)

        if erreur_password:
            return erreur_password

        # ==============================
        # CONFIRMATION DU MOT DE PASSE
        # ==============================

        if confirmation_password != password:
            return "Veuillez réécrire votre mot de passe."

        # ==============================
        # HACHAGE DU MOT DE PASSE
        # ==============================

        mot_de_passe_hache = generate_password_hash(password)

        # ==============================
        # CONNEXION A SQLITE
        # ==============================

        connexion = ouvrir_base()
        try:
            curseur = connexion.cursor()
            curseur.execute("""
                INSERT INTO utilisateur
                (nom, date_naissance, sexe, email, telephone, mot_de_passe, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nom,
                date_naissance.isoformat(),
                sexe,
                email,
                "+243" + telephone,
                mot_de_passe_hache,
                "visiteur"
            ))
            nouvel_utilisateur_id = curseur.lastrowid
            connexion.commit()
        except sqlite3.IntegrityError:
            connexion.rollback()
            return "Cette adresse e-mail est déjà utilisée."
        except sqlite3.Error:
            connexion.rollback()
            app.logger.exception("Erreur pendant la création du compte.")
            return "Impossible de créer le compte pour le moment.", 500
        finally:
            connexion.close()

        app.logger.info("Inscription %s enregistrée.", "visiteur")

        # Connecter automatiquement le visiteur
        session.clear()
        session["utilisateur_id"] = nouvel_utilisateur_id
        session["nom"] = nom
        session["role"] = "visiteur"

        # Rediriger vers l'espace utilisateur
        return redirect(url_for("espace"))

    return render_template("inscription_visiteur.html")


# ==============================
# ESPACE UTILISATEUR
# ==============================

@app.route("/espace")
def espace():

    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") == "artiste":

        connexion_db = ouvrir_base()
        connexion_db.row_factory = sqlite3.Row

        try:
            curseur_db = connexion_db.cursor()

            # Récupérer les œuvres de l'artiste connecté
            curseur_db.execute("""
                SELECT id, titre, type, description, date_creation, prix
                FROM oeuvre
                WHERE artiste_id = ?
                ORDER BY id DESC
            """, (session["utilisateur_id"],))

            lignes_oeuvres = curseur_db.fetchall()

            # Préparer les œuvres et leurs images
            oeuvres = []

            for ligne in lignes_oeuvres:
                oeuvre = dict(ligne)

                curseur_db.execute("""
                    SELECT id, chemin_fichier
                    FROM fichier_oeuvre
                    WHERE oeuvre_id = ?
                      AND type_fichier = 'image'
                    ORDER BY id
                """, (oeuvre["id"],))

                oeuvre["images"] = [
                    dict(fichier)
                    for fichier in curseur_db.fetchall()
                ]

                oeuvres.append(oeuvre)

        except sqlite3.Error:
            app.logger.exception(
                "Erreur lors du chargement des œuvres."
            )
            return "Impossible de charger vos œuvres.", 500

        finally:
            connexion_db.close()

        return render_template(
            "espace_artiste.html",
            oeuvres=oeuvres
        )

    if session.get("role") == "visiteur":
        return render_template("espace_visiteur.html")

    return "Rôle utilisateur incorrect.", 403

# ==============================
# AJOUTER UNE OEUVRE
# ==============================

@app.route("/ajouter-oeuvre", methods=["GET", "POST"])
def ajouter_oeuvre():
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "artiste":
        return "Accès réservé aux artistes.", 403, 403

    if request.method == "GET":
        return render_template("ajouter_oeuvre.html")

    # Lire les informations du formulaire.
    titre = request.form.get("titre", "").strip()
    type_oeuvre = request.form.get("type", "").strip().lower()
    description = request.form.get("description", "").strip()
    date_creation = request.form.get("date_creation", "").strip()
    prix = request.form.get("prix", "").strip()

    # Lire les fichiers du formulaire.
    fichier_musique = request.files.get("fichier_musique")
    images_oeuvre = [
        fichier for fichier in request.files.getlist("images_oeuvre")
        if fichier and fichier.filename.strip()
    ]
    fichier_litterature = request.files.get("fichier_litterature")
    images_sculpture = [
        fichier for fichier in request.files.getlist("images_sculpture")
        if fichier and fichier.filename.strip()
    ]

    # Valider les champs textuels avant d'ouvrir une connexion SQL.
    if not titre:
        return "Vous devez donner un titre à votre œuvre."

    types_autorises = {"musique", "peinture", "litterature", "sculpture"}
    if type_oeuvre not in types_autorises:
        return "Le type d'œuvre est incorrect."

    try:
        date_validee = datetime.strptime(date_creation, "%Y-%m-%d").date()
    except ValueError:
        return "La date de création est incorrecte."

    if date_validee > date.today():
        return "La date de création ne peut pas être dans le futur."

    try:
        prix_valide = float(prix)
    except (ValueError, TypeError):
        return "Le prix doit être un nombre."

    if not math.isfinite(prix_valide) or prix_valide <= 0:
        return "Le prix doit être un nombre fini supérieur à zéro."

    # Valider les types et le nombre de fichiers.
    extensions_images = {"jpg", "jpeg", "png", "webp"}
    extensions_audio = {"mp3", "wav", "ogg", "m4a"}
    extensions_documents = {"pdf", "doc", "docx", "txt"}

    fichiers_a_enregistrer = []

    if type_oeuvre == "musique":
        if not verifier_extension(fichier_musique, extensions_audio):
            return "Veuillez envoyer un fichier audio autorisé (MP3, WAV, OGG ou M4A)."

        if not verifier_taille_fichier(fichier_musique, 20):
            return "Le fichier audio doit peser au maximum 20 Mo."

        fichiers_a_enregistrer = [(fichier_musique, "audio")]

    elif type_oeuvre == "peinture":
        if not 1 <= len(images_oeuvre) <= 3:
            return "Une peinture doit comporter entre 1 et 3 images."

        for fichier in images_oeuvre:
            if not verifier_extension(fichier, extensions_images):
                return "Les images doivent être au format JPG, JPEG, PNG ou WEBP."

            if not verifier_taille_fichier(fichier, 7):
                return "Chaque image doit peser au maximum 7 Mo."

        fichiers_a_enregistrer = [
            (fichier, "image") for fichier in images_oeuvre
        ]

    elif type_oeuvre == "litterature":
        if not verifier_extension(fichier_litterature, extensions_documents):
            return "Veuillez envoyer un document autorisé (PDF, DOC, DOCX ou TXT)."

        if not verifier_taille_fichier(fichier_litterature, 10):
            return "Le document doit peser au maximum 10 Mo."

        fichiers_a_enregistrer = [(fichier_litterature, "document")]

    elif type_oeuvre == "sculpture":
        if not 1 <= len(images_sculpture) <= 3:
            return "Une sculpture doit comporter entre 1 et 3 images."

        for fichier in images_sculpture:
            if not verifier_extension(fichier, extensions_images):
                return "Les images doivent être au format JPG, JPEG, PNG ou WEBP."

            if not verifier_taille_fichier(fichier, 7):
                return "Chaque image doit peser au maximum 7 Mo."

        fichiers_a_enregistrer = [
            (fichier, "image") for fichier in images_sculpture
        ]

    # L'enregistrement commence seulement après la validation.
    connexion_db = ouvrir_base()
    fichiers_sauvegardes = []

    try:
        curseur_db = connexion_db.cursor()
        curseur_db.execute("""
            INSERT INTO oeuvre
                (artiste_id, titre, type, description, date_creation, prix)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["utilisateur_id"],
            titre,
            type_oeuvre,
            description,
            date_validee.isoformat(),
            prix_valide
        ))

        oeuvre_id = curseur_db.lastrowid

        for fichier, type_fichier in fichiers_a_enregistrer:
            nom_securise = secure_filename(fichier.filename)
            # L'extension est déjà validée par verifier_extension().
            extension = nom_securise.rsplit(".", 1)[1].lower()
            nom_unique = f"{uuid.uuid4().hex}.{extension}"
            chemin_complet = os.path.join(app.config["UPLOAD_FOLDER"], nom_unique)

            fichier.save(chemin_complet)
            fichiers_sauvegardes.append(chemin_complet)

            curseur_db.execute("""
                INSERT INTO fichier_oeuvre
                    (oeuvre_id, chemin_fichier, type_fichier)
                VALUES (?, ?, ?)
            """, (
                oeuvre_id,
                f"uploads/{nom_unique}",
                type_fichier
            ))

        connexion_db.commit()

    except (sqlite3.Error, OSError, IndexError):
        connexion_db.rollback()
        # Éviter de laisser des fichiers orphelins si la transaction échoue.
        for chemin in fichiers_sauvegardes:
            try:
                if os.path.exists(chemin):
                    os.remove(chemin)
            except OSError:
                app.logger.exception("Impossible de nettoyer un fichier incomplet.")
        app.logger.exception("Échec de l'enregistrement d'une œuvre.")
        return "Une erreur est survenue pendant l'enregistrement de l'œuvre ou de ses fichiers."

    finally:
        connexion_db.close()

    return redirect(url_for("mes_oeuvres"))

# ==============================
# Modification d'une oeuvre
# ==============================

@app.route("/modifier-oeuvre/<int:oeuvre_id>", methods=["GET", "POST"])
def modifier_oeuvre(oeuvre_id):

    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "artiste":
        return "Accès réservé aux artistes.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row
    fichiers_sauvegardes = []
    anciens_chemins = []

    try:
        curseur_db = connexion_db.cursor()

        # 1. Vérifier que l'œuvre appartient à l'artiste connecté.
        curseur_db.execute("""
            SELECT id, artiste_id, titre, type,
                   description, date_creation, prix
            FROM oeuvre
            WHERE id = ? AND artiste_id = ?
        """, (oeuvre_id, session["utilisateur_id"]))

        ligne_oeuvre = curseur_db.fetchone()

        if ligne_oeuvre is None:
            return "Œuvre introuvable.", 404

        oeuvre = dict(ligne_oeuvre)

        # 2. Récupérer les fichiers actuellement associés.
        curseur_db.execute("""
            SELECT id, chemin_fichier, type_fichier
            FROM fichier_oeuvre
            WHERE oeuvre_id = ?
            ORDER BY id
        """, (oeuvre_id,))

        fichiers_existants = [
            dict(fichier)
            for fichier in curseur_db.fetchall()
        ]

        # 3. Afficher les informations si la page est demandée en GET.
        if request.method == "GET":
            return render_template(
                "modifier_oeuvre.html",
                oeuvre=oeuvre,
                fichiers=fichiers_existants
            )

        # 4. Lire les nouvelles informations.
        titre = request.form.get("titre", "").strip()
        description = request.form.get("description", "").strip()
        date_creation = request.form.get("date_creation", "").strip()
        prix = request.form.get("prix", "").strip()

        if not titre:
            return "Vous devez donner un titre à votre œuvre."

        try:
            date_validee = datetime.strptime(
                date_creation, "%Y-%m-%d"
            ).date()
        except ValueError:
            return "La date de création est incorrecte."

        if date_validee > date.today():
            return "La date de création ne peut pas être dans le futur."

        try:
            prix_valide = float(prix)
        except (ValueError, TypeError):
            return "Le prix doit être un nombre."

        if not math.isfinite(prix_valide) or prix_valide <= 0:
            return "Le prix doit être un nombre fini supérieur à zéro."

        # 5. Identifier les éventuels nouveaux fichiers.
        fichier_musique = request.files.get("fichier_musique")
        fichier_litterature = request.files.get("fichier_litterature")

        if not fichier_musique or not fichier_musique.filename.strip():
            fichier_musique = None

        if not fichier_litterature or not fichier_litterature.filename.strip():
            fichier_litterature = None

        images_oeuvre = [
            fichier for fichier in request.files.getlist("images_oeuvre")
            if fichier and fichier.filename.strip()
        ]

        images_sculpture = [
            fichier for fichier in request.files.getlist("images_sculpture")
            if fichier and fichier.filename.strip()
        ]

        extensions_images = {"jpg", "jpeg", "png", "webp"}
        extensions_audio = {"mp3", "wav", "ogg", "m4a"}
        extensions_documents = {"pdf", "doc", "docx", "txt"}

        fichiers_a_enregistrer = []
        type_oeuvre = oeuvre["type"]

        # 6. Valider les nouveaux fichiers, s'il y en a.
        if type_oeuvre == "musique" and fichier_musique:
            if not verifier_extension(fichier_musique, extensions_audio):
                return "Format audio non autorisé."

            if not verifier_taille_fichier(fichier_musique, 20):
                return "Le fichier audio doit peser au maximum 20 Mo."

            fichiers_a_enregistrer = [(fichier_musique, "audio")]

        elif type_oeuvre == "peinture" and images_oeuvre:
            if not 1 <= len(images_oeuvre) <= 3:
                return "Sélectionnez entre 1 et 3 images."

            for fichier in images_oeuvre:
                if not verifier_extension(fichier, extensions_images):
                    return "Format d'image non autorisé."

                if not verifier_taille_fichier(fichier, 7):
                    return "Chaque image doit peser au maximum 7 Mo."

            fichiers_a_enregistrer = [
                (fichier, "image") for fichier in images_oeuvre
            ]

        elif type_oeuvre == "litterature" and fichier_litterature:
            if not verifier_extension(fichier_litterature, extensions_documents):
                return "Format de document non autorisé."

            if not verifier_taille_fichier(fichier_litterature, 10):
                return "Le document doit peser au maximum 10 Mo."

            fichiers_a_enregistrer = [(fichier_litterature, "document")]

        elif type_oeuvre == "sculpture" and images_sculpture:
            if not 1 <= len(images_sculpture) <= 3:
                return "Sélectionnez entre 1 et 3 images."

            for fichier in images_sculpture:
                if not verifier_extension(fichier, extensions_images):
                    return "Format d'image non autorisé."

                if not verifier_taille_fichier(fichier, 7):
                    return "Chaque image doit peser au maximum 7 Mo."

            fichiers_a_enregistrer = [
                (fichier, "image") for fichier in images_sculpture
            ]

        # 7. Enregistrer les nouveaux fichiers avant de modifier la base.
        if fichiers_a_enregistrer:
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            fichiers_prepares = []

            for fichier, type_fichier in fichiers_a_enregistrer:
                nom_securise = secure_filename(fichier.filename)

                if "." not in nom_securise:
                    raise ValueError("Nom de fichier incorrect.")

                extension = nom_securise.rsplit(".", 1)[1].lower()
                nom_unique = f"{uuid.uuid4().hex}.{extension}"

                chemin_complet = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nom_unique
                )

                fichier.save(chemin_complet)
                fichiers_sauvegardes.append(chemin_complet)

                fichiers_prepares.append((
                    f"uploads/{nom_unique}",
                    type_fichier
                ))

            anciens_chemins = [
                fichier["chemin_fichier"]
                for fichier in fichiers_existants
            ]

        # 8. Modifier les informations de l'œuvre.
        curseur_db.execute("""
            UPDATE oeuvre
            SET titre = ?,
                description = ?,
                date_creation = ?,
                prix = ?
            WHERE id = ? AND artiste_id = ?
        """, (
            titre,
            description,
            date_validee.isoformat(),
            prix_valide,
            oeuvre_id,
            session["utilisateur_id"]
        ))

        if curseur_db.rowcount != 1:
            raise sqlite3.IntegrityError(
                "L'œuvre n'a pas pu être mise à jour."
            )

        # 9. Remplacer les fichiers uniquement si de nouveaux
        # fichiers ont été fournis.
        if fichiers_a_enregistrer:
            curseur_db.execute("""
                DELETE FROM fichier_oeuvre
                WHERE oeuvre_id = ?
            """, (oeuvre_id,))

            for chemin_fichier, type_fichier in fichiers_prepares:
                curseur_db.execute("""
                    INSERT INTO fichier_oeuvre
                        (oeuvre_id, chemin_fichier, type_fichier)
                    VALUES (?, ?, ?)
                """, (oeuvre_id, chemin_fichier, type_fichier))

        connexion_db.commit()

    except (sqlite3.Error, OSError, ValueError, IndexError):
        connexion_db.rollback()

        # Nettoyer les nouveaux fichiers si la transaction échoue.
        for chemin in fichiers_sauvegardes:
            try:
                if os.path.isfile(chemin):
                    os.remove(chemin)
            except OSError:
                app.logger.exception(
                    "Impossible de nettoyer un nouveau fichier."
                )

        app.logger.exception("Échec de la modification d'une œuvre.")
        return "Une erreur est survenue pendant la modification."

    finally:
        connexion_db.close()

    # 10. Supprimer les anciens fichiers seulement après la validation
    # de la transaction en base de données.
    for ancien_chemin in anciens_chemins:
        nom_fichier = os.path.basename(
            ancien_chemin.replace("\\", "/")
        )
        chemin_complet = os.path.join(
            app.config["UPLOAD_FOLDER"],
            nom_fichier
        )

        try:
            if os.path.isfile(chemin_complet):
                os.remove(chemin_complet)
        except OSError:
            app.logger.exception(
                "Impossible de supprimer un ancien fichier."
            )

    return redirect(url_for("mes_oeuvres"))

# ==============================
# MES OEUVRES
# ==============================



@app.route("/mes-oeuvres")
def mes_oeuvres():

    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "artiste":
        return "Accès réservé aux artistes.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        # Récupérer les œuvres de l'artiste connecté
        curseur_db.execute("""
            SELECT id, titre, type, description, date_creation, prix
            FROM oeuvre
            WHERE artiste_id = ?
            ORDER BY id DESC
        """, (session["utilisateur_id"],))

        lignes_oeuvres = curseur_db.fetchall()

        # Préparer les œuvres et leurs images
        oeuvres = []

        for ligne in lignes_oeuvres:
            oeuvre = dict(ligne)

            curseur_db.execute("""
                SELECT id, chemin_fichier
                FROM fichier_oeuvre
                WHERE oeuvre_id = ?
                  AND type_fichier = 'image'
                ORDER BY id
            """, (oeuvre["id"],))

            oeuvre["images"] = [
                dict(fichier)
                for fichier in curseur_db.fetchall()
            ]

            oeuvres.append(oeuvre)

    except sqlite3.Error:
        app.logger.exception("Erreur lors du chargement des œuvres.")
        return "Impossible de charger vos œuvres.", 500

    finally:
        connexion_db.close()

    return render_template(
        "mes_oeuvres.html",
        oeuvres=oeuvres
    )

@app.route("/uploads/<path:filename>")
def afficher_fichier_upload(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )

@app.route("/oeuvre/<int:oeuvre_id>")
def details_oeuvre(oeuvre_id):

    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    role = session.get("role")

    if role not in ("artiste", "visiteur"):
        return "Accès interdit.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        # Récupérer l'œuvre et les coordonnées de son artiste
        curseur_db.execute("""
            SELECT
                o.id,
                o.artiste_id,
                o.titre,
                o.type,
                o.description,
                o.date_creation,
                o.prix,
                u.nom AS artiste_nom,
                u.telephone AS artiste_telephone
            FROM oeuvre AS o
            JOIN utilisateur AS u
                ON u.id = o.artiste_id
            WHERE o.id = ?
              AND u.role = 'artiste'
        """, (oeuvre_id,))
        ligne_oeuvre = curseur_db.fetchone()

        if ligne_oeuvre is None:
            return "Œuvre introuvable.", 404

        oeuvre = dict(ligne_oeuvre)

        # Un artiste consulte uniquement ses propres œuvres ici.
        if (
            role == "artiste"
            and oeuvre["artiste_id"] != session["utilisateur_id"]
        ):
            return "Accès interdit.", 403

        # Récupérer tous les fichiers liés à cette œuvre
        curseur_db.execute("""
            SELECT id, chemin_fichier, type_fichier
            FROM fichier_oeuvre
            WHERE oeuvre_id = ?
            ORDER BY id
        """, (oeuvre_id,))

        fichiers = [
            dict(fichier)
            for fichier in curseur_db.fetchall()
        ]

    except sqlite3.Error:
        app.logger.exception(
            "Erreur lors du chargement des détails de l'œuvre."
        )
        return "Impossible de charger les détails de cette œuvre.", 500

    finally:
        connexion_db.close()

    return render_template(
        "details_oeuvre.html",
        oeuvre=oeuvre,
        fichiers=fichiers
    )

@app.route("/supprimer-oeuvre/<int:oeuvre_id>", methods=["POST"])
def supprimer_oeuvre(oeuvre_id):

    # 1. Vérifier la connexion et le rôle
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "artiste":
        return "Accès réservé aux artistes.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row
    fichiers_a_supprimer = []

    try:
        curseur_db = connexion_db.cursor()

        # 2. Vérifier que l'œuvre appartient à cet artiste
        curseur_db.execute("""
            SELECT id
            FROM oeuvre
            WHERE id = ? AND artiste_id = ?
        """, (
            oeuvre_id,
            session["utilisateur_id"]
        ))

        oeuvre = curseur_db.fetchone()

        if oeuvre is None:
            return "Œuvre introuvable.", 404

        # 3. Récupérer les chemins des fichiers associés
        curseur_db.execute("""
            SELECT chemin_fichier
            FROM fichier_oeuvre
            WHERE oeuvre_id = ?
        """, (oeuvre_id,))

        fichiers_a_supprimer = [
            ligne["chemin_fichier"]
            for ligne in curseur_db.fetchall()
        ]

        # 4. Supprimer l'œuvre de la base de données
        curseur_db.execute("""
            DELETE FROM oeuvre
            WHERE id = ? AND artiste_id = ?
        """, (
            oeuvre_id,
            session["utilisateur_id"]
        ))

        if curseur_db.rowcount != 1:
            connexion_db.rollback()
            return "Œuvre introuvable.", 404

        # Les fichiers associés sont retirés de la table
        # fichier_oeuvre grâce à ON DELETE CASCADE.
        connexion_db.commit()

    except sqlite3.Error:
        connexion_db.rollback()
        app.logger.exception(
            "Erreur lors de la suppression de l'œuvre."
        )
        return "Impossible de supprimer cette œuvre.", 500

    finally:
        connexion_db.close()

    # 5. Supprimer les fichiers physiques après validation
    for chemin in fichiers_a_supprimer:
        nom_fichier = os.path.basename(
            chemin.replace("\\", "/")
        )

        chemin_absolu = os.path.join(
            app.config["UPLOAD_FOLDER"],
            nom_fichier
        )

        try:
            if os.path.isfile(chemin_absolu):
                os.remove(chemin_absolu)

        except OSError:
            app.logger.exception(
                "Impossible de supprimer le fichier : %s",
                nom_fichier
            )

    # 6. Retourner à la liste des œuvres
    return redirect(url_for("mes_oeuvres"))

# ==============================
# AFFICHER UN FICHIER D'UNE ŒUVRE
# ==============================


@app.route("/fichier-oeuvre/<int:fichier_id>")
def afficher_fichier_oeuvre(fichier_id):

    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    role = session.get("role")

    if role not in ("artiste", "visiteur"):
        return "Accès interdit.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        curseur_db.execute("""
            SELECT
                f.chemin_fichier,
                f.type_fichier,
                o.artiste_id
            FROM fichier_oeuvre AS f
            JOIN oeuvre AS o
                ON o.id = f.oeuvre_id
            WHERE f.id = ?
        """, (fichier_id,))

        fichier = curseur_db.fetchone()

    except sqlite3.Error:
        app.logger.exception("Erreur lors de la récupération du fichier.")
        return "Impossible de charger ce fichier.", 500

    finally:
        connexion_db.close()

    if fichier is None:
        return "Fichier introuvable.", 404

    # Un artiste ne peut accéder qu'aux fichiers de ses propres œuvres.
    if role == "artiste":
        if fichier["artiste_id"] != session["utilisateur_id"]:
            return "Accès interdit.", 403

    # Les visiteurs connectés peuvent consulter les images et écouter l'audio.
    # Les documents littéraires restent réservés au contact avec l'artiste.
    if role == "visiteur":
        if fichier["type_fichier"] not in ("image", "audio"):
            return "Veuillez contacter l'artiste pour consulter ce document.", 403

    nom_fichier = os.path.basename(fichier["chemin_fichier"])

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        nom_fichier,
        as_attachment=False
    )


# ==============================
# EXPLORER
# ==============================


@app.route("/explorer")
def explorer():

    # Vérifier la connexion
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    # Réserver cette page aux visiteurs
    if session.get("role") != "visiteur":
        return "Accès réservé aux visiteurs.", 403

    # Récupérer les filtres transmis dans l'URL
    categorie = request.args.get("categorie", "").strip().lower()
    recherche = request.args.get("recherche", "").strip()

    # Catégories autorisées
    categories_autorisees = {
        "musique",
        "peinture",
        "litterature",
        "sculpture"
    }

    # Ignorer les catégories inconnues
    if categorie not in categories_autorisees:
        categorie = ""

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        # Récupérer les œuvres et le nom de leur artiste
        requete = """
            SELECT
                o.id,
                o.artiste_id,
                o.titre,
                o.type,
                o.description,
                o.date_creation,
                o.prix,
                u.nom AS artiste_nom
            FROM oeuvre AS o
            JOIN utilisateur AS u
                ON u.id = o.artiste_id
            WHERE u.role = 'artiste'
        """

        parametres = []

        # Filtrer par catégorie
        if categorie:
            requete += " AND o.type = ?"
            parametres.append(categorie)

        # Rechercher chaque mot dans le titre,
        # la description ou le nom de l'artiste
        if recherche:
            mots_recherche = recherche.split()

            for mot in mots_recherche:
                requete += """
                    AND (
                       SANS_ACCENTS(o.titre) LIKE SANS_ACCENTS(?)
                       OR SANS_ACCENTS(o.description) LIKE SANS_ACCENTS(?)
                       OR SANS_ACCENTS(u.nom) LIKE SANS_ACCENTS(?)
                    )
                """

                terme = f"%{mot}%"

                parametres.extend([
                    terme,
                    terme,
                    terme
                ])

        # Afficher les œuvres les plus récentes en premier
        requete += " ORDER BY o.id DESC"

        curseur_db.execute(requete, parametres)

        oeuvres = [
            dict(ligne)
            for ligne in curseur_db.fetchall()
        ]

        # Vérifier si un artiste correspondant au nom recherché existe.
        artiste_trouve = False

        if recherche and not oeuvres:
            terme_artiste = f"%{recherche}%"

            curseur_db.execute("""
                SELECT 1
                FROM utilisateur
                WHERE role = 'artiste'
                  AND nom LIKE ? COLLATE NOCASE
                LIMIT 1
            """, (terme_artiste,))

            artiste_trouve = curseur_db.fetchone() is not None

    except sqlite3.Error:
        app.logger.exception(
            "Erreur pendant le chargement de la galerie."
        )
        return "Impossible de charger les œuvres pour le moment.", 500

    finally:
        connexion_db.close()

    # Transmettre les résultats au fichier HTML
    return render_template(
        "explorer.html",
        oeuvres=oeuvres,
        categorie=categorie,
        recherche=recherche,
        artiste_trouve=artiste_trouve
    )

# ==============================
# MON PROFIL ARTISTE
# PROFIL PRIVE
# ==============================

@app.route("/mon-profil")
def mon_profil():
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "artiste":
        return "Accès réservé aux artistes.", 403, 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row
    try:
        curseur_db = connexion_db.cursor()
        curseur_db.execute("""
            SELECT id, nom, date_naissance, sexe, email, telephone
            FROM utilisateur
            WHERE id = ? AND role = 'artiste'
        """, (session["utilisateur_id"],))
        ligne_artiste = curseur_db.fetchone()
        if ligne_artiste is None:
            return "Profil artiste introuvable.", 404
        artiste = dict(ligne_artiste)

        curseur_db.execute("""
            SELECT id, titre, type, description, date_creation, prix
            FROM oeuvre
            WHERE artiste_id = ?
            ORDER BY id DESC
        """, (artiste["id"],))
        oeuvres = [dict(ligne) for ligne in curseur_db.fetchall()]
    except sqlite3.Error:
        app.logger.exception("Erreur lors du chargement du profil artiste.")
        return "Impossible de charger votre profil pour le moment.", 500
    finally:
        connexion_db.close()

    return render_template(
        "profil_artiste.html",
        mode="prive",
        artiste_id=artiste["id"],
        artiste=artiste,
        oeuvres=oeuvres
    )


@app.route("/artiste/<int:artiste_id>")
def profil_artiste(artiste_id):
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "visiteur":
        return "Accès réservé aux visiteurs.", 403, 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row
    try:
        curseur_db = connexion_db.cursor()
        curseur_db.execute("""
            SELECT id, nom, email, telephone
            FROM utilisateur
            WHERE id = ? AND role = 'artiste'
        """, (artiste_id,))
        ligne_artiste = curseur_db.fetchone()
        if ligne_artiste is None:
            return "Artiste introuvable.", 404
        artiste = dict(ligne_artiste)

        curseur_db.execute("""
            SELECT id, titre, type, description, date_creation, prix
            FROM oeuvre
            WHERE artiste_id = ?
            ORDER BY id DESC
        """, (artiste_id,))
        oeuvres = [dict(ligne) for ligne in curseur_db.fetchall()]
    except sqlite3.Error:
        app.logger.exception("Erreur lors du chargement du profil public.")
        return "Impossible de charger ce profil pour le moment.", 500
    finally:
        connexion_db.close()

    return render_template(
        "profil_artiste.html",
        mode="public",
        artiste_id=artiste_id,
        artiste=artiste,
        oeuvres=oeuvres
    )


@app.route("/deconnexion")
def deconnexion():
    session.clear()
    return redirect(url_for("connexion"))


# ==============================
# MODIFIER PROFIL ARTISTE
# ==============================

@app.route("/modifier-profil-artiste", methods=["GET", "POST"])
def modifier_profil_artiste():
    """Permet à un artiste de modifier son profil."""
    
    # 1. Vérifier la connexion
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    # 2. Réserver la page aux artistes
    if session.get("role") != "artiste":
        return "Accès réservé aux artistes.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        # 3. Charger uniquement le profil de l'artiste connecté
        curseur_db.execute("""
            SELECT id, nom, date_naissance, sexe, email, telephone
            FROM utilisateur
            WHERE id = ? AND role = 'artiste'
        """, (session["utilisateur_id"],))

        ligne_utilisateur = curseur_db.fetchone()

        if ligne_utilisateur is None:
            return "Profil artiste introuvable.", 404

        utilisateur = dict(ligne_utilisateur)

        # Calculer la date maximale (18 ans minimum)
        date_max = date.today().replace(year=date.today().year - 18).isoformat()

        # 4. Traiter le formulaire envoyé
        if request.method == "POST":

            nom = request.form.get("nom", "").strip()
            date_naissance = request.form.get("date_naissance", "").strip()
            sexe = request.form.get("sexe", "").strip()
            email = request.form.get("email", "").strip()
            telephone = request.form.get("telephone", "").strip()

            # Garder les valeurs saisies en cas d'erreur
            utilisateur.update({
                "nom": nom,
                "date_naissance": date_naissance,
                "sexe": sexe,
                "email": email,
                "telephone": telephone
            })

            # 5. Vérifier les données obligatoires
            if not nom:
                flash("Le nom est obligatoire.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            if len(nom) > 100:
                flash("Le nom ne peut pas dépasser 100 caractères.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            if not email or len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                flash("Veuillez saisir une adresse e-mail valide.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            if not telephone:
                flash("Le numéro de téléphone est obligatoire.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            if len(telephone) > 30:
                flash("Le numéro de téléphone est trop long.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            if not sexe or sexe not in ("Homme", "Femme", "Autre"):
                flash("Veuillez sélectionner votre sexe.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            if not date_naissance:
                flash("La date de naissance est obligatoire.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            # Vérifier la date de naissance
            try:
                naissance = date.fromisoformat(date_naissance)

                if naissance > date.today():
                    flash("La date de naissance ne peut pas être dans le futur.", "error")
                    return render_template(
                        "modifier_profil_artiste.html",
                        utilisateur=utilisateur,
                        date_max=date_max
                    ), 400

                # Vérifier l'âge minimum (18 ans)
                age = date.today().year - naissance.year
                if (date.today().month, date.today().day) < (naissance.month, naissance.day):
                    age -= 1

                if age < 18:
                    flash("Vous devez avoir au moins 18 ans.", "error")
                    return render_template(
                        "modifier_profil_artiste.html",
                        utilisateur=utilisateur,
                        date_max=date_max
                    ), 400

            except ValueError:
                flash("La date de naissance est invalide.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            # 6. Vérifier si l'adresse e-mail appartient à un autre compte
            curseur_db.execute("""
                SELECT id
                FROM utilisateur
                WHERE LOWER(email) = LOWER(?)
                  AND id != ?
                LIMIT 1
            """, (email, session["utilisateur_id"]))

            email_existant = curseur_db.fetchone()

            if email_existant:
                flash("Cette adresse e-mail est déjà utilisée par un autre compte.", "error")
                return render_template(
                    "modifier_profil_artiste.html",
                    utilisateur=utilisateur,
                    date_max=date_max
                ), 400

            # 7. Enregistrer les informations de l'artiste connecté
            curseur_db.execute("""
                UPDATE utilisateur
                SET nom = ?,
                    date_naissance = ?,
                    sexe = ?,
                    email = ?,
                    telephone = ?
                WHERE id = ? AND role = 'artiste'
            """, (
                nom,
                date_naissance,
                sexe,
                email,
                telephone,
                session["utilisateur_id"]
            ))

            # Mettre à jour le nom dans la session
            session["nom"] = nom

            connexion_db.commit()

            app.logger.info(
                "Profil de l'artiste %s modifié avec succès.",
                session["utilisateur_id"]
            )

            flash("Votre profil a été mis à jour avec succès !", "success")

            # 8. Retourner au profil après l'enregistrement
            return redirect(url_for("mon_profil"))

        # Afficher le formulaire lors de la première ouverture
        return render_template(
            "modifier_profil_artiste.html",
            utilisateur=utilisateur,
            date_max=date_max
        )

    except sqlite3.Error:
        app.logger.exception(
            "Erreur lors de la modification du profil artiste."
        )
        flash("Une erreur est survenue lors de la modification de votre profil.", "error")
        return redirect(url_for("mon_profil"))

    finally:
        connexion_db.close()


@app.route("/mon-profil-visiteur")
def profil_visiteur():
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    if session.get("role") != "visiteur":
        return "Accès réservé aux visiteurs.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row
    try:
        curseur_db = connexion_db.cursor()
        curseur_db.execute("""
            SELECT id, nom, date_naissance, sexe, email, telephone
            FROM utilisateur
            WHERE id = ? AND role = 'visiteur'
        """, (session["utilisateur_id"],))
        ligne_utilisateur = curseur_db.fetchone()
        if ligne_utilisateur is None:
            return "Profil visiteur introuvable.", 404
        utilisateur = dict(ligne_utilisateur)
    except sqlite3.Error:
        app.logger.exception("Erreur lors du chargement du profil visiteur.")
        return "Impossible de charger votre profil pour le moment.", 500
    finally:
        connexion_db.close()

    return render_template("profil_visiteur.html", utilisateur=utilisateur)

@app.route("/modifier-profil-visiteur", methods=["GET", "POST"])
def modifier_profil_visiteur():

    # 1. Vérifier la connexion
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    # 2. Réserver la page aux visiteurs
    if session.get("role") != "visiteur":
        return "Accès réservé aux visiteurs.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        # 3. Charger uniquement le profil du visiteur connecté
        curseur_db.execute("""
            SELECT id, nom, date_naissance, sexe, email, telephone
            FROM utilisateur
            WHERE id = ? AND role = 'visiteur'
        """, (session["utilisateur_id"],))

        ligne_utilisateur = curseur_db.fetchone()

        if ligne_utilisateur is None:
            return "Profil visiteur introuvable.", 404

        utilisateur = dict(ligne_utilisateur)

        # 4. Traiter le formulaire envoyé
        if request.method == "POST":

            nom = request.form.get("nom", "").strip()
            date_naissance = request.form.get(
                "date_naissance", ""
            ).strip()
            sexe = request.form.get("sexe", "").strip()
            email = request.form.get("email", "").strip()
            telephone = request.form.get("telephone", "").strip()

            # Garder les valeurs saisies en cas d'erreur
            utilisateur.update({
                "nom": nom,
                "date_naissance": date_naissance,
                "sexe": sexe,
                "email": email,
                "telephone": telephone
            })

            # 5. Vérifier les données
            if not nom:
                erreur = "Le nom est obligatoire."

            elif len(nom) > 100:
                erreur = "Le nom ne peut pas dépasser 100 caractères."

            elif (
                not email
                or len(email) > 254
                or not re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+",
                    email
                )
            ):
                erreur = "Veuillez saisir une adresse e-mail valide."

            elif len(telephone) > 30:
                erreur = "Le numéro de téléphone est trop long."

            elif sexe not in ("", "Homme", "Femme", "Autre"):
                erreur = "Veuillez choisir une valeur valide pour le sexe."

            else:
                erreur = None

            # Vérifier la date de naissance
            if not erreur and date_naissance:
                try:
                    naissance = date.fromisoformat(date_naissance)

                    if naissance > date.today():
                        erreur = "La date de naissance ne peut pas être dans le futur."

                except ValueError:
                    erreur = "La date de naissance est invalide."

            # 6. Vérifier si l'adresse e-mail appartient à un autre compte
            if not erreur:
                curseur_db.execute("""
                    SELECT id
                    FROM utilisateur
                    WHERE LOWER(email) = LOWER(?)
                      AND id != ?
                    LIMIT 1
                """, (
                    email,
                    session["utilisateur_id"]
                ))

                email_existant = curseur_db.fetchone()

                if email_existant:
                    erreur = "Cette adresse e-mail est déjà utilisée."

            # 7. Si les données sont invalides, afficher à nouveau le formulaire
            if erreur:
                return render_template(
                    "modifier_profil_visiteur.html",
                    utilisateur=utilisateur,
                    erreur=erreur
                ), 400

            # 8. Enregistrer uniquement les informations du visiteur connecté
            curseur_db.execute("""
                UPDATE utilisateur
                SET nom = ?,
                    date_naissance = ?,
                    sexe = ?,
                    email = ?,
                    telephone = ?
                WHERE id = ? AND role = 'visiteur'
            """, (
                nom,
                date_naissance,
                sexe,
                email,
                telephone,
                session["utilisateur_id"]
            ))

            connexion_db.commit()

            app.logger.info(
                "Profil du visiteur %s modifié.",
                session["utilisateur_id"]
            )

            # 9. Retourner au profil après l'enregistrement
            return redirect(url_for("profil_visiteur"))

        # Afficher le formulaire lors de la première ouverture
        return render_template(
            "modifier_profil_visiteur.html",
            utilisateur=utilisateur
        )

    except sqlite3.Error:
        app.logger.exception(
            "Erreur lors de la modification du profil visiteur."
        )

        return (
            "Impossible de modifier votre profil pour le moment.",
            500
        )

    finally:
        connexion_db.close()

# ==============================
# DETAIL D'UNE ŒUVRE
# ==============================

@app.route("/oeuvre/<int:oeuvre_id>")
def oeuvre(oeuvre_id):

    # Vérifier la connexion
    if "utilisateur_id" not in session:
        return redirect(url_for("connexion"))

    # Réserver cette page aux visiteurs
    if session.get("role") != "visiteur":
        return "Accès réservé aux visiteurs.", 403

    connexion_db = ouvrir_base()
    connexion_db.row_factory = sqlite3.Row

    try:
        curseur_db = connexion_db.cursor()

        # Récupérer l'œuvre et les coordonnées de son artiste
        curseur_db.execute("""
            SELECT
                o.id,
                o.artiste_id,
                o.titre,
                o.type,
                o.description,
                o.date_creation,
                o.prix,
                u.nom AS artiste_nom,
                u.telephone AS artiste_telephone,
                u.email AS artiste_email
            FROM oeuvre AS o
            JOIN utilisateur AS u
                ON u.id = o.artiste_id
            WHERE o.id = ?
              AND u.role = 'artiste'
        """, (oeuvre_id,))

        ligne_oeuvre = curseur_db.fetchone()

        if ligne_oeuvre is None:
            return "Cette œuvre n'existe pas.", 404

        oeuvre_donnees = dict(ligne_oeuvre)

        # Récupérer les fichiers associés à l'œuvre
        curseur_db.execute("""
            SELECT id, chemin_fichier, type_fichier
            FROM fichier_oeuvre
            WHERE oeuvre_id = ?
            ORDER BY id
        """, (oeuvre_id,))

        fichiers = [
            dict(ligne)
            for ligne in curseur_db.fetchall()
        ]

    except sqlite3.Error:
        app.logger.exception(
            "Erreur lors du chargement du détail de l'œuvre."
        )
        return "Impossible de charger cette œuvre pour le moment.", 500

    finally:
        connexion_db.close()

    # Transmettre les données à la page HTML
    return render_template(
        "oeuvre.html",
        oeuvre=oeuvre_donnees,
        fichiers=fichiers
    )


# ==============================
# CREATION / VERIFICATION DE LA BASE
# ==============================

creer_base()


# ==============================
# LANCEMENT DE FLASK
# ==============================

if __name__ == "__main__":
    # debug=True est réservé au développement local.
    app.run(debug=True)

