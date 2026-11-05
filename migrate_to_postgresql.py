"""
Script de migration SQLite vers PostgreSQL pour Arctic
Ce script transfère toutes les données de arctic.db vers PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
SQLITE_DB = "arctic.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("❌ Erreur : DATABASE_URL n'est pas définie dans .env")
    print("Ajoutez votre URL PostgreSQL dans .env")
    print("Exemple : DATABASE_URL=postgresql://user:password@host:port/database")
    exit(1)

print("🚀 Démarrage de la migration SQLite → PostgreSQL")
print(f"📂 Base source : {SQLITE_DB}")
print(f"🗄️  Base cible : PostgreSQL")

# Connexion SQLite
try:
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    print("✅ Connexion SQLite établie")
except Exception as e:
    print(f"❌ Erreur connexion SQLite : {e}")
    exit(1)

# Connexion PostgreSQL
try:
    postgres_conn = psycopg2.connect(POSTGRES_URL)
    postgres_cursor = postgres_conn.cursor()
    print("✅ Connexion PostgreSQL établie")
except Exception as e:
    print(f"❌ Erreur connexion PostgreSQL : {e}")
    print("Vérifiez que l'URL PostgreSQL est correcte")
    sqlite_conn.close()
    exit(1)

# ==============================
# CRÉATION DES TABLES POSTGRESQL
# ==============================

print("\n📋 Création des tables PostgreSQL...")

try:
    # Table utilisateur
    postgres_cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateur (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(255) NOT NULL,
            date_naissance DATE NOT NULL,
            sexe VARCHAR(10) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            telephone VARCHAR(20) NOT NULL,
            mot_de_passe VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK(role IN ('artiste', 'visiteur')),
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            derniere_connexion TIMESTAMP,
            actif INTEGER DEFAULT 1,
            CONSTRAINT email_format CHECK(email LIKE '%@%.%')
        )
    """)
    
    # Index utilisateur
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_utilisateur_email ON utilisateur(email)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_utilisateur_role ON utilisateur(role)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_utilisateur_actif ON utilisateur(actif)
    """)
    
    # Table oeuvre
    postgres_cursor.execute("""
        CREATE TABLE IF NOT EXISTS oeuvre (
            id SERIAL PRIMARY KEY,
            artiste_id INTEGER NOT NULL,
            titre VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL CHECK(type IN ('musique', 'peinture', 'litterature', 'sculpture')),
            description TEXT,
            date_creation DATE NOT NULL,
            prix DECIMAL(10, 2) NOT NULL CHECK(prix > 0),
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP,
            vues INTEGER DEFAULT 0,
            actif INTEGER DEFAULT 1,
            FOREIGN KEY (artiste_id) REFERENCES utilisateur(id) ON DELETE CASCADE
        )
    """)
    
    # Index oeuvre
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_oeuvre_artiste ON oeuvre(artiste_id)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_oeuvre_type ON oeuvre(type)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_oeuvre_actif ON oeuvre(actif)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_oeuvre_artiste_actif ON oeuvre(artiste_id, actif)
    """)
    
    # Table fichier_oeuvre
    postgres_cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichier_oeuvre (
            id SERIAL PRIMARY KEY,
            oeuvre_id INTEGER NOT NULL,
            chemin_fichier VARCHAR(500) NOT NULL,
            type_fichier VARCHAR(20) NOT NULL CHECK(type_fichier IN ('image', 'audio', 'document')),
            taille_octets BIGINT,
            ordre INTEGER DEFAULT 0,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE
        )
    """)
    
    # Index fichier_oeuvre
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fichier_oeuvre ON fichier_oeuvre(oeuvre_id)
    """)
    
    # Table favori
    postgres_cursor.execute("""
        CREATE TABLE IF NOT EXISTS favori (
            id SERIAL PRIMARY KEY,
            utilisateur_id INTEGER NOT NULL,
            oeuvre_id INTEGER NOT NULL,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) ON DELETE CASCADE,
            FOREIGN KEY (oeuvre_id) REFERENCES oeuvre(id) ON DELETE CASCADE,
            UNIQUE(utilisateur_id, oeuvre_id)
        )
    """)
    
    # Index favori
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_favori_utilisateur ON favori(utilisateur_id)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_favori_oeuvre ON favori(oeuvre_id)
    """)
    
    # Table commentaire
    postgres_cursor.execute("""
        CREATE TABLE IF NOT EXISTS commentaire (
            id SERIAL PRIMARY KEY,
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
    
    # Index commentaire
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commentaire_oeuvre ON commentaire(oeuvre_id)
    """)
    postgres_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commentaire_utilisateur ON commentaire(utilisateur_id)
    """)
    
    postgres_conn.commit()
    print("✅ Tables PostgreSQL créées avec succès")
    
