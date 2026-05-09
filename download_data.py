"""
Script de téléchargement des images depuis Kaggle.
Compatible Streamlit Cloud (secrets) et Render (env vars).
Les images sont stockées dans ./data/ (même dossier que l'app).
"""

import os
import sys
import json
import subprocess

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_BASE_DIR, 'data')


def _get_kaggle_credentials():
    """Récupère les credentials Kaggle depuis Streamlit secrets ou variables d'environnement."""
    username = None
    key = None

    # 1. Essayer Streamlit secrets (Streamlit Cloud)
    try:
        import streamlit as st
        username = st.secrets.get("KAGGLE_USERNAME") or st.secrets.get("kaggle", {}).get("username")
        key = st.secrets.get("KAGGLE_KEY") or st.secrets.get("kaggle", {}).get("key")
    except Exception:
        pass

    # 2. Fallback : variables d'environnement (Render, local)
    if not username:
        username = os.environ.get('KAGGLE_USERNAME')
    if not key:
        key = os.environ.get('KAGGLE_KEY')

    return username, key


def check_images_available():
    """Vérifie si les images sont disponibles localement."""
    if not os.path.exists(DATA_DIR):
        return False
    jpg_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.jpg')]
    return len(jpg_files) > 100


def download_images_from_kaggle():
    """Télécharge les images depuis Kaggle si elles ne sont pas présentes."""

    # Vérifier si les images existent déjà
    if check_images_available():
        jpg_count = len([f for f in os.listdir(DATA_DIR) if f.endswith('.jpg')])
        print(f"✅ Images déjà présentes : {jpg_count} fichiers")
        return True

    # Récupérer les credentials
    kaggle_username, kaggle_key = _get_kaggle_credentials()

    if not kaggle_username or not kaggle_key:
        print("⚠️ Credentials Kaggle non trouvés (KAGGLE_USERNAME / KAGGLE_KEY)")
        return False

    print(f"📥 Téléchargement des images depuis Kaggle vers {DATA_DIR} ...")

    try:
        # Écrire le fichier kaggle.json
        kaggle_dir = os.path.expanduser('~/.kaggle')
        os.makedirs(kaggle_dir, exist_ok=True)
        kaggle_json_path = os.path.join(kaggle_dir, 'kaggle.json')
        with open(kaggle_json_path, 'w') as f:
            json.dump({"username": kaggle_username, "key": kaggle_key}, f)
        os.chmod(kaggle_json_path, 0o600)

        # Installer kaggle CLI si nécessaire
        try:
            import kaggle as _  # noqa
        except ImportError:
            print("❌ Module kaggle non disponible - ajoutez kaggle dans requirements.txt")
            return False

        # Créer le dossier data
        os.makedirs(DATA_DIR, exist_ok=True)

        # Télécharger le dataset (version COMPLETE = images haute résolution ~80x60 -> 400x300)
        print("📦 Téléchargement du dataset fashion-product-images-dataset (version complète)...")
        result = subprocess.run(
            ["kaggle", "datasets", "download",
             "-d", "paramaggarwal/fashion-product-images-dataset",
             "-p", DATA_DIR, "--unzip"],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Erreur kaggle CLI : {result.stderr}")
            return False

        # Les images peuvent être dans un sous-dossier "images/" après unzip
        images_subdir = os.path.join(DATA_DIR, 'images')
        if os.path.exists(images_subdir):
            import shutil
            for fname in os.listdir(images_subdir):
                src = os.path.join(images_subdir, fname)
                dst = os.path.join(DATA_DIR, fname)
                if not os.path.exists(dst):
                    shutil.move(src, dst)
            # Supprimer le sous-dossier vide
            try:
                os.rmdir(images_subdir)
            except OSError:
                pass

        # Résultat final
        jpg_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.jpg')]
        print(f"✅ {len(jpg_files)} images téléchargées avec succès dans {DATA_DIR}")
        return len(jpg_files) > 0

    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
        import traceback
        traceback.print_exc()
        return False


def get_image_path(image_filename):
    """Retourne le chemin complet d'une image, ou None si introuvable."""
    path = os.path.join(DATA_DIR, image_filename)
    return path if os.path.exists(path) else None


if __name__ == "__main__":
    print("=== Téléchargement des images SmartBuy ===")
    success = download_images_from_kaggle()
    sys.exit(0 if success else 1)
