#!/usr/bin/env bash
# Script de build pour Render.com

set -o errexit

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Créer le dossier uploads
mkdir -p uploads

echo "✅ Build terminé avec succès"