except Exception as e:
    print(f"❌ Erreur création tables : {e}")
    postgres_conn.rollback()
    sqlite_conn.close()
    postgres_conn.close()
    exit(1)

# ==============================
# MIGRATION DES DONNÉES
# ==============================

print("\n📦 Migration des données...")

# Vider les tables PostgreSQL (pour éviter les doublons lors de tests)
try:
    postgres_cursor.execute("TRUNCATE TABLE fichier_oeuvre, favori, commentaire, oeuvre, utilisateur RESTART IDENTITY CASCADE")
    postgres_conn.commit()
    print("🗑️  Tables PostgreSQL vidées")
except Exception as e:
    print(f"⚠️  Avertissement vidage tables : {e}")

# 1. MIGRATION UTILISATEURS
print("\n👥 Migration des utilisateurs...")
sqlite_cursor.execute("SELECT * FROM utilisateur")
utilisateurs = sqlite_cursor.fetchall()

if utilisateurs:
    utilisateurs_data = [
        (
            u['nom'], u['date_naissance'], u['sexe'], u['email'],
            u['telephone'], u['mot_de_passe'], u['role'],
            u.get('date_creation'), u.get('derniere_connexion'), u.get('actif', 1)
        )
        for u in utilisateurs
    ]
    
    execute_values(
        postgres_cursor,
        """
        INSERT INTO utilisateur 
        (nom, date_naissance, sexe, email, telephone, mot_de_passe, role, date_creation, derniere_connexion, actif)
        VALUES %s
        """,
        utilisateurs_data
    )
    postgres_conn.commit()
    print(f"✅ {len(utilisateurs)} utilisateurs migrés")
else:
    print("⚠️  Aucun utilisateur à migrer")

# Créer mapping ID SQLite → PostgreSQL pour utilisateurs
sqlite_cursor.execute("SELECT id, email FROM utilisateur")
utilisateur_mapping = {}
for u in sqlite_cursor.fetchall():
    postgres_cursor.execute("SELECT id FROM utilisateur WHERE email = %s", (u['email'],))
    result = postgres_cursor.fetchone()
    if result:
        utilisateur_mapping[u['id']] = result[0]

# 2. MIGRATION OEUVRES
print("\n🎨 Migration des œuvres...")
sqlite_cursor.execute("SELECT * FROM oeuvre")
oeuvres = sqlite_cursor.fetchall()

if oeuvres:
    oeuvres_data = [
        (
            utilisateur_mapping.get(o['artiste_id'], o['artiste_id']),
            o['titre'], o['type'], o['description'], o['date_creation'],
            o['prix'], o.get('date_ajout'), o.get('date_modification'),
            o.get('vues', 0), o.get('actif', 1)
        )
        for o in oeuvres
    ]
    
    execute_values(
        postgres_cursor,
        """
        INSERT INTO oeuvre 
        (artiste_id, titre, type, description, date_creation, prix, date_ajout, date_modification, vues, actif)
        VALUES %s
        """,
        oeuvres_data
    )
    postgres_conn.commit()
    print(f"✅ {len(oeuvres)} œuvres migrées")
else:
    print("⚠️  Aucune œuvre à migrer")

# Créer mapping ID SQLite → PostgreSQL pour oeuvres
sqlite_cursor.execute("SELECT id, titre, artiste_id FROM oeuvre")
oeuvre_mapping = {}
for o in sqlite_cursor.fetchall():
    postgres_cursor.execute(
        "SELECT id FROM oeuvre WHERE titre = %s AND artiste_id = %s",
        (o['titre'], utilisateur_mapping.get(o['artiste_id'], o['artiste_id']))
    )
    result = postgres_cursor.fetchone()
    if result:
        oeuvre_mapping[o['id']] = result[0]

