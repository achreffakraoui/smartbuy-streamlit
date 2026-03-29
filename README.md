# SmartBuy - Application de recommandation de mode IA

Application Streamlit de recommandation de produits de mode utilisant TF-IDF, K-NN et ResNet50.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

## Données (images)

Les images des produits (~4GB) ne sont pas incluses dans ce repo.  
Télécharge le dossier `data/` depuis Google Drive et place-le dans le même dossier que `app.py` :

**[Télécharger data/ sur Google Drive](https://drive.google.com/file/d/1a9pbY_S3iAzUfpmLlg-iSGpL2yq31b-Q/view?usp=drive_link)**

## Structure

```
├── app.py              # Application principale
├── pages_improved.py   # Pages avec IA
├── auth.py             # Authentification
├── database.py         # Base de données
├── styles.py           # CSS
├── models/             # Modèles IA (TF-IDF, KNN, FAISS)
└── data/               # Images produits (à télécharger)
```
