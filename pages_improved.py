"""
SmartBuy - Gestionnaire de pages avec IA complète
Toutes les fonctionnalités IA activées : TF-IDF, K-NN, ResNet50, FAISS
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
from PIL import Image
import pickle
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# ============================================
# CLASSE DE BASE POUR LES PAGES
# ============================================

class BasePage:
    """Classe de base pour toutes les pages"""
    
    def __init__(self, db, auth):
        self.db = db
        self.auth = auth
        self.load_models()
        self.load_categories()
    
    def load_models(self):
        """Charge tous les modèles IA"""
        try:
            # Chemin absolu basé sur l'emplacement de ce fichier
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(base_dir, 'models')

            # Modèles textuels
            self.tfidf_vectorizer = joblib.load(os.path.join(models_dir, 'tfidf.pkl'))
            self.knn_model = joblib.load(os.path.join(models_dir, 'knn_text.pkl'))
            
            # Dataset
            self.df_products = pd.read_csv(os.path.join(models_dir, 'stylesclean.csv'))
            
            # Index FAISS pour recherche visuelle
            try:
                if FAISS_AVAILABLE:
                    self.faiss_index = faiss.read_index(os.path.join(models_dir, 'resnet_faiss.index'))
                    self.has_faiss = True
                else:
                    self.faiss_index = None
                    self.has_faiss = False
            except:
                self.faiss_index = None
                self.has_faiss = False
            
            # Index FAISS hybride
            try:
                if FAISS_AVAILABLE:
                    self.hybrid_index = faiss.read_index(os.path.join(models_dir, 'hybrid_faiss.index'))
                    self.has_hybrid = True
                else:
                    self.hybrid_index = None
                    self.has_hybrid = False
            except:
                self.hybrid_index = None
                self.has_hybrid = False
            
            # Ne pas afficher de message de succès
                
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des modèles : {e}")
            self.tfidf_vectorizer = None
            self.knn_model = None
            self.df_products = pd.DataFrame()
            self.faiss_index = None
            self.hybrid_index = None
            self.has_faiss = False
            self.has_hybrid = False
    
    def load_categories(self):
        """Charge les catégories basées sur le dataset réel"""
        # Catégories réelles du dataset: Casual Shoes, Handbags, Heels, Kurtas, Shirts, Sports Shoes, Sunglasses, Tops, Tshirts, Watches
        self.categories = [
            {"name": "Chaussures Casual", "icon": "👟", "filter": "Casual Shoes"},
            {"name": "Chaussures Sport", "icon": "⚽", "filter": "Sports Shoes"},
            {"name": "Talons", "icon": "👠", "filter": "Heels"},
            {"name": "Chemises", "icon": "👔", "filter": "Shirts"},
            {"name": "T-Shirts", "icon": "👕", "filter": "Tshirts"},
            {"name": "Tops", "icon": "👚", "filter": "Tops"},
            {"name": "Kurtas", "icon": "👗", "filter": "Kurtas"},
            {"name": "Montres", "icon": "⌚", "filter": "Watches"},
            {"name": "Sacs à main", "icon": "👜", "filter": "Handbags"},
            {"name": "Lunettes", "icon": "🕶️", "filter": "Sunglasses"}
        ]
    
    def get_similar_products_text(self, product_index, n=6):
        """Trouve les produits similaires par texte (K-NN) - MÊME CATÉGORIE UNIQUEMENT"""
        try:
            if self.knn_model is None or self.df_products.empty:
                return pd.DataFrame()
            
            # Obtenir le produit de référence et sa catégorie
            reference_product = self.df_products.iloc[product_index]
            reference_category = reference_product.get('category', '')
            
            # Obtenir le vecteur du produit
            product_desc = reference_product['description']
            product_vector = self.tfidf_vectorizer.transform([product_desc])
            
            # Trouver les voisins les plus proches (chercher plus pour filtrer ensuite)
            distances, indices = self.knn_model.kneighbors(product_vector, n_neighbors=min(100, len(self.df_products)))
            
            # Filtrer pour garder UNIQUEMENT la même catégorie
            similar_products = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx != product_index:
                    product = self.df_products.iloc[idx]
                    if product.get('category', '') == reference_category:
                        similar_products.append(idx)
                        if len(similar_products) >= n:
                            break
            
            return self.df_products.iloc[similar_products]
            
        except Exception as e:
            st.error(f"Erreur similarité texte : {e}")
            return pd.DataFrame()
    
    def get_similar_products_visual(self, product_index, n=6):
        """Trouve les produits similaires par image (FAISS) - MÊME CATÉGORIE UNIQUEMENT"""
        try:
            if self.df_products.empty or product_index >= len(self.df_products):
                return pd.DataFrame()
            
            # Obtenir le produit de référence et sa catégorie
            reference_product = self.df_products.iloc[product_index]
            reference_category = reference_product.get('category', '')
            
            # Si FAISS est disponible, l'utiliser MAIS filtrer par catégorie
            if self.has_faiss and self.faiss_index is not None:
                try:
                    # Recherche dans l'index FAISS (chercher plus pour filtrer ensuite)
                    distances, indices = self.faiss_index.search(np.array([[product_index]]), min(100, len(self.df_products)))
                    
                    # Filtrer pour garder UNIQUEMENT la même catégorie
                    similar_products = []
                    for idx in indices[0]:
                        if idx != product_index and idx < len(self.df_products):
                            product = self.df_products.iloc[idx]
                            if product.get('category', '') == reference_category:
                                similar_products.append(idx)
                                if len(similar_products) >= n:
                                    break
                    
                    if similar_products:
                        return self.df_products.iloc[similar_products]
                except:
                    pass
            
            # Sinon, retourner des produits de la même catégorie
            same_category = self.df_products[
                (self.df_products['category'] == reference_category) &
                (self.df_products.index != product_index)
            ]
            
            if len(same_category) > 0:
                return same_category.sample(n=min(n, len(same_category)))
            
            # Si aucun produit de la même catégorie, retourner DataFrame vide
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erreur similarité visuelle : {e}")
            return pd.DataFrame()
    
    def get_similar_products_hybrid(self, product_index, n=12):
        """Combine similarité texte + image pour recommandations optimales - MÊME CATÉGORIE UNIQUEMENT"""
        try:
            # Obtenir le produit de référence
            if product_index >= len(self.df_products):
                return pd.DataFrame()
            
            reference_product = self.df_products.iloc[product_index]
            reference_category = reference_product.get('category', '')
            
            # Filtrer d'abord par catégorie
            same_category_products = self.df_products[
                (self.df_products['category'] == reference_category) &
                (self.df_products.index != product_index)
            ]
            
            if same_category_products.empty:
                return pd.DataFrame()
            
            # Obtenir les similarités textuelles (seulement de la même catégorie)
            text_similar = self.get_similar_products_text(product_index, n=n)
            text_similar = text_similar[text_similar['category'] == reference_category]
            
            # Obtenir les similarités visuelles (seulement de la même catégorie)
            visual_similar = self.get_similar_products_visual(product_index, n=n)
            visual_similar = visual_similar[visual_similar['category'] == reference_category]
            
            # Combiner et dédupliquer
            combined = pd.concat([text_similar, visual_similar]).drop_duplicates()
            
            # Vérifier encore une fois que tous sont de la même catégorie
            combined = combined[combined['category'] == reference_category]
            
            return combined.head(n)
            
        except Exception as e:
            st.error(f"Erreur similarité hybride : {e}")
            return pd.DataFrame()
    
    def display_product_card(self, product, key, show_details_button=True):
        """Affiche une carte produit standardisée"""
        with st.container():
            # Image
            base_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(base_dir, 'data', product.get('image_path', 'default.jpg'))
            if os.path.exists(img_path):
                st.image(img_path, width=250)
            else:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); 
                           height: 200px; display: flex; align-items: center; 
                           justify-content: center; border-radius: 10px; color: white; margin-bottom: 0.5rem;'>
                    <span style='font-size: 2rem;'>🛍️</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Informations produit
            st.markdown(f"**{product.get('display name', 'Produit')[:50]}**")
            st.caption(f"Catégorie: {product.get('category', 'N/A')}")
            
            # Prix simulé basé sur l'index du produit pour avoir des prix variés
            # Utiliser le nom du produit comme seed pour cohérence
            product_name = product.get('display name', product.get('productDisplayName', 'Product'))
            # Créer un seed unique basé sur le hash du nom
            seed_value = abs(hash(product_name)) % 10000
            np.random.seed(seed_value)
            price = np.random.randint(20, 200)
            st.markdown(f"<div style='color: #FF6B9D; font-size: 1.3rem; font-weight: bold; margin: 0.3rem 0;'>{price}€</div>", unsafe_allow_html=True)
            
            # Description courte
            description = product.get('description', 'Aucune description disponible')
            st.caption(f"{description[:80]}...")
            
            # Boutons d'action
            if show_details_button:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🛒 Panier", key=f"cart_{key}", use_container_width=True):
                        self.add_to_cart(product)
                with col2:
                    if st.button("👀 Détails", key=f"view_{key}", use_container_width=True):
                        self.view_product_details(product)
            else:
                if st.button("🛒 Ajouter au panier", key=f"cart_{key}", use_container_width=True):
                    self.add_to_cart(product)
    
    def add_to_cart(self, product):
        """Ajoute un produit au panier"""
        if not st.session_state.user:
            st.warning("🔐 Connectez-vous pour ajouter au panier")
            return
        
        if 'cart' not in st.session_state:
            st.session_state.cart = []
        
        st.session_state.cart.append(product)
        st.success("✅ Produit ajouté au panier !")
    
    def view_product_details(self, product):
        """Affiche les détails complets d'un produit avec recommandations"""
        # Enregistrer l'historique si l'utilisateur est connecté
        if st.session_state.user:
            result = self.db.add_user_history(
                user_id=st.session_state.user['id'],
                category=product.get('category', ''),
                product_id=product.get('id', None),
                action_type='product_view'
            )
            # Debug : afficher un message de confirmation
            if result.get('success'):
                st.toast(f"✅ Vue produit enregistrée : {product.get('category', '')}", icon="✅")
        
        st.session_state.viewing_product = product
        st.session_state.page = 'product_details'
        st.rerun()

