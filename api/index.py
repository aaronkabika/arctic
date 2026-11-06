"""
Point d'entrée Vercel pour Flask - Version Test
"""
from flask import Flask

# Créer une application Flask minimale pour tester
app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arctic - Déploiement Réussi!</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 48px; margin-bottom: 20px; }
            p { font-size: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Arctic est Déployé sur Vercel!</h1>
            <p>Le déploiement a réussi!</p>
            <p>Prochaine étape : Migration des données PostgreSQL</p>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    import os
    return {
        "status": "ok",
        "database_url": "configured" if os.getenv("DATABASE_URL") else "missing",
        "vercel": os.getenv("VERCEL", "not set")
    }
