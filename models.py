"""
Modèles et gestion de la base de données pour Arctic
"""
import sqlite3
import os
from utils import normaliser_texte


# Variable globale pour le chemin de la base de données
_database_path = None


def set_database_path(path):
    """Définit le chemin de la base de données."""
    global _database_path
    _database_path = path


def get_database_path():
    """Récupère le chemin de la base de données."""
    global _database_path
    if _database_path is None:
        # Chemin par défaut
        return os.path.join(os.path.dirname(__file__), "arctic.db")
    return _database_path


# ==============================
# GESTION DE LA BASE DE DONNÉES
# ==============================

def ouvrir_base():
    """Ouvre une connexion à la base de données avec optimisations."""
    try:
        connexion = sqlite3.connect(get_database_path())
        connexion.row_factory = sqlite3.Row  # Retourner des dictionnaires
        connexion.create_function("SANS_ACCENTS", 1, normaliser_texte)
        connexion.execute("PRAGMA foreign_keys = ON")  # Activer les foreign keys
        connexion.execute("PRAGMA journal_mode=WAL")  # Mode Write-Ahead Logging
        return connexion
    except sqlite3.Error as e:
        print(f"Erreur lors de l'ouverture de la base : {e}")
        raise


def init_db():
    """Initialise la base de données avec les tables nécessaires."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        
        # Table utilisateur
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateur (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                date_naissance TEXT NOT NULL,
                sexe TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telephone TEXT NOT NULL,
                mot_de_passe TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('artiste', 'visiteur')),
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                derniere_connexion TIMESTAMP,
                actif INTEGER DEFAULT 1,
                CONSTRAINT email_format CHECK(email LIKE '%@%.%')
            )
        """)
        
        # Index pour accélérer les recherches
        curseur.execute("""
            CREATE INDEX IF NOT EXISTS idx_utilisateur_email 
            ON utilisateur(email)
        """)
        
        # Table oeuvre
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS oeuvre (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artiste_id INTEGER NOT NULL,
                titre TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('musique', 'peinture', 'litterature', 'sculpture')),
                description TEXT,
                date_creation TEXT NOT NULL,
                prix REAL NOT NULL CHECK(prix > 0),
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP,
                vues INTEGER DEFAULT 0,
                actif INTEGER DEFAULT 1,
                FOREIGN KEY (artiste_id) REFERENCES utilisateur(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour accélérer les recherches d'œuvres
        curseur.execute("""
            CREATE INDEX IF NOT EXISTS idx_oeuvre_artiste 
            ON oeuvre(artiste_id)
        """)
        curseur.execute("""
            CREATE INDEX IF NOT EXISTS idx_oeuvre_type 
            ON oeuvre(type)
        """)
        
        # Table fichier_oeuvre
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS fichier_oeuvre (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oeuvre_id INTEGER NOT NULL,
                chemin_fichier TEXT NOT NULL,
                type_fichier TEXT NOT NULL CHECK(type_fichier IN ('image', 'audio', 'document')),
                taille_octets INTEGER,
                ordre INTEGER DEFAULT 0,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour les fichiers
        curseur.execute("""
            CREATE INDEX IF NOT EXISTS idx_fichier_oeuvre 
            ON fichier_oeuvre(oeuvre_id)
        """)
        
        # Table favoris (nouvelle fonctionnalité)
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS favori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utilisateur_id INTEGER NOT NULL,
                oeuvre_id INTEGER NOT NULL,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE,
                FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE,
                UNIQUE(utilisateur_id, oeuvre_id)
            )
        """)
        
        # Table commentaires (nouvelle fonctionnalité)
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS commentaire (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oeuvre_id INTEGER NOT NULL,
                utilisateur_id INTEGER NOT NULL,
                contenu TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP,
                actif INTEGER DEFAULT 1,
                FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE
            )
        """)
        
        connexion.commit()
        print("✅ Base de données initialisée avec succès.")
        
    except sqlite3.Error as e:
        connexion.rollback()
        print(f"❌ Erreur lors de l'initialisation de la base : {e}")
        raise
    finally:
        connexion.close()


# ==============================
# FONCTIONS DE REQUÊTES - UTILISATEURS
# ==============================

def get_utilisateur_by_email(email):
    """Récupère un utilisateur par son email."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            SELECT id, nom, email, mot_de_passe, role, date_naissance, sexe, telephone
            FROM utilisateur
            WHERE LOWER(email) = LOWER(?)
              AND actif = 1
        """, (email,))
        return curseur.fetchone()
    finally:
        connexion.close()


def get_utilisateur_by_id(utilisateur_id):
    """Récupère un utilisateur par son ID."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            SELECT id, nom, email, role, date_naissance, sexe, telephone, date_creation
            FROM utilisateur
            WHERE id = ? AND actif = 1
        """, (utilisateur_id,))
        return curseur.fetchone()
    finally:
        connexion.close()


