"""
Point d'entrée Vercel pour Flask Arctic
"""
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialiser la base de données au démarrage
from database import init_database

try:
    init_database()
    print("✅ Base de données initialisée")
except Exception as e:
    print(f"⚠️ Erreur init DB : {e}")

# Importer l'application Flask principale
from app import app