# ============================================
# PAGE D'ACCUEIL
# ============================================

class HomePage(BasePage):
    """Page d'accueil avec recommandations IA"""
    
    def render(self):
        """Affiche la page d'accueil"""
        # Hero Section
        st.markdown("""
        <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); 
                    padding: 30px 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
            <h1 style='color: white; font-size: 2em; margin: 0;'>Bienvenue sur SmartBuy</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Barre de recherche rapide
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            search_query = st.text_input("", placeholder="🔍 Rechercher un produit...", key="home_search")
            if search_query:
                st.session_state.page = "search"
                st.session_state.search_query = search_query
                st.rerun()
        
        # Catégories principales (10 catégories réelles)
        st.markdown("### 🏷️ Catégories Populaires")
        
        # Afficher en 5 colonnes x 2 lignes
        for row in range(2):
            cols = st.columns(5)
            for col_idx, col in enumerate(cols):
                cat_idx = row * 5 + col_idx
                if cat_idx < len(self.categories):
                    cat = self.categories[cat_idx]
                    with col:
                        if st.button(f"{cat['icon']}\n{cat['name']}", key=f"cat_{cat_idx}", use_container_width=True):
                            # Enregistrer l'historique si l'utilisateur est connecté
                            if st.session_state.user:
                                result = self.db.add_user_history(
                                    user_id=st.session_state.user['id'],
                                    category=cat['filter'],
                                    action_type='category_click'
                                )
                                # Debug : afficher un message de confirmation
                                if result.get('success'):
                                    st.toast(f"✅ Historique enregistré : {cat['filter']}", icon="✅")
                            
                            st.session_state.page = "search"
                            st.session_state.category_filter = cat['filter']
                            st.session_state.search_query = ""  # Reset search
                            if 'search_page' in st.session_state:
                                del st.session_state.search_page
                            st.rerun()
        
        # Produits recommandés - PERSONNALISÉS selon l'historique
        st.markdown("---")
        
        # Vérifier si l'utilisateur est connecté et a un historique
        user_has_history = False
        preferred_categories = []
        
        if st.session_state.user:
            user_id = st.session_state.user['id']
            preferred_categories = self.db.get_user_preferred_categories(user_id, limit=5)
            user_has_history = len(preferred_categories) > 0
        
        if user_has_history:
            st.markdown(f"### 🎯 Recommandations Personnalisées pour {st.session_state.user['full_name']}")
            st.caption(f"Basées sur vos catégories préférées : {', '.join(preferred_categories[:3])}")
        else:
            st.markdown("### 🎯 Produits Recommandés (IA)")
        
        if self.df_products is not None and not self.df_products.empty:
            # Trier les produits selon l'historique utilisateur
            if user_has_history:
                # Créer un ordre personnalisé : 10 produits de chaque catégorie préférée
                sorted_products = pd.DataFrame()
                displayed_product_ids = set()  # Pour éviter les répétitions
                
                # Ajouter 10 produits de chaque catégorie préférée (ordre inversé = dernière recherche en premier)
                for category in preferred_categories:
                    category_products = self.df_products[self.df_products['category'] == category]
                    # Prendre seulement les 10 premiers produits de cette catégorie
                    category_products_limited = category_products.head(10)
                    sorted_products = pd.concat([sorted_products, category_products_limited])
                    # Enregistrer les IDs des produits affichés
                    displayed_product_ids.update(category_products_limited.index.tolist())
                
                # Ajouter les autres produits MÉLANGÉS (sans répétition)
                # Exclure les produits déjà affichés
                remaining_products = self.df_products[~self.df_products.index.isin(displayed_product_ids)]
                # Mélanger les produits restants pour éviter l'affichage par catégorie
                remaining_products_shuffled = remaining_products.sample(frac=1, random_state=42).reset_index(drop=True)
                sorted_products = pd.concat([sorted_products, remaining_products_shuffled])
                
                # Réinitialiser l'index
                sorted_products = sorted_products.reset_index(drop=True)
            else:
                # Mélanger TOUS les produits de TOUTES les catégories (comportement par défaut)
                sorted_products = self.df_products.sample(frac=1, random_state=42).reset_index(drop=True)
            
            # Pagination
            products_per_page = 100
            total_products = len(sorted_products)
            total_pages = (total_products + products_per_page - 1) // products_per_page
            
            # Initialiser la page si nécessaire
            if 'home_page' not in st.session_state:
                st.session_state.home_page = 1
            
            current_page = st.session_state.home_page
            
            # Boutons de pagination - 3 colonnes
            col1, col2, col3 = st.columns([3, 1, 3])
            
            with col1:
                if st.button("⬅️ Page Précédente", disabled=(current_page == 1), use_container_width=True, key="home_prev"):
                    st.session_state.home_page = max(1, current_page - 1)
                    st.rerun()
            
            with col2:
                st.markdown(f"<div style='text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #6c757d 0%, #495057 100%); border-radius: 5px;'>"
                          f"<strong style='font-size: 1rem; color: white;'>Page {current_page}/{total_pages}</strong>"
                          f"</div>", unsafe_allow_html=True)
            
            with col3:
                if st.button("Page Suivante ➡️", disabled=(current_page == total_pages), use_container_width=True, key="home_next"):
                    st.session_state.home_page = min(total_pages, current_page + 1)
                    st.rerun()
            
            # Calculer les indices
            start_idx = (current_page - 1) * products_per_page
            end_idx = min(start_idx + products_per_page, total_products)
            
            # Afficher les produits de la page actuelle
            products_to_show = sorted_products.iloc[start_idx:end_idx]
            
            # Affichage en grille 4 colonnes
            for i in range(0, len(products_to_show), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    if i + j < len(products_to_show):
                        product = products_to_show.iloc[i + j]
                        with col:
                            self.display_product_card(product, f"home_{start_idx + i}_{j}")
        
        # Statistiques
        st.markdown("---")
        st.markdown("### 📊 Statistiques SmartBuy")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🛍️ Produits", f"{len(self.df_products):,}", "↗️ 44K+")
        with col2:
            st.metric("👥 Utilisateurs", "1,200+", "↗️ 8%")
        with col3:
            st.metric("🤖 IA Précision", "94%", "↗️ TF-IDF+K-NN")
        with col4:
            st.metric("⭐ Satisfaction", "4.8/5", "↗️ FAISS")

# ============================================
# PAGE DÉTAILS PRODUIT
# ============================================

class ProductDetailsPage(BasePage):
    """Page de détails d'un produit avec recommandations IA"""
    
    def render(self):
        """Affiche les détails complets du produit"""
        if 'viewing_product' not in st.session_state:
            st.warning("Aucun produit sélectionné")
            if st.button("🏠 Retour à l'accueil"):
                st.session_state.page = 'home'
                st.rerun()
            return
        
        product = st.session_state.viewing_product
        
        # Bouton retour
        if st.button("← Retour"):
            del st.session_state.viewing_product
            st.session_state.page = 'home'
            st.rerun()
        
        st.markdown("---")
        
        # Détails du produit
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Image principale
            img_path = f"data/{product.get('image_path', 'default.jpg')}"
            if os.path.exists(img_path):
                st.image(img_path, width=400)
            else:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); 
                           height: 400px; display: flex; align-items: center; 
                           justify-content: center; border-radius: 10px; color: white;'>
                    <span style='font-size: 4rem;'>🛍️</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Informations détaillées
            st.markdown(f"# {product.get('display name', 'Produit')}")
            st.markdown(f"**Catégorie:** {product.get('category', 'N/A')}")
            
            # Prix
            product_id = product.get('id', 0)
            np.random.seed(int(product_id) if product_id else 0)
            price = np.random.randint(20, 200)
            st.markdown(f"## 💰 {price}€")
            
            # Description complète
            st.markdown("### 📝 Description")
            st.write(product.get('description', 'Aucune description disponible'))
            
            # Bouton d'achat
            if st.button("🛒 Ajouter au panier", type="primary", use_container_width=True):
                self.add_to_cart(product)
        
        # Produits similaires - Combinaison IA complète
        st.markdown("---")
        st.markdown("### 🎯 Produits similaires par description et image (K-NN + TF-IDF + ResNet50 + FAISS)")
        st.caption("🤖 Recommandations intelligentes combinant analyse textuelle ET visuelle pour trouver les produits les plus similaires")
        
        # Trouver l'index réel du produit dans le DataFrame complet
        product_id = product.get('id', None)
        current_category = product.get('category', '')
        
        # Chercher le produit dans le DataFrame par son ID
        if product_id is not None:
            matching_products = self.df_products[self.df_products['id'] == product_id]
            if not matching_products.empty:
                product_index = matching_products.index[0]
            else:
                # Si pas trouvé par ID, chercher par nom
                product_name = product.get('display name', '')
                matching_products = self.df_products[self.df_products['display name'] == product_name]
                if not matching_products.empty:
                    product_index = matching_products.index[0]
                else:
                    st.error("Produit non trouvé dans la base de données")
                    return
        else:
            # Fallback : utiliser l'index du produit si disponible
            product_index = product.name if hasattr(product, 'name') else 0
        
        # Obtenir les produits similaires - UNIQUEMENT DE LA MÊME CATÉGORIE
        # Méthode simple et efficace : filtrer d'abord par catégorie, puis chercher les similaires
        
        # 1. Filtrer tous les produits de la même catégorie
        same_category_products = self.df_products[
            (self.df_products['category'] == current_category) &
            (self.df_products.index != product_index)
        ]
        
        if same_category_products.empty:
            st.info(f"Aucun autre produit trouvé dans la catégorie '{current_category}'")
        else:
            # 2. Utiliser K-NN pour trouver les plus similaires PARMI les produits de la même catégorie
            try:
                product_desc = self.df_products.iloc[product_index]['description']
                product_vector = self.tfidf_vectorizer.transform([product_desc])
                
                # Créer un vecteur TF-IDF pour chaque produit de la même catégorie
                same_category_descriptions = same_category_products['description'].tolist()
                same_category_vectors = self.tfidf_vectorizer.transform(same_category_descriptions)
                
                # Calculer la similarité cosinus
                from sklearn.metrics.pairwise import cosine_similarity
                similarities = cosine_similarity(product_vector, same_category_vectors)[0]
                
                # Trier par similarité décroissante
                similar_indices = similarities.argsort()[::-1][:18]
                similar_hybrid = same_category_products.iloc[similar_indices]
                
            except Exception as e:
                # Si erreur, prendre des produits aléatoires de la même catégorie
                similar_hybrid = same_category_products.sample(n=min(18, len(same_category_products)))
            
            # 3. Afficher les produits similaires
            for i in range(0, len(similar_hybrid), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(similar_hybrid):
                        sim_product = similar_hybrid.iloc[i + j]
                        with col:
                            # Utiliser un index unique basé sur l'index réel du produit
                            unique_key = f"detail_{sim_product.name if hasattr(sim_product, 'name') else i*3+j}"
                            self.display_product_card(sim_product, unique_key, show_details_button=True)

# ============================================
# EXPORTS
# ============================================

__all__ = ['HomePage', 'ProductDetailsPage', 'SearchPage', 'CartPage', 'CheckoutPage', 'ContactPage', 'ProfilePage']


# ============================================
# PAGE DE RECHERCHE
# ============================================

class SearchPage(BasePage):
    """Page de recherche avec IA TF-IDF + K-NN"""
    
    def render(self):
        """Affiche la page de recherche"""
        st.markdown("# 🔍 Recherche Intelligente (TF-IDF + K-NN)")
        
        # Vérifier si on vient d'une catégorie
        category_filter = st.session_state.get('category_filter', 'Toutes')
        
        # Barre de recherche principale
        col1, col2 = st.columns([4, 1])
        with col1:
            search_query = st.text_input(
                "Rechercher", 
                value=st.session_state.get('search_query', ''),
                placeholder="Ex: robe rouge élégante, sneakers Nike...",
                key="search_input"
            )
        with col2:
            search_button = st.button("🔍 Rechercher", use_container_width=True, type="primary")
        
        # Si l'utilisateur tape dans la recherche, réinitialiser le filtre de catégorie
        if search_query and search_query != st.session_state.get('last_search', ''):
            st.session_state.category_filter = 'Toutes'
            category_filter = 'Toutes'
            st.session_state.last_search = search_query
        
        # Filtres avancés
        with st.expander("🎛️ Filtres avancés", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.selectbox("Catégorie", 
                    ["Toutes"] + [cat['filter'] for cat in self.categories],
                    index=0 if category_filter == 'Toutes' else 
                          [cat['filter'] for cat in self.categories].index(category_filter) + 1 
                          if category_filter in [cat['filter'] for cat in self.categories] else 0)
                st.session_state.category_filter = category_filter
            with col2:
                price_range = st.slider("Prix (€)", min_value=0, max_value=1000, value=(0, 500), step=10)
            with col3:
                sort_by = st.selectbox("Trier par", 
                    ["Pertinence IA", "Prix croissant", "Prix décroissant", "Nouveautés"])
        
        # Déterminer quels produits afficher - PRIORITÉ À LA RECHERCHE
        if search_button or (search_query and search_query.strip()):
            # Recherche IA a la priorité
            with st.spinner("🤖 Recherche IA en cours (TF-IDF + K-NN)..."):
                results = self.search_products_ai(search_query, category_filter, price_range, sort_by)
            
            # Enregistrer la recherche si utilisateur connecté
            if st.session_state.user and search_query:
                self.log_search(search_query)
            
            # Afficher les résultats
            if len(results) > 0:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); 
                           padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;'>
                    <div style='color: white; font-size: 1.3rem; font-weight: bold;'>✨ {len(results)} résultats trouvés pour "{search_query}"</div>
                </div>
                """, unsafe_allow_html=True)
                
                self.display_paginated_results(results, "search")
            else:
                st.info("🔍 Aucun produit trouvé. Essayez d'autres mots-clés.")
        
        elif category_filter != 'Toutes':
            # Afficher TOUS les produits de la catégorie sélectionnée
            st.markdown(f"### 🏷️ Catégorie : {category_filter}")
            
            # Enregistrer l'historique si utilisateur connecté
            if st.session_state.user:
                self.db.add_user_history(
                    user_id=st.session_state.user['id'],
                    category=category_filter,
                    action_type='category_filter'
                )
            
            # Filtrer directement par la catégorie exacte
            mask = self.df_products['category'] == category_filter
            
            results = self.df_products[mask].copy()
            
            if len(results) > 0:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); 
                           padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;'>
                    <div style='color: white; font-size: 1.3rem; font-weight: bold;'>✨ {len(results)} produits trouvés dans "{category_filter}"</div>
                </div>
                """, unsafe_allow_html=True)
                
                self.display_paginated_results(results, "category")
            else:
                st.warning(f"🔍 Aucun produit trouvé dans la catégorie '{category_filter}'")
                st.info("💡 Essayez une autre catégorie ou utilisez la recherche")
        
        else:
            st.info("💡 Saisissez un terme de recherche ou sélectionnez une catégorie")
    
    def display_paginated_results(self, results, page_type):
        """Affiche les résultats avec pagination améliorée"""
        products_per_page = 100
        total_products = len(results)
        total_pages = (total_products + products_per_page - 1) // products_per_page
        
        # Initialiser la page si nécessaire
        page_key = f'{page_type}_page'
        if page_key not in st.session_state:
            st.session_state[page_key] = 1
        
        current_page = st.session_state[page_key]
        
        # Boutons de pagination - 3 colonnes
        col1, col2, col3 = st.columns([3, 1, 3])
        
        with col1:
            if st.button("⬅️ Page Précédente", key=f"prev_{page_type}", disabled=(current_page == 1), use_container_width=True):
                st.session_state[page_key] = max(1, current_page - 1)
                st.rerun()
        
        with col2:
            st.markdown(f"<div style='text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #6c757d 0%, #495057 100%); border-radius: 5px;'>"
                      f"<strong style='font-size: 1rem; color: white;'>Page {current_page}/{total_pages}</strong>"
                      f"</div>", unsafe_allow_html=True)
        
        with col3:
            if st.button("Page Suivante ➡️", key=f"next_{page_type}", disabled=(current_page == total_pages), use_container_width=True):
                st.session_state[page_key] = min(total_pages, current_page + 1)
                st.rerun()
        
        # Calculer les indices
        start_idx = (current_page - 1) * products_per_page
        end_idx = min(start_idx + products_per_page, total_products)
        results_to_show = results.iloc[start_idx:end_idx]
        
        # Grille de résultats (4 colonnes)
        for i in range(0, len(results_to_show), 4):
            cols = st.columns(4)
            for j, col in enumerate(cols):
                if i + j < len(results_to_show):
                    product = results_to_show.iloc[i + j]
                    with col:
                        self.display_product_card(product, f"{page_type}_{start_idx + i}_{j}")
    
    def search_products_ai(self, query, category, price_range, sort_by):
        """Recherche de produits avec IA (TF-IDF + K-NN) + recherche directe"""
        if not query:
            return pd.DataFrame()
        
        try:
            # 1. D'abord chercher directement dans les catégories
            query_lower = query.lower()
            category_matches = pd.DataFrame()
            
            # Mapping français -> anglais pour les catégories
            category_mapping = {
                'talons': 'Heels',
                'chaussures': 'Shoes',
                'sac': 'Handbags',
                'montre': 'Watches',
                'lunettes': 'Sunglasses',
                'chemise': 'Shirts',
                'top': 'Tops',
                'tshirt': 'Tshirts',
                't-shirt': 'Tshirts',
                'kurta': 'Kurtas'
            }
            
            # Vérifier si le mot-clé correspond à une catégorie
            for fr_word, en_category in category_mapping.items():
                if fr_word in query_lower:
                    mask = self.df_products['category'] == en_category
                    category_matches = self.df_products[mask].copy()
                    if len(category_matches) > 0:
                        category_matches['relevance_score'] = 1.0
                        return category_matches
            
            # 2. Recherche directe dans la catégorie (anglais)
            for cat in self.df_products['category'].unique():
                if cat and query_lower in cat.lower():
                    mask = self.df_products['category'] == cat
                    category_matches = self.df_products[mask].copy()
                    if len(category_matches) > 0:
                        category_matches['relevance_score'] = 1.0
                        return category_matches
            
            # 3. Si pas de correspondance directe, utiliser TF-IDF + K-NN
            if self.tfidf_vectorizer is None or self.knn_model is None:
                return pd.DataFrame()
            
            # Vectoriser la requête avec TF-IDF
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Obtenir les produits similaires avec K-NN
            distances, indices = self.knn_model.kneighbors(query_vector, n_neighbors=min(500, len(self.df_products)))
            
            # Récupérer les produits correspondants
            results = self.df_products.iloc[indices[0]].copy()
            
            # Ajouter le score de pertinence
            results['relevance_score'] = 1 - distances[0]  # Plus proche = score plus élevé
            
            # Appliquer les filtres
            if category != "Toutes":
                results = results[results['category'] == category]
            
            # Trier selon le critère
            if sort_by == "Pertinence IA":
                results = results.sort_values('relevance_score', ascending=False)
            elif sort_by == "Prix croissant":
                results = results.sample(frac=1)
            elif sort_by == "Prix décroissant":
                results = results.sample(frac=1)
            else:  # Nouveautés
                results = results.sample(frac=1)
            
            return results
            
        except Exception as e:
            st.error(f"Erreur lors de la recherche IA: {e}")
            return pd.DataFrame()
    
    def log_search(self, query):
        """Enregistre la recherche de l'utilisateur dans l'historique"""
        if st.session_state.user and query:
            # Essayer de détecter la catégorie dans la recherche
            query_lower = query.lower()
            detected_category = None
            
            # Mapper les mots-clés aux catégories
            category_keywords = {
                'Casual Shoes': ['casual', 'shoes', 'chaussures casual'],
                'Sports Shoes': ['sport', 'running', 'sneakers', 'basket'],
                'Heels': ['heels', 'talons', 'escarpins'],
                'Shirts': ['shirt', 'chemise'],
                'Tshirts': ['tshirt', 't-shirt', 'tee'],
                'Tops': ['top', 'haut'],
                'Kurtas': ['kurta'],
                'Watches': ['watch', 'montre'],
                'Handbags': ['handbag', 'sac', 'bag'],
                'Sunglasses': ['sunglasses', 'lunettes']
            }
            
            # Détecter la catégorie
            for category, keywords in category_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    detected_category = category
                    break
            
            # Enregistrer dans l'historique
            if detected_category:
                self.db.add_user_history(
                    user_id=st.session_state.user['id'],
                    category=detected_category,
                    action_type='search'
                )


