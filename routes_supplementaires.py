"""
Routes supplémentaires pour Arctic
À ajouter à app_new.py
"""

from flask import request, session, redirect, url_for, send_from_directory, render_template, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import uuid
import math
from datetime import datetime, date

# Ces fonctions doivent être ajoutées dans app_new.py dans register_routes(app)

def register_additional_routes(app):
    """Enregistre les routes supplémentaires manquantes."""
    
    from models import ouvrir_base
    from utils import verifier_extension, verifier_taille_fichier
    
    # AJOUTER/MODIFIER UNE OEUVRE (Route complète manquante dans app_new.py)
    @app.route("/ajouter-oeuvre", methods=["GET", "POST"])
    def ajouter_oeuvre():
        if "utilisateur_id" not in session:
            flash("Vous devez être connecté.", "warning")
            return redirect(url_for("connexion"))

        if session.get("role") != "artiste":
            flash("Accès réservé aux artistes.", "error")
            return redirect(url_for("espace"))

        if request.method == "GET":
            return render_template("ajouter_oeuvre.html")

        # Récupérer les données du formulaire
        titre = request.form.get("titre", "").strip()
        type_oeuvre = request.form.get("type", "").strip().lower()
        description = request.form.get("description", "").strip()
        date_creation = request.form.get("date_creation", "").strip()
        prix = request.form.get("prix", "").strip()

        # Validation
        if not titre:
            flash("Vous devez donner un titre à votre œuvre.", "error")
            return render_template("ajouter_oeuvre.html")

        types_autorises = {"musique", "peinture", "litterature", "sculpture"}
        if type_oeuvre not in types_autorises:
            flash("Le type d'œuvre est incorrect.", "error")
            return render_template("ajouter_oeuvre.html")

        try:
            date_validee = datetime.strptime(date_creation, "%Y-%m-%d").date()
        except ValueError:
            flash("La date de création est incorrecte.", "error")
            return render_template("ajouter_oeuvre.html")

        if date_validee > date.today():
            flash("La date de création ne peut pas être dans le futur.", "error")
            return render_template("ajouter_oeuvre.html")

        try:
            prix_valide = float(prix)
        except (ValueError, TypeError):
            flash("Le prix doit être un nombre.", "error")
            return render_template("ajouter_oeuvre.html")

        if not math.isfinite(prix_valide) or prix_valide <= 0:
            flash("Le prix doit être un nombre supérieur à zéro.", "error")
            return render_template("ajouter_oeuvre.html")

        # Gérer les fichiers selon le type
        extensions_images = {"jpg", "jpeg", "png", "webp"}
        extensions_audio = {"mp3", "wav", "ogg", "m4a"}
        extensions_documents = {"pdf", "doc", "docx", "txt"}

        fichiers_a_enregistrer = []

        if type_oeuvre == "musique":
            fichier_musique = request.files.get("fichier_musique")
            if not fichier_musique or not fichier_musique.filename:
                flash("Veuillez envoyer un fichier audio.", "error")
                return render_template("ajouter_oeuvre.html")

            if not verifier_extension(fichier_musique, extensions_audio):
                flash("Format audio non autorisé (MP3, WAV, OGG, M4A).", "error")
                return render_template("ajouter_oeuvre.html")

            if not verifier_taille_fichier(fichier_musique, 20):
                flash("Le fichier audio doit peser au maximum 20 Mo.", "error")
                return render_template("ajouter_oeuvre.html")

            fichiers_a_enregistrer = [(fichier_musique, "audio")]

        elif type_oeuvre == "peinture":
            images_oeuvre = [f for f in request.files.getlist("images_oeuvre") if f and f.filename.strip()]
            
            if not 1 <= len(images_oeuvre) <= 3:
                flash("Une peinture doit comporter entre 1 et 3 images.", "error")
                return render_template("ajouter_oeuvre.html")

            for fichier in images_oeuvre:
                if not verifier_extension(fichier, extensions_images):
                    flash("Les images doivent être au format JPG, JPEG, PNG ou WEBP.", "error")
                    return render_template("ajouter_oeuvre.html")

                if not verifier_taille_fichier(fichier, 7):
                    flash("Chaque image doit peser au maximum 7 Mo.", "error")
                    return render_template("ajouter_oeuvre.html")

            fichiers_a_enregistrer = [(f, "image") for f in images_oeuvre]

        elif type_oeuvre == "litterature":
            fichier_litterature = request.files.get("fichier_litterature")
            if not fichier_litterature or not fichier_litterature.filename:
                flash("Veuillez envoyer un document.", "error")
                return render_template("ajouter_oeuvre.html")

            if not verifier_extension(fichier_litterature, extensions_documents):
                flash("Format de document non autorisé (PDF, DOC, DOCX, TXT).", "error")
                return render_template("ajouter_oeuvre.html")

            if not verifier_taille_fichier(fichier_litterature, 10):
                flash("Le document doit peser au maximum 10 Mo.", "error")
                return render_template("ajouter_oeuvre.html")

            fichiers_a_enregistrer = [(fichier_litterature, "document")]

        elif type_oeuvre == "sculpture":
            images_sculpture = [f for f in request.files.getlist("images_sculpture") if f and f.filename.strip()]
            
            if not 1 <= len(images_sculpture) <= 3:
                flash("Une sculpture doit comporter entre 1 et 3 images.", "error")
                return render_template("ajouter_oeuvre.html")

            for fichier in images_sculpture:
                if not verifier_extension(fichier, extensions_images):
                    flash("Les images doivent être au format JPG, JPEG, PNG ou WEBP.", "error")
                    return render_template("ajouter_oeuvre.html")

                if not verifier_taille_fichier(fichier, 7):
                    flash("Chaque image doit peser au maximum 7 Mo.", "error")
                    return render_template("ajouter_oeuvre.html")

            fichiers_a_enregistrer = [(f, "image") for f in images_sculpture]

        # Enregistrer dans la base de données
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

            # Sauvegarder les fichiers
            for fichier, type_fichier in fichiers_a_enregistrer:
                nom_securise = secure_filename(fichier.filename)
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
            flash(f"L'œuvre '{titre}' a été ajoutée avec succès!", "success")
            return redirect(url_for("mes_oeuvres"))

        except (sqlite3.Error, OSError) as e:
            connexion_db.rollback()
            # Nettoyer les fichiers en cas d'erreur
            for chemin in fichiers_sauvegardes:
                try:
                    if os.path.exists(chemin):
                        os.remove(chemin)
                except OSError:
                    pass
            
            app.logger.error(f"Erreur lors de l'ajout de l'œuvre : {e}")
            flash("Une erreur est survenue lors de l'enregistrement de l'œuvre.", "error")
            return render_template("ajouter_oeuvre.html")

        finally:
            connexion_db.close()
    
    
    # SUPPRIMER UNE OEUVRE
    @app.route("/supprimer-oeuvre/<int:oeuvre_id>", methods=["POST"])
    def supprimer_oeuvre(oeuvre_id):
        if "utilisateur_id" not in session:
            flash("Vous devez être connecté.", "warning")
            return redirect(url_for("connexion"))

        if session.get("role") != "artiste":
            flash("Accès réservé aux artistes.", "error")
            return redirect(url_for("espace"))

        connexion_db = ouvrir_base()
        fichiers_a_supprimer = []

        try:
            curseur_db = connexion_db.cursor()

            # Vérifier que l'œuvre appartient à cet artiste
            curseur_db.execute("""
                SELECT id
                FROM oeuvre
                WHERE id = ? AND artiste_id = ?
            """, (oeuvre_id, session["utilisateur_id"]))

            oeuvre = curseur_db.fetchone()

            if oeuvre is None:
                flash("Œuvre introuvable.", "error")
                return redirect(url_for("mes_oeuvres"))

            # Récupérer les chemins des fichiers
            curseur_db.execute("""
                SELECT chemin_fichier
                FROM fichier_oeuvre
                WHERE oeuvre_id = ?
            """, (oeuvre_id,))

            fichiers_a_supprimer = [row[0] for row in curseur_db.fetchall()]

            # Supprimer l'œuvre
            curseur_db.execute("""
                DELETE FROM oeuvre
                WHERE id = ? AND artiste_id = ?
            """, (oeuvre_id, session["utilisateur_id"]))

            connexion_db.commit()
            flash("L'œuvre a été supprimée avec succès.", "success")

        except sqlite3.Error as e:
            connexion_db.rollback()
            app.logger.error(f"Erreur lors de la suppression de l'œuvre : {e}")
            flash("Impossible de supprimer cette œuvre.", "error")
            return redirect(url_for("mes_oeuvres"))

        finally:
            connexion_db.close()

        # Supprimer les fichiers physiques
        for chemin in fichiers_a_supprimer:
            nom_fichier = os.path.basename(chemin.replace("\\", "/"))
            chemin_absolu = os.path.join(app.config["UPLOAD_FOLDER"], nom_fichier)

            try:
                if os.path.isfile(chemin_absolu):
                    os.remove(chemin_absolu)
            except OSError:
                app.logger.warning(f"Impossible de supprimer le fichier : {nom_fichier}")

        return redirect(url_for("mes_oeuvres"))
