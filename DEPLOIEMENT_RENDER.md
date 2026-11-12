# Guide de Déploiement Arctic sur Render.com

## 🎯 Avantages de Render.com

- ✅ **Supporte SQLite nativement** (pas de migration PostgreSQL nécessaire)
- ✅ **Gratuit** (plan Free avec 750h/mois)
- ✅ **Stockage persistant** pour la base de données
- ✅ **Simple et rapide** à configurer
- ✅ **Support Python/Flask** natif

---

## 🚀 Étapes de Déploiement

### 1. Créer un Compte Render

1. Allez sur [render.com](https://render.com)
2. Cliquez sur **"Get Started"**
3. Connectez-vous avec **GitHub**
4. Autorisez Render à accéder à vos repositories

### 2. Créer un Nouveau Web Service

1. Sur le dashboard Render, cliquez sur **"New +"** → **"Web Service"**
2. Cherchez et sélectionnez le repository **"arctic"**
3. Cliquez sur **"Connect"**

### 3. Configurer le Service

**Paramètres à remplir** :

| Champ | Valeur |
|-------|--------|
| **Name** | `arctic` |
| **Region** | `Frankfurt (EU Central)` ou proche |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` |

### 4. Variables d'Environnement

Cliquez sur **"Advanced"** puis ajoutez ces variables :

| Key | Value |
|-----|-------|
| `ARCTIC_SECRET_KEY` | [Générer avec Python] |
| `FLASK_ENV` | `production` |
| `PYTHON_VERSION` | `3.11.0` |

**Pour générer ARCTIC_SECRET_KEY** :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Ajouter un Disque Persistant (Important!)

Pour que la base SQLite et les uploads persistent :

1. Scrollez vers le bas
2. Section **"Disks"**
3. Cliquez sur **"Add Disk"**
4. Configurez :
   - **Name** : `arctic-data`
   - **Mount Path** : `/opt/render/project/src/data`
   - **Size** : `1 GB` (gratuit)
5. Cliquez sur **"Save"**

### 6. Déployer

1. Cliquez sur **"Create Web Service"**
2. Render va :
   - Cloner votre code depuis GitHub
   - Installer les dépendances
   - Lancer l'application
3. Attendez 3-5 minutes

### 7. Accéder à l'Application

Une fois le déploiement terminé :
- Render vous donne une URL : `https://arctic-xxxx.onrender.com`
- Cliquez sur l'URL pour voir votre application Arctic !

---

## ⚠️ Notes Importantes

### Base de Données SQLite

La base `arctic.db` sera créée au premier lancement. Pour la migrer :

1. **Option A** : Utiliser le dashboard Render pour uploader `arctic.db`
2. **Option B** : Créer les données directement via l'interface web

### Uploads

Les fichiers uploadés (images, audio, PDF) seront stockés dans le disque persistant.

### Auto-Sleep (Plan Free)

Le plan gratuit met l'application en veille après 15 minutes d'inactivité. Le réveil prend ~30 secondes.

---

## 🔄 Mises à Jour

Render redéploie automatiquement à chaque `git push` sur la branche `main`.

```bash
git add .
git commit -m "Mise à jour"
git push origin main
```

---

## 🆘 Problèmes Courants

### Erreur : "Application failed to respond"

- Vérifiez que `gunicorn` est dans `requirements.txt`
- Vérifiez le Start Command : `gunicorn app:app`

### Base de données vide

- La base sera créée au premier accès
- Ou uploadez `arctic.db` via le dashboard Render

### Fichiers disparus après redéploiement

- Assurez-vous d'avoir configuré le disque persistant
- Vérifiez le Mount Path

---

## 📊 Comparaison Vercel vs Render

| Fonctionnalité | Vercel | Render |
|----------------|--------|--------|
| SQLite | ❌ Non supporté | ✅ Supporté |
| PostgreSQL | ✅ Recommandé | ✅ Supporté |
| Stockage persistant | ❌ Non (serverless) | ✅ Oui |
| Plan gratuit | ✅ Oui | ✅ 750h/mois |
| Auto-déploiement | ✅ Oui | ✅ Oui |

---

**Render.com est parfait pour votre projet Arctic avec SQLite !** 🎉
