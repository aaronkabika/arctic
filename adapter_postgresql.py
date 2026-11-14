"""
Script pour adapter app.py de SQLite vers PostgreSQL
"""
import re

print("🔧 Adaptation de app.py pour PostgreSQL...")

# Lire le fichier app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Supprimer l'import sqlite3
content = re.sub(r'import sqlite3\n', '', content)

# 2. Supprimer les anciennes fonctions ouvrir_base() et get_db_cursor() et creer_base()
# Trouver et supprimer la fonction ouvrir_base
pattern_ouvrir = r'def ouvrir_base\(\):.*?(?=\ndef\s|\n@app\.|\nclass\s|\Z)'
content = re.sub(pattern_ouvrir, '', content, flags=re.DOTALL)

# Supprimer la fonction get_db_cursor (l'ancienne version)
pattern_cursor = r'def get_db_cursor\(\):.*?finally:\s+conn\.close\(\)\s*\n'
content = re.sub(pattern_cursor, '', content, flags=re.DOTALL)

# Supprimer la fonction creer_base
pattern_creer = r'def creer_base\(\):.*?(?=\ndef\s|\n@app\.|\nclass\s|\Z)'
content = re.sub(pattern_creer, '', content, flags=re.DOTALL)

# 3. Remplacer tous les usages de connexion SQLite par database.py
# Remplacer les patterns courants

# Pattern: connexion = ouvrir_base()
content = re.sub(
    r'connexion(?:_db)?\s*=\s*ouvrir_base\(\)',
    'with get_db_connection() as connexion',
    content
)

# Pattern: curseur = connexion.cursor()
content = re.sub(
    r'curseur(?:_db)?\s*=\s*connexion\.cursor\(\)',
    'curseur = get_db_cursor(connexion)',
    content
)

# 4. Ajouter un commentaire pour marquer l'adaptation
header_comment = '''
# ==============================
# NOTE: Ce fichier a été adapté pour PostgreSQL
# Les fonctions de base de données sont dans database.py
# ==============================
'''

# Insérer après les imports
import_end = content.find('# ==============================\n# CONFIGURATION DE L\'APPLICATION')
if import_end != -1:
    content = content[:import_end] + header_comment + content[import_end:]

# 5. Sauvegarder
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Adaptation terminée!")
print("\n📝 Modifications effectuées:")
print("  - Supprimé import sqlite3")
print("  - Supprimé anciennes fonctions SQL")
print("  - Remplacé par database.py")
print("\n⚠️  IMPORTANT: Vérifiez manuellement les requêtes SQL dans app.py")
print("   Certaines peuvent nécessiter des ajustements pour PostgreSQL")
