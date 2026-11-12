"""
Module de gestion de la base de données PostgreSQL pour Arctic
"""
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager


def get_database_url():
    """Récupère l'URL de la base de données depuis les variables d'environnement."""
    return os.environ.get('DATABASE_URL')


@contextmanager
def get_db_connection():
    """
    Gestionnaire de contexte pour les connexions à la base de données.
    Utilise PostgreSQL en production (Vercel) ou SQLite en développement.
    """
    database_url = get_database_url()
    
    if database_url and database_url.startswith('postgresql'):
        # PostgreSQL (Production sur Vercel)
        conn = psycopg2.connect(database_url)
        conn.set_session(autocommit=False)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        # SQLite (Développement local)
        import sqlite3
        conn = sqlite3.connect('arctic.db')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_db_cursor(conn):
    """Retourne un curseur adapté au type de base de données."""
    database_url = get_database_url()
    
    if database_url and database_url.startswith('postgresql'):
        # PostgreSQL - utiliser RealDictCursor pour avoir des dictionnaires
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        # SQLite - déjà configuré avec row_factory
        return conn.cursor()


def init_database():
    """
    Initialise la base de données avec les tables nécessaires.
    Compatible PostgreSQL et SQLite.
    """
    database_url = get_database_url()
    is_postgres = database_url and database_url.startswith('postgresql')
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        # Adaptations pour PostgreSQL vs SQLite
        if is_postgres:
            serial_type = "SERIAL"
            text_type = "VARCHAR(255)"
            datetime_type = "TIMESTAMP"
            check_constraint = ""
        else:
            serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            text_type = "TEXT"
            datetime_type = "TEXT"
            check_constraint = ""
        
        # Table utilisateur
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS utilisateur (
                id {serial_type if not is_postgres else 'SERIAL PRIMARY KEY'},
                nom {text_type} NOT NULL,
                date_naissance DATE NOT NULL,
                sexe VARCHAR(10) NOT NULL,
                email {text_type} NOT NULL UNIQUE,
                telephone VARCHAR(20) NOT NULL,
                mot_de_passe {text_type} NOT NULL,
                role VARCHAR(20) NOT NULL CHECK(role IN ('artiste', 'visiteur')),
                date_creation {datetime_type} DEFAULT {'CURRENT_TIMESTAMP' if is_postgres else 'CURRENT_TIMESTAMP'},
                derniere_connexion {datetime_type},
                actif INTEGER DEFAULT 1
                {',' if not is_postgres else ''}
                {'' if is_postgres else 'PRIMARY KEY (id)' if serial_type == 'INTEGER PRIMARY KEY AUTOINCREMENT' else ''}
            )
        """)
        
        # Index pour utilisateur
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_utilisateur_email ON utilisateur(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_utilisateur_role ON utilisateur(role)
        """)
        
        # Table oeuvre
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS oeuvre (
                id {serial_type if not is_postgres else 'SERIAL PRIMARY KEY'},
                artiste_id INTEGER NOT NULL,
                titre {text_type} NOT NULL,
                type VARCHAR(50) NOT NULL CHECK(type IN ('musique', 'peinture', 'litterature', 'sculpture')),
                description TEXT,
                date_creation DATE NOT NULL,
                prix {'DECIMAL(10, 2)' if is_postgres else 'REAL'} NOT NULL CHECK(prix > 0),
                date_ajout {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                date_modification {datetime_type},
                vues INTEGER DEFAULT 0,
                actif INTEGER DEFAULT 1,
                FOREIGN KEY (artiste_id) REFERENCES utilisateur(id) ON DELETE CASCADE
                {',' if not is_postgres else ''}
                {'' if is_postgres else 'PRIMARY KEY (id)' if serial_type == 'INTEGER PRIMARY KEY AUTOINCREMENT' else ''}
            )
        """)
        
        # Index pour oeuvre
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oeuvre_artiste ON oeuvre(artiste_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oeuvre_type ON oeuvre(type)
        """)
        
        # Table fichier_oeuvre
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS fichier_oeuvre (
                id {serial_type if not is_postgres else 'SERIAL PRIMARY KEY'},
                oeuvre_id INTEGER NOT NULL,
                chemin_fichier VARCHAR(500) NOT NULL,
                type_fichier VARCHAR(20) NOT NULL CHECK(type_fichier IN ('image', 'audio', 'document')),
                taille_octets BIGINT,
                ordre INTEGER DEFAULT 0,
                date_ajout {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE
                {',' if not is_postgres else ''}
                {'' if is_postgres else 'PRIMARY KEY (id)' if serial_type == 'INTEGER PRIMARY KEY AUTOINCREMENT' else ''}
            )
        """)
        
        # Index pour fichier_oeuvre
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fichier_oeuvre ON fichier_oeuvre(oeuvre_id)
        """)
        
        # Table favori
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS favori (
                id {serial_type if not is_postgres else 'SERIAL PRIMARY KEY'},
                utilisateur_id INTEGER NOT NULL,
                oeuvre_id INTEGER NOT NULL,
                date_ajout {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE,
                FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE,
                UNIQUE(utilisateur_id, oeuvre_id)
                {',' if not is_postgres else ''}
                {'' if is_postgres else 'PRIMARY KEY (id)' if serial_type == 'INTEGER PRIMARY KEY AUTOINCREMENT' else ''}
            )
        """)
        
        # Table commentaire
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS commentaire (
                id {serial_type if not is_postgres else 'SERIAL PRIMARY KEY'},
                oeuvre_id INTEGER NOT NULL,
                utilisateur_id INTEGER NOT NULL,
                contenu TEXT NOT NULL,
                date_creation {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                date_modification {datetime_type},
                actif INTEGER DEFAULT 1,
                FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE
                {',' if not is_postgres else ''}
                {'' if is_postgres else 'PRIMARY KEY (id)' if serial_type == 'INTEGER PRIMARY KEY AUTOINCREMENT' else ''}
            )
        """)
        
        conn.commit()
        print("✅ Base de données initialisée avec succès")


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Exécute une requête SQL et retourne les résultats.
    
    Args:
        query: La requête SQL à exécuter
        params: Les paramètres de la requête (tuple ou dict)
        fetch_one: Si True, retourne une seule ligne
        fetch_all: Si True, retourne toutes les lignes
    
    Returns:
        - Si fetch_one: un dictionnaire ou None
        - Si fetch_all: une liste de dictionnaires
        - Sinon: le cursor.lastrowid (pour les INSERT)
    """
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else None
        elif fetch_all:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            # Pour les INSERT, retourner l'ID
            try:
                return cursor.lastrowid
            except:
                return None
