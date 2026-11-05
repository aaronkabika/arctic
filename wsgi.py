"""
Point d'entrée WSGI pour Vercel
"""
from app import app

# Vercel cherche une variable "app" ou "application"
application = app

if __name__ == "__main__":
    app.run()
