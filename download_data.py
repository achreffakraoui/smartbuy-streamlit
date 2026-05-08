"""
Script de téléchargement des images depuis Kaggle
Utilisé au démarrage sur Render si les images ne sont pas présentes
"""

import os
import sys
import zipfile

def download_images_from_kaggle():
    """Télécharge les images depuis Kaggle si elles ne sont pas présentes"""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    # Vérifier si les images existent déjà
    if os.path.exists(data_dir):
        jpg_files = [f for f in os.listdir(data_dir) if f.endswith('.jpg')]
        if len(jpg_files) > 1000:
            print(f"✅ Images déjà présentes : {len(jpg_files)} fichiers")
            return True
    
    # Vérifier si les credentials Kaggle sont disponibles
    kaggle_username = os.environ.get('KAGGLE_USERNAME')
    kaggle_key = os.environ.get('KAGGLE_KEY')
    
    if not kaggle_username or not kaggle_key:
        print("⚠️ Variables KAGGLE_USERNAME et KAGGLE_KEY non définies - images non téléchargées")
        return False
    
    print("📥 Téléchargement des images depuis Kaggle...")
    
    try:
        # Configurer les credentials Kaggle
        kaggle_dir = os.path.expanduser('~/.kaggle')
        os.makedirs(kaggle_dir, exist_ok=True)
        
        kaggle_json_path = os.path.join(kaggle_dir, 'kaggle.json')
        with open(kaggle_json_path, 'w') as f:
            import json
            json.dump({
                "username": kaggle_username,
                "key": kaggle_key
            }, f)
        os.chmod(kaggle_json_path, 0o600)
        
        # Installer kaggle si nécessaire
        try:
            import kaggle
        except ImportError:
            os.system(f"{sys.executable} -m pip install kaggle")
            import kaggle
        
        # Créer le dossier data
        os.makedirs(data_dir, exist_ok=True)
        
        # Télécharger le dataset (version small = images 80x60)
        print("📦 Téléchargement du dataset fashion-product-images-small...")
        os.system(f"kaggle datasets download -d paramaggarwal/fashion-product-images-small -p {data_dir} --unzip")
        
        # Vérifier le téléchargement
        jpg_files = [f for f in os.listdir(data_dir) if f.endswith('.jpg')]
        print(f"✅ {len(jpg_files)} images téléchargées avec succès")
        return len(jpg_files) > 0
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
        return False


def check_images_available():
    """Vérifie si les images sont disponibles localement"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    if not os.path.exists(data_dir):
        return False
    
    jpg_files = [f for f in os.listdir(data_dir) if f.endswith('.jpg')]
    return len(jpg_files) > 100


if __name__ == "__main__":
    download_images_from_kaggle()