# 3. MIGRATION FICHIERS OEUVRE
print("\n📁 Migration des fichiers d'œuvres...")
sqlite_cursor.execute("SELECT * FROM fichier_oeuvre")
fichiers = sqlite_cursor.fetchall()

if fichiers:
    fichiers_data = [
        (
            oeuvre_mapping.get(f['oeuvre_id'], f['oeuvre_id']),
            f['chemin_fichier'], f['type_fichier'],
            f.get('taille_octets'), f.get('ordre', 0), f.get('date_ajout')
        )
        for f in fichiers
    ]
    
    execute_values(
        postgres_cursor,
        """
        INSERT INTO fichier_oeuvre 
        (oeuvre_id, chemin_fichier, type_fichier, taille_octets, ordre, date_ajout)
        VALUES %s
        """,
        fichiers_data
    )
    postgres_conn.commit()
    print(f"✅ {len(fichiers)} fichiers migrés")
else:
    print("⚠️  Aucun fichier à migrer")

# 4. MIGRATION FAVORIS (si la table existe)
print("\n⭐ Migration des favoris...")
try:
    sqlite_cursor.execute("SELECT * FROM favori")
    favoris = sqlite_cursor.fetchall()
    
    if favoris:
        favoris_data = [
            (
                utilisateur_mapping.get(f['utilisateur_id'], f['utilisateur_id']),
                oeuvre_mapping.get(f['oeuvre_id'], f['oeuvre_id']),
                f.get('date_ajout')
            )
            for f in favoris
        ]
        
        execute_values(
            postgres_cursor,
            """
            INSERT INTO favori 
            (utilisateur_id, oeuvre_id, date_ajout)
            VALUES %s
            """,
            favoris_data
        )
        postgres_conn.commit()
        print(f"✅ {len(favoris)} favoris migrés")
    else:
        print("⚠️  Aucun favori à migrer")
except sqlite3.OperationalError:
    print("⚠️  Table favori non présente dans SQLite")

# 5. MIGRATION COMMENTAIRES (si la table existe)
print("\n💬 Migration des commentaires...")
try:
    sqlite_cursor.execute("SELECT * FROM commentaire")
    commentaires = sqlite_cursor.fetchall()
    
    if commentaires:
        commentaires_data = [
            (
                oeuvre_mapping.get(c['oeuvre_id'], c['oeuvre_id']),
                utilisateur_mapping.get(c['utilisateur_id'], c['utilisateur_id']),
                c['contenu'], c.get('date_creation'),
                c.get('date_modification'), c.get('actif', 1)
            )
            for c in commentaires
        ]
        
        execute_values(
            postgres_cursor,
            """
            INSERT INTO commentaire 
            (oeuvre_id, utilisateur_id, contenu, date_creation, date_modification, actif)
            VALUES %s
            """,
            commentaires_data
        )
        postgres_conn.commit()
        print(f"✅ {len(commentaires)} commentaires migrés")
    else:
        print("⚠️  Aucun commentaire à migrer")
except sqlite3.OperationalError:
    print("⚠️  Table commentaire non présente dans SQLite")

# ==============================
# VÉRIFICATION FINALE
# ==============================

print("\n🔍 Vérification de la migration...")

# Compter les lignes dans chaque table
tables = ['utilisateur', 'oeuvre', 'fichier_oeuvre', 'favori', 'commentaire']

print("\n📊 Résumé de la migration :")
print("-" * 60)

for table in tables:
    try:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
    except sqlite3.OperationalError:
        sqlite_count = 0
    
    postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    postgres_count = postgres_cursor.fetchone()[0]
    
    status = "✅" if sqlite_count == postgres_count else "⚠️"
    print(f"{status} {table:20s} : SQLite {sqlite_count:3d} → PostgreSQL {postgres_count:3d}")

print("-" * 60)

# Fermer les connexions
sqlite_conn.close()
postgres_conn.close()

print("\n✅ Migration terminée avec succès !")
print("\n📝 Prochaines étapes :")
print("1. Vérifiez les données dans votre interface PostgreSQL (Neon/Supabase)")
print("2. Configurez DATABASE_URL dans Vercel")
print("3. Déployez l'application")
print("\n🎉 Votre application Arctic est prête pour Vercel !")