def creer_utilisateur(nom, date_naissance, sexe, email, telephone, mot_de_passe, role):
    """Crée un nouvel utilisateur dans la base."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            INSERT INTO utilisateur
            (nom, date_naissance, sexe, email, telephone, mot_de_passe, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nom, date_naissance, sexe, email, telephone, mot_de_passe, role))
        connexion.commit()
        return curseur.lastrowid
    except sqlite3.IntegrityError:
        connexion.rollback()
        return None
    finally:
        connexion.close()


def update_derniere_connexion(utilisateur_id):
    """Met à jour la date de dernière connexion."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            UPDATE utilisateur
            SET derniere_connexion = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (utilisateur_id,))
        connexion.commit()
    finally:
        connexion.close()


# ==============================
# FONCTIONS DE REQUÊTES - OEUVRES
# ==============================

def get_oeuvres_artiste(artiste_id, limit=None, offset=0):
    """Récupère les œuvres d'un artiste."""
    connexion = ouvrir_base()
    connexion.row_factory = sqlite3.Row
    try:
        curseur = connexion.cursor()
        query = """
            SELECT id, titre, type, description, date_creation, prix, vues, date_ajout
            FROM oeuvre
            WHERE artiste_id = ? AND actif = 1
            ORDER BY date_ajout DESC
        """
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        curseur.execute(query, (artiste_id,))
        return [dict(row) for row in curseur.fetchall()]
    finally:
        connexion.close()


def get_oeuvre_by_id(oeuvre_id):
    """Récupère une œuvre par son ID."""
    connexion = ouvrir_base()
    connexion.row_factory = sqlite3.Row
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            SELECT o.*, u.nom as artiste_nom
            FROM oeuvre o
            JOIN utilisateur u ON o.artiste_id = u.id
            WHERE o.id = ? AND o.actif = 1
        """, (oeuvre_id,))
        row = curseur.fetchone()
        return dict(row) if row else None
    finally:
        connexion.close()


def get_toutes_oeuvres(type_filtre=None, limit=None, offset=0, order_by='date_ajout DESC'):
    """Récupère toutes les œuvres avec filtres et pagination."""
    connexion = ouvrir_base()
    connexion.row_factory = sqlite3.Row
    try:
        curseur = connexion.cursor()
        
        query = """
            SELECT o.*, u.nom as artiste_nom
            FROM oeuvre o
            JOIN utilisateur u ON o.artiste_id = u.id
            WHERE o.actif = 1
        """
        params = []
        
        if type_filtre:
            query += " AND o.type = ?"
            params.append(type_filtre)
        
        query += f" ORDER BY o.{order_by}"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        curseur.execute(query, params)
        return [dict(row) for row in curseur.fetchall()]
    finally:
        connexion.close()


def get_fichiers_oeuvre(oeuvre_id):
    """Récupère les fichiers associés à une œuvre."""
    connexion = ouvrir_base()
    connexion.row_factory = sqlite3.Row
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            SELECT id, chemin_fichier, type_fichier, taille_octets
            FROM fichier_oeuvre
            WHERE oeuvre_id = ?
            ORDER BY ordre, id
        """, (oeuvre_id,))
        return [dict(row) for row in curseur.fetchall()]
    finally:
        connexion.close()


def incrementer_vues_oeuvre(oeuvre_id):
    """Incrémente le compteur de vues d'une œuvre."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        curseur.execute("""
            UPDATE oeuvre
            SET vues = vues + 1
            WHERE id = ?
        """, (oeuvre_id,))
        connexion.commit()
    finally:
        connexion.close()


def rechercher_oeuvres(terme_recherche, limit=None):
    """Recherche des œuvres par titre ou description."""
    connexion = ouvrir_base()
    connexion.row_factory = sqlite3.Row
    try:
        curseur = connexion.cursor()
        query = """
            SELECT o.*, u.nom as artiste_nom
            FROM oeuvre o
            JOIN utilisateur u ON o.artiste_id = u.id
            WHERE o.actif = 1
              AND (SANS_ACCENTS(o.titre) LIKE SANS_ACCENTS(?)
                   OR SANS_ACCENTS(o.description) LIKE SANS_ACCENTS(?)
                   OR SANS_ACCENTS(u.nom) LIKE SANS_ACCENTS(?))
            ORDER BY o.date_ajout DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        terme = f"%{terme_recherche}%"
        curseur.execute(query, (terme, terme, terme))
        return [dict(row) for row in curseur.fetchall()]
    finally:
        connexion.close()


def count_oeuvres(type_filtre=None):
    """Compte le nombre total d'œuvres."""
    connexion = ouvrir_base()
    try:
        curseur = connexion.cursor()
        query = "SELECT COUNT(*) FROM oeuvre WHERE actif = 1"
        params = []
        
        if type_filtre:
            query += " AND type = ?"
            params.append(type_filtre)
        
        curseur.execute(query, params)
        return curseur.fetchone()[0]
    finally:
        connexion.close()
