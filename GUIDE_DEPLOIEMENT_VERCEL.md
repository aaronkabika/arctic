# Guide de Déploiement Arctic sur Vercel

## 📋 Prérequis

1. **Compte GitHub** - Pour héberger le code
2. **Compte Vercel** - Gratuit sur [vercel.com](https://vercel.com)
3. **Base PostgreSQL** - Choisir un fournisseur :
   - ✅ **Neon** (recommandé) - [neon.tech](https://neon.tech) - Gratuit, facile, rapide
   - ✅ **Supabase** - [supabase.com](https://supabase.com) - Gratuit avec interface
   - ✅ **Railway** - [railway.app](https://railway.app) - Gratuit avec limites

---

## 🚀 Étape 1 : Créer la base de données PostgreSQL

### Option A : Neon (Recommandé)

1. Créer un compte sur [neon.tech](https://neon.tech)
2. Créer un nouveau projet "Arctic"
3. Copier l'URL de connexion (format : `postgresql://user:password@host/dbname`)
4. Garder cette URL pour l'étape 3

### Option B : Supabase

1. Créer un compte sur [supabase.com](https://supabase.com)
2. Créer un nouveau projet "Arctic"
3. Aller dans Settings > Database
4. Copier la "Connection string" (mode Session ou Transaction)
5. Garder cette URL pour l'étape 3

---

## 🗂️ Étape 2 : Préparer le Repository GitHub

### A. Initialiser Git (si pas déjà fait)

```powershell
git init
git add .
git commit -m "Initial commit - Arctic app ready for Vercel"
```

### B. Créer un Repository sur GitHub

1. Aller sur [github.com](https://github.com) et se connecter
2. Cliquer sur "New repository"
3. Nom : `arctic-art-platform`
4. Visibilité : **Private** (recommandé)
5. NE PAS initialiser avec README (déjà fait localement)
6. Cliquer sur "Create repository"

### C. Pousser le code vers GitHub

```powershell
git remote add origin https://github.com/VOTRE_USERNAME/arctic-art-platform.git
git branch -M main
git push -u origin main
```

---

## ☁️ Étape 3 : Déployer sur Vercel

### A. Connecter GitHub à Vercel

1. Aller sur [vercel.com](https://vercel.com)
2. Se connecter avec GitHub
3. Autoriser Vercel à accéder à vos repositories
4. Cliquer sur "Add New Project"
5. Sélectionner le repository `arctic-art-platform`

### B. Configurer les Variables d'Environnement

Dans la page de configuration Vercel, ajouter ces variables :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `ARCTIC_SECRET_KEY` | `[générer clé aléatoire]` | Clé secrète Flask (64 caractères) |
| `DATABASE_URL` | `postgresql://...` | URL PostgreSQL (Neon/Supabase) |
| `FLASK_ENV` | `production` | Environment Flask |
| `FLASK_DEBUG` | `False` | Mode debug désactivé |

**Pour générer une clé secrète sécurisée :**

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### C. Déployer

1. Cliquer sur "Deploy"
2. Attendre la fin du build (2-3 minutes)
3. Vercel vous donnera une URL : `https://arctic-art-platform.vercel.app`

---

## 🗄️ Étape 4 : Migrer les Données SQLite → PostgreSQL

### A. Installer psycopg2 localement

```powershell
pip install psycopg2-binary
```

### B. Exécuter le script de migration

```powershell
python migrate_to_postgresql.py
```

Le script va :
- Lire toutes les données de `arctic.db`
- Créer les tables dans PostgreSQL
- Transférer les 9 utilisateurs, 5 œuvres et fichiers
- Valider l'intégrité des données

### C. Vérifier les données

Vous pouvez vérifier dans l'interface de Neon ou Supabase que toutes les données sont présentes.

---

## ✅ Étape 5 : Tester l'Application

1. Aller sur l'URL Vercel : `https://arctic-art-platform.vercel.app`
2. Tester la connexion avec un compte existant
3. Tester l'ajout d'une œuvre
4. Tester la navigation

---

## ⚠️ Limitations Importantes de Vercel

### 1. **Fichiers Uploads Non Persistants**

- Vercel est **serverless** : les fichiers uploadés disparaissent après le redémarrage
- **Solution** : Utiliser un service de stockage externe

**Options recommandées :**

#### Option A : Cloudinary (Recommandé)
- Gratuit jusqu'à 25 GB
- CDN intégré
- Optimisation d'images automatique
- [cloudinary.com](https://cloudinary.com)

#### Option B : AWS S3
- Payant mais peu cher
- Très fiable
- Configuration plus complexe

#### Option C : Supabase Storage
- Gratuit jusqu'à 1 GB
- Facile si vous utilisez déjà Supabase
- Intégré avec PostgreSQL

### 2. **Limite de Temps d'Exécution**

- Les requêtes doivent se terminer en **10 secondes** (plan gratuit)
- Plan Pro : 60 secondes

---

## 🔧 Configuration Stockage Externe (Cloudinary)

### A. Créer un compte Cloudinary

1. Aller sur [cloudinary.com](https://cloudinary.com)
2. S'inscrire gratuitement
3. Copier : Cloud Name, API Key, API Secret

### B. Installer la librairie

```powershell
pip install cloudinary
pip freeze > requirements.txt
```

### C. Ajouter les variables d'environnement dans Vercel

| Variable | Valeur |
|----------|--------|
| `CLOUDINARY_CLOUD_NAME` | votre_cloud_name |
| `CLOUDINARY_API_KEY` | votre_api_key |
| `CLOUDINARY_API_SECRET` | votre_api_secret |

---

## 📊 Monitoring et Logs

### Voir les logs Vercel

1. Aller sur vercel.com > Votre projet
2. Onglet "Deployments"
3. Cliquer sur le dernier déploiement
4. Onglet "Logs" pour voir les erreurs

---

## 🔄 Mises à Jour

### Déployer une nouvelle version

```powershell
git add .
git commit -m "Description des changements"
git push origin main
```

Vercel redéploie automatiquement à chaque push sur `main`.

---

## 🆘 Problèmes Courants

### Erreur : "Application Error"

- Vérifier les logs Vercel
- Vérifier que `DATABASE_URL` est correct
- Vérifier que PostgreSQL est accessible

### Erreur : "502 Bad Gateway"

- Le build a échoué
- Vérifier `requirements.txt`
- Vérifier que tous les fichiers nécessaires sont présents

### Les images ne s'affichent pas

- Normal sur Vercel serverless
- Mettre en place Cloudinary ou S3

---

## 📞 Support

- Documentation Vercel : [vercel.com/docs](https://vercel.com/docs)
- Documentation Flask : [flask.palletsprojects.com](https://flask.palletsprojects.com)
- Documentation PostgreSQL : [postgresql.org/docs](https://www.postgresql.org/docs/)

---

## 🎯 Checklist Complète

- [ ] Compte GitHub créé
- [ ] Compte Vercel créé
- [ ] Base PostgreSQL créée (Neon/Supabase)
- [ ] Repository GitHub créé et code poussé
- [ ] Variables d'environnement configurées dans Vercel
- [ ] Application déployée sur Vercel
- [ ] Données migrées de SQLite vers PostgreSQL
- [ ] Tests de connexion OK
- [ ] Stockage externe configuré (Cloudinary/S3)
- [ ] Tests upload d'œuvres OK

---

**Prêt à déployer !** 🚀
