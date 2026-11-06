"""
Test simple de connexion à Neon PostgreSQL
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"URL utilisée : {DATABASE_URL[:50]}...")
print("\n🔄 Test de connexion à PostgreSQL...")

# Essai 1: Connexion avec paramètres explicites
try:
    print("\n📌 Essai 1: Connexion basique avec URL complète...")
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Connexion réussie !")
    conn.close()
    
except Exception as e:
    print(f"❌ Essai 1 échoué : {e}")

# Essai 2: Sans sslmode dans l'URL, ajouté en paramètre
try:
    print("\n📌 Essai 2: Connexion avec SSL en paramètre...")
    url_sans_ssl = DATABASE_URL.split('?')[0]
    conn = psycopg2.connect(url_sans_ssl, sslmode='require')
    print("✅ Connexion réussie !")
    conn.close()
    
except Exception as e:
    print(f"❌ Essai 2 échoué : {e}")

# Essai 3: Avec timeout plus long
try:
    print("\n📌 Essai 3: Connexion avec timeout étendu...")
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
    print("✅ Connexion réussie !")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ Version PostgreSQL : {version[0][:50]}...")
    
    cursor.close()
    conn.close()
    print("\n🎉 Tout fonctionne !")
    
except Exception as e:
    print(f"❌ Essai 3 échoué : {e}")

print("\n🔍 Si tous les essais ont échoué, il peut y avoir:")
print("   - Un problème de firewall/réseau")
print("   - La base Neon est en veille (free tier)")
print("   - Un problème de configuration Neon")
