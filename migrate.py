"""
Script de migration pour Arctic
Migre de l'ancienne structure vers la nouvelle
"""

import sqlite3
import os
import shutil
from datetime import datetime


def backup_database():
    """Crée une sauvegarde de la base de données."""
    if os.path.exists("arctic.db"):
        backup_name = f"arctic_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2("arctic.db", backup_name)
        print(f"✅ Sauvegarde créée : {backup_name}")
        return True
    return False


def upgrade_database():
    """Met à jour le schéma de la base de données."""
    conn = sqlite3.connect("arctic.db")
    cursor = conn.cursor()
    
    try:
        print("\n🔄 Mise à jour du schéma de la base de données...")
        
        # Ajouter les nouvelles colonnes à la table utilisateur
        nouvelles_colonnes_utilisateur = [
            ("date_creation", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("derniere_connexion", "TIMESTAMP"),
            ("actif", "INTEGER DEFAULT 1")
        ]
        
        for colonne, type_sql in nouvelles_colonnes_utilisateur:
            try:
                cursor.execute(f"ALTER TABLE utilisateur ADD COLUMN {colonne} {type_sql}")
                print(f"  ✅ Colonne '{colonne}' ajoutée à utilisateur")
            except sqlite3.OperationalError:
                print(f"  ℹ️  Colonne '{colonne}' existe déjà")
        
        # Ajouter les nouvelles colonnes à la table oeuvre
        nouvelles_colonnes_oeuvre = [
            ("date_ajout", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("date_modification", "TIMESTAMP"),
            ("vues", "INTEGER DEFAULT 0"),
            ("actif", "INTEGER DEFAULT 1")
        ]
        
        for colonne, type_sql in nouvelles_colonnes_oeuvre:
            try:
                cursor.execute(f"ALTER TABLE oeuvre ADD COLUMN {colonne} {type_sql}")
                print(f"  ✅ Colonne '{colonne}' ajoutée à oeuvre")
            except sqlite3.OperationalError:
                print(f"  ℹ️  Colonne '{colonne}' existe déjà")
        
        # Ajouter les nouvelles colonnes à la table fichier_oeuvre
        nouvelles_colonnes_fichier = [
            ("taille_octets", "INTEGER"),
            ("ordre", "INTEGER DEFAULT 0"),
            ("date_ajout", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for colonne, type_sql in nouvelles_colonnes_fichier:
            try:
                cursor.execute(f"ALTER TABLE fichier_oeuvre ADD COLUMN {colonne} {type_sql}")
                print(f"  ✅ Colonne '{colonne}' ajoutée à fichier_oeuvre")
            except sqlite3.OperationalError:
                print(f"  ℹ️  Colonne '{colonne}' existe déjà")
        
        # Créer la table favori
        cursor.execute("""
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
        print("  ✅ Table 'favori' créée")
        
        # Créer la table commentaire
        cursor.execute("""
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
        print("  ✅ Table 'commentaire' créée")
        
        # Créer les indexes
        indexes = [
            ("idx_utilisateur_email", "utilisateur", "email"),
            ("idx_oeuvre_artiste", "oeuvre", "artiste_id"),
            ("idx_oeuvre_type", "oeuvre", "type"),
            ("idx_fichier_oeuvre", "fichier_oeuvre", "oeuvre_id")
        ]
        
        for nom_index, table, colonne in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {nom_index} ON {table}({colonne})")
                print(f"  ✅ Index '{nom_index}' créé")
            except sqlite3.OperationalError:
                print(f"  ℹ️  Index '{nom_index}' existe déjà")
        
        # Activer les optimisations SQLite
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("\n✅ Mise à jour de la base de données terminée avec succès!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erreur lors de la mise à jour : {e}")
        return False
    finally:
        conn.close()
    
    return True


def verify_migration():
    """Vérifie que la migration s'est bien déroulée."""
    conn = sqlite3.connect("arctic.db")
    cursor = conn.cursor()
    
    print("\n🔍 Vérification de la migration...")
    
    try:
        # Vérifier les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        tables_requises = ["utilisateur", "oeuvre", "fichier_oeuvre", "favori", "commentaire"]
        for table in tables_requises:
            if table in tables:
                print(f"  ✅ Table '{table}' présente")
            else:
                print(f"  ❌ Table '{table}' manquante")
        
        # Compter les enregistrements
        cursor.execute("SELECT COUNT(*) FROM utilisateur")
        nb_utilisateurs = cursor.fetchone()[0]
        print(f"\n📊 Statistiques :")
        print(f"  - {nb_utilisateurs} utilisateur(s)")
        
        cursor.execute("SELECT COUNT(*) FROM oeuvre")
        nb_oeuvres = cursor.fetchone()[0]
        print(f"  - {nb_oeuvres} œuvre(s)")
        
        cursor.execute("SELECT COUNT(*) FROM fichier_oeuvre")
        nb_fichiers = cursor.fetchone()[0]
        print(f"  - {nb_fichiers} fichier(s)")
        
        print("\n✅ Vérification terminée!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification : {e}")
    finally:
        conn.close()


def main():
    """Fonction principale de migration."""
    print("="*60)
    print("  MIGRATION ARCTIC - Vers la version professionnelle")
    print("="*60)
    
    # Étape 1 : Sauvegarde
    print("\n📦 Étape 1 : Sauvegarde de la base de données")
    if backup_database():
        print("✅ Sauvegarde réussie")
    else:
        print("⚠️  Aucune base de données à sauvegarder")
    
    # Étape 2 : Migration du schéma
    print("\n🔄 Étape 2 : Mise à jour du schéma")
    if upgrade_database():
        print("✅ Schéma mis à jour")
    else:
        print("❌ Erreur lors de la mise à jour")
        return
    
    # Étape 3 : Vérification
    print("\n🔍 Étape 3 : Vérification")
    verify_migration()
    
    # Instructions finales
    print("\n" + "="*60)
    print("  MIGRATION TERMINÉE AVEC SUCCÈS!")
    print("="*60)
    print("\n📋 Prochaines étapes :")
    print("  1. Vérifier que tous les fichiers sont présents")
    print("  2. Installer les dépendances : pip install -r requirements.txt")
    print("  3. Configurer .env avec votre clé secrète")
    print("  4. Tester l'application : python app.py")
    print("\n🎉 Bienvenue dans Arctic v2.0 !")
    print("="*60)


if __name__ == "__main__":
    main()
