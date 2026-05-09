"""
SmartBuy - Application principale
Achetez malin, vivez mieux
Architecture modulaire et propre
"""

import streamlit as st
import os
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="SmartBuy - Achetez malin, vivez mieux",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Téléchargement des images si nécessaire (Streamlit Cloud / Render)
try:
    from download_data import download_images_from_kaggle, check_images_available
    if not check_images_available():
        with st.spinner("📥 Téléchargement des images produits... (première fois uniquement, ~2-3 min)"):
            success = download_images_from_kaggle()
            if success:
                st.success("✅ Images téléchargées avec succès !")
                st.rerun()
            else:
                st.warning("⚠️ Images non disponibles - vérifiez les secrets KAGGLE_USERNAME et KAGGLE_KEY")
except Exception as e:
    st.warning(f"⚠️ Téléchargement images ignoré : {e}")

# Import des modules
from database import Database
from pages_improved import HomePage, SearchPage, CartPage, CheckoutPage, ContactPage, ProfilePage, ProductDetailsPage
from auth import AuthManager

# Import des styles
from styles import load_custom_css

class SmartBuy:
    """Classe principale de l'application SmartBuy"""
    
    def __init__(self):
        self.db = Database()
        self.auth = AuthManager(self.db)
        self.init_session_state()
    
    def init_session_state(self):
        """Initialise les variables de session"""
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'cart' not in st.session_state:
            st.session_state.cart = []
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
    
    def render_header(self):
        """Affiche l'en-tête de l'application"""
        # Header avec fond professionnel gris (même couleur que le hero section)
        st.markdown("""
        <style>
        .header-container {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header-title {
            text-align: center;
            color: white !important;
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0;
        }
        .header-subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.9);
            font-style: italic;
            margin-top: 0.5rem;
        }
        /* Boutons noirs au lieu de rose */
        div[data-testid="column"] button[kind="primary"] {
            background-color: #2c3e50 !important;
            border-color: #2c3e50 !important;
            color: white !important;
        }
        div[data-testid="column"] button[kind="primary"]:hover {
            background-color: #1a252f !important;
            border-color: #1a252f !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("🏠 Accueil", use_container_width=True, type="primary", key="btn_accueil"):
                st.session_state.page = 'home'
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="header-container">
                <h1 class="header-title">🛒 SmartBuy</h1>
                <p class="header-subtitle">Achetez malin, vivez mieux</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.session_state.user:
                col3a, col3b = st.columns(2)
                with col3a:
                    if st.button("👤 Profil", use_container_width=True, key="btn_profil"):
                        st.session_state.page = 'profile'
                        st.rerun()
                with col3b:
                    if st.button("🚪 Déconnexion", use_container_width=True, key="btn_deconnexion"):
                        self.auth.logout()
                        st.rerun()
            else:
                if st.button("🔐 Connexion", use_container_width=True, type="primary", key="btn_connexion"):
                    st.session_state.page = 'login'
                    st.rerun()
    
    def render_navigation(self):
        """Affiche la barre de navigation"""
        st.markdown("---")
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        
        with nav_col1:
            if st.button("🔍 Recherche", use_container_width=True, 
                        type="primary" if st.session_state.page == 'search' else "secondary"):
                st.session_state.page = 'search'
                st.rerun()
        
        with nav_col2:
            cart_count = len(st.session_state.cart)
            cart_label = f"🛒 Panier ({cart_count})" if cart_count > 0 else "🛒 Panier"
            if st.button(cart_label, use_container_width=True, 
                        type="primary" if st.session_state.page == 'cart' else "secondary"):
                st.session_state.page = 'cart'
                st.rerun()
        
        with nav_col3:
            if st.button("💳 Paiement", use_container_width=True, 
                        type="primary" if st.session_state.page == 'checkout' else "secondary"):
                st.session_state.page = 'checkout'
                st.rerun()
        
        with nav_col4:
            if st.button("📞 Contact", use_container_width=True, 
                        type="primary" if st.session_state.page == 'contact' else "secondary"):
                st.session_state.page = 'contact'
                st.rerun()
        
        st.markdown("---")
    
    def render_sidebar(self):
        """Affiche la barre latérale avec filtres et informations"""
        with st.sidebar:
            st.markdown("### 🎯 Navigation rapide")
            
            # Informations utilisateur
            if st.session_state.user:
                st.success(f"Connecté en tant que: **{st.session_state.user['username']}**")
            else:
                st.info("Connectez-vous pour accéder à toutes les fonctionnalités")
            
            st.markdown("---")
            
            # Filtres de recherche (si sur la page de recherche)
            if st.session_state.page == 'search':
                st.markdown("### 🔍 Filtres")
                st.selectbox("Catégorie", 
                           ["Toutes", "Chaussures", "Vêtements", "Accessoires", "Sacs"],
                           key="filter_category")
                st.slider("Prix maximum (€)", 
                         min_value=0, max_value=500, value=500, step=10,
                         key="filter_price")
                st.multiselect("Marques", 
                             ["Nike", "Adidas", "Zara", "H&M", "Gucci", "Prada"],
                             key="filter_brands")
                st.markdown("---")
            
            # Informations système
            st.markdown("### ℹ️ À propos")
            st.caption("SmartBuy utilise l'intelligence artificielle pour vous recommander les meilleurs produits de mode.")
            st.caption("Achetez malin, vivez mieux - Modèles IA: TF-IDF, K-NN, ResNet50")
    
    def render_footer(self):
        """Affiche le pied de page"""
        st.markdown("---")
        footer_cols = st.columns([1, 1, 1])
        
        with footer_cols[0]:
            st.markdown("**SmartBuy** © 2026")
        with footer_cols[1]:
            st.markdown("Propulsé par l'IA avancée")
        with footer_cols[2]:
            st.markdown("[Politique de confidentialité](#) | [CGU](#)")
    
    def render_page(self):
        """Affiche la page courante"""
        page = st.session_state.page
        
        if page == 'home':
            HomePage(self.db, self.auth).render()
        elif page == 'search':
            SearchPage(self.db, self.auth).render()
        elif page == 'cart':
            CartPage(self.db, self.auth).render()
        elif page == 'checkout':
            CheckoutPage(self.db, self.auth).render()
        elif page == 'contact':
            ContactPage(self.db, self.auth).render()
        elif page == 'profile':
            ProfilePage(self.db, self.auth).render()
        elif page == 'product_details':
            ProductDetailsPage(self.db, self.auth).render()
        elif page in ['login', 'register']:
            self.auth.render()
        else:
            st.error("Page non trouvée")
    
    def run(self):
        """Lance l'application"""
        # Charge les styles CSS personnalisés
        load_custom_css()
        
        # Affiche l'interface
        self.render_header()
        self.render_navigation()
        
        # Colonne principale et sidebar
        self.render_sidebar()
        
        # Contenu principal
        self.render_page()
        
        # Pied de page
        self.render_footer()

def main():
    """Point d'entrée principal"""
    try:
        app = SmartBuy()
        app.run()
    except Exception as e:
        st.error(f"Une erreur est survenue: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()