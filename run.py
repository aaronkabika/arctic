"""
Script de lancement pour Arctic
Lance l'application en mode développement ou production
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv n'est pas installé. Les variables .env ne seront pas chargées.")
    print("   Installez-le avec: pip install python-dotenv")

# Importer l'application
try:
    from app_new import create_app
except ImportError as e:
    print("❌ Erreur : Impossible d'importer l'application.")
    print(f"   Détails : {e}")
    print("📝 Assurez-vous que tous les fichiers sont présents :")
    print("   - app_new.py")
    print("   - config.py")
    print("   - models.py")
    print("   - utils.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur lors de l'import : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def main():
    """Lance l'application."""
    # Déterminer l'environnement
    env = os.getenv("FLASK_ENV", "development")
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    print("="*60)
    print("  🎨 ARCTIC - Plateforme d'Art et de Découverte")
    print("="*60)
    print(f"\n📌 Environnement : {env}")
    print(f"🔧 Mode debug : {debug}")
    
    # Vérifier la clé secrète
    secret_key = os.getenv("ARCTIC_SECRET_KEY")
    if not secret_key or secret_key == "your_very_secret_key_here_change_in_production":
        print("\n⚠️  ATTENTION : Clé secrète par défaut détectée!")
        print("📝 Pour la production, définissez ARCTIC_SECRET_KEY dans .env")
    
    # Créer l'application
    try:
        app = create_app(env)
        print("\n✅ Application initialisée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation : {e}")
        sys.exit(1)
    
    # Afficher les informations de connexion
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    
    print(f"\n🚀 Lancement du serveur...")
    print(f"📡 Adresse : http://localhost:{port}")
    print(f"🌐 Réseau : http://{host}:{port}")
    print("\n💡 Appuyez sur Ctrl+C pour arrêter le serveur")
    print("="*60 + "\n")
    
    # Lancer le serveur
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n\n👋 Serveur arrêté. À bientôt!")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
