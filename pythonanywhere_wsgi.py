"""
WSGI configuration pour PythonAnywhere
À copier dans /var/www/votreusername_pythonanywhere_com_wsgi.py
"""
import sys
import os

# Ajouter le chemin de votre projet
project_home = '/home/votreusername/arctic'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Importer l'application Flask
from app import app as application

# Configuration pour PythonAnywhere
application.config['DEBUG'] = False
