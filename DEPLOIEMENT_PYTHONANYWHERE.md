# Guide de Déploiement Arctic sur PythonAnywhere

## 🎯 Avantages de PythonAnywhere

- ✅ **100% Gratuit** (pas de carte bancaire)
- ✅ **Supporte SQLite** nativement
- ✅ **Parfait pour Flask**
- ✅ **Interface bash** pour gérer les fichiers
- ✅ **Simple à configurer**

---

## 🚀 Étapes de Déploiement

### 1. Créer un Compte

1. Allez sur [pythonanywhere.com](https://www.pythonanywhere.com)
2. Cliquez sur "Start running Python online"
3. Créez un compte **Beginner** (gratuit)
4. Confirmez votre email

### 2. Uploader le Code

**Option A : Via Git (Recommandé)**

1. Sur PythonAnywhere, allez dans **"Consoles"** → **"Bash"**
2. Clonez votre repository :
   ```bash
   git clone https://github.com/aaronkabika/arctic.git
   cd arctic
   ```

**Option B : Upload Manuel**

1. Allez dans **"Files"**
2. Créez un dossier `arctic`
3. Uploadez tous vos fichiers

### 3. Installer les Dépendances

Dans la console Bash :

```bash
cd arctic
pip3 install --user -r requirements.txt
```

### 4. Créer une Web App

1. Allez dans l'onglet **"Web"**
2. Cliquez sur **"Add a new web app"**
3. Choisissez **"Manual configuration"**
4. Sélectionnez **Python 3.10**
5. Cliquez sur **"Next"**

### 5. Configurer le WSGI

1. Sur la page Web, cherchez la section **"Code"**
2. Cliquez sur le lien du fichier WSGI (ex: `/var/www/votreusername_pythonanywhere_com_wsgi.py`)
3. **Remplacez tout le contenu** par :

```python
import sys
import os

# Remplacez 'votreusername' par votre username PythonAnywhere
project_home = '/home/votreusername/arctic'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
application.config['DEBUG'] = False
```

4. **Remplacez `votreusername`** par votre nom d'utilisateur PythonAnywhere
5. Cliquez sur **"Save"**

### 6. Configurer les Fichiers Statiques

Sur la page Web, section **"Static files"** :

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/votreusername/arctic/static` |
| `/uploads/` | `/home/votreusername/arctic/uploads` |

(Remplacez `votreusername` par votre username)

### 7. Configurer les Variables d'Environnement

1. Allez dans l'onglet **"Files"**
2. Ouvrez le fichier `.bashrc` (dans votre home)
3. Ajoutez à la fin :

```bash
export ARCTIC_SECRET_KEY="votre_cle_secrete_ici"
export FLASK_ENV="production"
```

4. Sauvegardez

**Pour générer une clé sécurisée**, dans la console Bash :
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 8. Créer la Base de Données

Dans la console Bash :

```bash
cd arctic
python3 -c "from app import creer_base; creer_base()"
```

### 9. Démarrer l'Application

1. Retournez sur l'onglet **"Web"**
2. Cliquez sur le gros bouton vert **"Reload votreusername.pythonanywhere.com"**
3. Attendez 10-20 secondes
4. Cliquez sur le lien de votre site : `http://votreusername.pythonanywhere.com`

---

## ✅ Vérification

Vous devriez voir la page d'accueil Arctic !

---

## 📦 Migrer les Données Existantes

Pour transférer votre base `arctic.db` existante :

1. Sur PythonAnywhere, onglet **"Files"**
2. Naviguez vers `/home/votreusername/arctic/`
3. Cliquez sur **"Upload a file"**
4. Uploadez votre fichier `arctic.db` local

Ou via Bash :

```bash
# Sur votre ordinateur local
# (Uploadez arctic.db via l'interface Files de PythonAnywhere)
```

---

## 🔄 Mises à Jour

Pour mettre à jour votre code :

```bash
cd arctic
git pull origin main
# Puis sur l'onglet Web, cliquez "Reload"
```

---

## ⚠️ Limitations du Plan Gratuit

- **1 web app** seulement
- **512 MB** d'espace disque
- **Custom domain** : Non (seulement votreusername.pythonanywhere.com)
- **HTTPS** : Non sur le plan gratuit
- L'app s'endort après **3 mois sans visite**

---

## 🆘 Problèmes Courants

### Erreur 502 Bad Gateway

- Vérifiez les logs : onglet Web → "Error log"
- Vérifiez que le chemin dans WSGI est correct

### ImportError

- Installez les dépendances : `pip3 install --user -r requirements.txt`
- Rechargez l'app

### Base de données vide

- Exécutez `creer_base()` dans la console Python
- Ou uploadez votre `arctic.db` existant

---

## 📞 Support

- Documentation : [help.pythonanywhere.com](https://help.pythonanywhere.com)
- Forum : [pythonanywhere.com/forums](https://www.pythonanywhere.com/forums/)

---

**PythonAnywhere est parfait pour démarrer avec Arctic !** 🎉