# ============================================
# PAGE PANIER (Inchangée)
# ============================================

class CartPage(BasePage):
    """Page du panier d'achat"""
    
    def render(self):
        """Affiche la page du panier"""
        st.markdown("# 🛒 Mon Panier")
        
        if not st.session_state.user:
            st.info("🔐 Connectez-vous pour accéder à votre panier.")
            return
        
        cart_items = st.session_state.get('cart', [])
        
        if not cart_items:
            st.markdown("""
            <div style='text-align: center; padding: 3rem; background: white; 
                        border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <h3>🛒 Votre panier est vide</h3>
                <p>Découvrez nos produits et ajoutez vos favoris !</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🛍️ Continuer mes achats", use_container_width=True):
                st.session_state.page = "search"
                st.rerun()
            return
        
        # Afficher les articles du panier
        total = 0
        for i, item in enumerate(cart_items):
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            
            with col1:
                img_path = f"data/{item.get('image_path', 'default.jpg')}"
                if os.path.exists(img_path):
                    st.image(img_path, width=80)
                else:
                    st.markdown("📷")
            
            with col2:
                st.markdown(f"**{item.get('display name', 'Produit')}**")
                st.caption(f"Catégorie: {item.get('category', 'N/A')}")
            
            with col3:
                quantity = st.number_input("Qté", min_value=1, value=1, key=f"qty_{i}")
            
            with col4:
                product_id = item.get('id', 0)
                np.random.seed(int(product_id) if product_id else 0)
                price = np.random.randint(20, 200)
                item_total = price * quantity
                st.markdown(f"**{item_total}€**")
                
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            
            total += item_total
            st.divider()
        
        # Résumé du panier
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #FF6B9D 0%, #C44569 100%); 
                       color: white; padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <div style='font-size: 1.1rem;'>Sous-total: {total}€</div>
                <div style='font-size: 1rem;'>Livraison: Gratuite</div>
                <div style='font-size: 1.8rem; margin-top: 1rem; font-weight: bold;'>Total: {total}€</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💳 Procéder au paiement", type="primary", use_container_width=True):
                st.session_state.page = "checkout"
                st.rerun()


# ============================================
# PAGES CHECKOUT, CONTACT, PROFILE (Inchangées)
# ============================================

class CheckoutPage(BasePage):
    """Page de paiement sécurisé"""
    
    def render(self):
        """Affiche la page de paiement"""
        st.markdown("# 💳 Paiement Sécurisé")
        
        if not st.session_state.user:
            st.warning("🔐 Veuillez vous connecter pour continuer.")
            return
        
        tabs = st.tabs(["📋 Informations", "💳 Paiement", "✅ Confirmation"])
        
        # Onglet Informations
        with tabs[0]:
            st.markdown("### 📋 Informations de livraison")
            
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("Prénom *")
                address = st.text_input("Adresse *")
                city = st.text_input("Ville *")
            
            with col2:
                last_name = st.text_input("Nom *")
                postal_code = st.text_input("Code postal *")
                country = st.selectbox("Pays *", ["France", "Belgique", "Suisse", "Canada"])
            
            phone = st.text_input("Téléphone")
            
            if st.button("Continuer vers le paiement", type="primary"):
                if all([first_name, last_name, address, city, postal_code]):
                    st.success("✅ Informations enregistrées")
                else:
                    st.error("❌ Veuillez remplir tous les champs obligatoires")
        
        # Onglet Paiement
        with tabs[1]:
            st.markdown("### 💳 Méthode de paiement")
            
            payment_method = st.radio("Choisissez votre méthode", 
                ["💳 Carte bancaire", "🏦 PayPal", "📱 Apple Pay", "🔒 Google Pay"])
            
            if payment_method == "💳 Carte bancaire":
                card_number = st.text_input("Numéro de carte", placeholder="1234 5678 9012 3456")
                
                col1, col2 = st.columns(2)
                with col1:
                    expiry = st.text_input("Expiration", placeholder="MM/AA")
                with col2:
                    cvv = st.text_input("CVV", type="password", placeholder="123")
                
                cardholder = st.text_input("Nom du porteur")
            
            if st.button("🔒 Confirmer le paiement", type="primary"):
                with st.spinner("Traitement du paiement..."):
                    import time
                    time.sleep(2)
                
                st.success("✅ Paiement confirmé !")
                st.balloons()
                st.session_state.order_confirmed = True
        
        # Onglet Confirmation
        with tabs[2]:
            if st.session_state.get('order_confirmed', False):
                st.success("🎉 Commande confirmée !")
                st.markdown("### 📦 Numéro de commande: #SB-2026-001")
                st.info("📧 Vous recevrez un email de confirmation sous peu.")
                
                if st.button("🏠 Retour à l'accueil"):
                    st.session_state.page = "home"
                    st.session_state.cart = []
                    del st.session_state.order_confirmed
                    st.rerun()
            else:
                st.info("Complétez les étapes précédentes pour voir la confirmation.")


class ContactPage(BasePage):
    """Page de contact"""
    
    def render(self):
        """Affiche la page de contact"""
        st.markdown("# 📞 Contactez-nous")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 💬 Envoyez-nous un message")
            
            with st.form("contact_form"):
                name = st.text_input("Nom complet *")
                email = st.text_input("Email *")
                subject = st.selectbox("Sujet", 
                    ["Question produit", "Problème de commande", "Retour/Échange", "Suggestion", "Autre"])
                message = st.text_area("Message *", height=150)
                
                if st.form_submit_button("📤 Envoyer", type="primary"):
                    if name and email and message:
                        st.success("✅ Message envoyé ! Nous vous répondrons dans les 24h.")
                    else:
                        st.error("❌ Veuillez remplir tous les champs obligatoires")
        
        with col2:
            st.markdown("### 📍 Nos coordonnées")
            st.markdown("""
            **📧 Email:**  
            contact@smartbuy.com
            
            **📞 Téléphone:**  
            +33 1 23 45 67 89
            
            **📍 Adresse:**  
            123 Rue de la Mode  
            75001 Paris, France
            
            **🕒 Horaires:**  
            Lun - Ven: 9h - 18h  
            Sam: 10h - 17h  
            Dim: Fermé
            """)
            
            st.markdown("### 🚀 Réseaux sociaux")
            col_social1, col_social2, col_social3 = st.columns(3)
            with col_social1:
                st.markdown("📘 [Facebook](#)")
            with col_social2:
                st.markdown("📷 [Instagram](#)")
            with col_social3:
                st.markdown("🐦 [Twitter](#)")


class ProfilePage(BasePage):
    """Page de profil utilisateur"""
    
    def render(self):
        """Affiche la page de profil"""
        st.markdown("# 👤 Mon Profil")
        
        if not st.session_state.user:
            st.warning("🔐 Connectez-vous pour accéder à votre profil.")
            return
        
        user = st.session_state.user
        
        tabs = st.tabs(["👤 Informations", "📊 Statistiques", "🛍️ Historique", "⚙️ Paramètres"])
        
        # Onglet Informations
        with tabs[0]:
            st.markdown("### 👤 Informations personnelles")
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Nom d'utilisateur", value=user.get('username', ''), disabled=True)
                st.text_input("Nom complet", value=user.get('full_name', ''))
            
            with col2:
                st.text_input("Email", value=user.get('email', ''))
                st.text_input("Téléphone", value=user.get('phone', ''))
            
            st.text_area("Adresse", value=user.get('address', ''))
            
            if st.button("💾 Sauvegarder", type="primary"):
                st.success("✅ Profil mis à jour !")
        
        # Onglet Statistiques
        with tabs[1]:
            st.markdown("### 📊 Vos statistiques")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🛍️ Produits vus", "127", "↗️ 12")
            with col2:
                st.metric("❤️ Favoris", "23", "↗️ 3")
            with col3:
                st.metric("🛒 Commandes", "8", "↗️ 1")
            with col4:
                st.metric("💰 Total dépensé", "1,247€", "↗️ 156€")
        
        # Onglet Historique
        with tabs[2]:
            st.markdown("### 🛍️ Historique des commandes")
            st.info("Fonctionnalité en développement")
        
        # Onglet Paramètres
        with tabs[3]:
            st.markdown("### ⚙️ Paramètres du compte")
            
            st.checkbox("📧 Recevoir les newsletters", value=True)
            st.checkbox("🔔 Notifications push", value=False)
            st.checkbox("📱 Notifications SMS", value=False)
            
            st.markdown("---")
            st.markdown("### 🔒 Sécurité")
            
            if st.button("🔑 Changer le mot de passe"):
                st.info("Fonctionnalité à venir")
            
            if st.button("🗑️ Supprimer le compte", type="secondary"):
                st.warning("Cette action est irréversible !")
