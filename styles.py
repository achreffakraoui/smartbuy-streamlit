"""
SmartBuy - Styles CSS personnalisés
Architecture modulaire pour une meilleure maintenabilité
"""

import streamlit as st

def load_custom_css():
    """Charge les styles CSS personnalisés de l'application"""
    css = """
<style>
/* Variables de couleurs */
:root {
    --primary-color: #FF6B9D;
    --secondary-color: #C44569;
    --accent-color: #F8B500;
    --background-color: #FFFFFF;
    --text-color: #2C3E50;
    --border-color: #E8E8E8;
    --success-color: #27AE60;
    --error-color: #E74C3C;
}

/* Styles généraux */
.main {
    background-color: var(--background-color);
    padding: 1rem;
}

/* Réduire les marges globales */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 100%;
}

/* Réduire l'espace entre les éléments */
.stMarkdown, .stButton, .stImage {
    margin-bottom: 0.3rem !important;
}

/* Colonnes plus compactes */
[data-testid="column"] {
    padding: 0.3rem !important;
}

/* Images centrées et compactes */
[data-testid="stImage"] > img {
    border-radius: 8px;
    margin: 0 auto;
    display: block;
}

/* En-tête */
h1, h2, h3 {
    color: var(--text-color);
    font-weight: 600;
    margin-bottom: 0.5rem;
    margin-top: 0.5rem;
}

/* Boutons */
.stButton button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.3s ease;
    border: none;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Cartes de produits */
.product-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    border: 1px solid var(--border-color);
    margin-bottom: 1rem;
}

.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.product-card img {
    max-width: 100%;
    height: auto;
    object-fit: cover;
    border-radius: 8px;
}

.product-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-color);
    margin-bottom: 0.5rem;
}

.product-price {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
    margin: 0.5rem 0;
}

.product-description {
    color: #6C757D;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 1rem;
}

/* Supprimer les espaces blancs inutiles */
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
}

.element-container {
    margin-bottom: 0.5rem;
}

/* Réduire l'espace entre les colonnes */
[data-testid="column"] {
    padding: 0.5rem;
}

/* Images plus compactes */
[data-testid="stImage"] {
    margin-bottom: 0.5rem;
}

/* Barre de recherche */
.search-container {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(255, 107, 157, 0.2);
}

.search-title {
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.5rem;
}

/* Panier */
.cart-item {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.cart-total {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    font-size: 1.5rem;
    font-weight: 700;
    text-align: center;
    margin-top: 1rem;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
    margin-right: 0.5rem;
}

.badge-primary {
    background-color: var(--primary-color);
    color: white;
}

.badge-secondary {
    background-color: var(--accent-color);
    color: var(--text-color);
}

.badge-success {
    background-color: var(--success-color);
    color: white;
}

/* Formulaires */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    border-radius: 8px;
    border: 2px solid var(--border-color);
    padding: 0.75rem;
    transition: all 0.3s ease;
}

.stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1);
}

/* Sidebar */
.css-1d391kg {
    background-color: #F8F9FA;
}

/* Messages d'alerte */
.stAlert {
    border-radius: 8px;
    border-left: 4px solid;
}

/* Recommandations IA */
.ai-recommendation {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin: 1rem 0;
}

.ai-badge {
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    display: inline-block;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.5s ease-out;
}

/* Responsive */
@media (max-width: 768px) {
    .product-card {
        padding: 1rem;
    }
    
    .search-title {
        font-size: 1.5rem;
    }
    
    .product-price {
        font-size: 1.25rem;
    }
}

/* Footer */
footer {
    text-align: center;
    padding: 2rem 0;
    color: #6C757D;
    font-size: 0.9rem;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-color);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--secondary-color);
}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)