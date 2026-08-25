import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="BiblioTech",
    page_icon="📚",
    layout="wide"
)

st.title("📚 BiblioTech")
st.subheader("Système de recommandation de livres")


# =========================
# Sidebar
# =========================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Accueil",
        "Créer un compte",
        "Rechercher un livre",
        "Noter un livre",
        "Mes recommandations"
    ]
)


# =========================
# Accueil
# =========================

if menu == "Accueil":

    st.markdown("""
    ## Bienvenue sur BiblioTech

    Cette application permet :
    - de rechercher des livres par titre ou auteur ;
    - de découvrir des livres similaires ;
    - d'obtenir des recommandations personnalisées ;
    - d'ajouter des notes ;
    - d'améliorer progressivement le moteur de recommandation.
    """)


# =========================
# Création utilisateur
# =========================

elif menu == "Créer un compte":

    st.header("Créer un compte")

    username = st.text_input("Nom d'utilisateur")
    email = st.text_input("Email")

    age = st.number_input(
        "Âge",
        min_value=10,
        max_value=100,
        step=1
    )

    country = st.text_input("Pays")

    if st.button("Créer le compte"):

        payload = {
            "username": username,
            "email": email,
            "age": age,
            "country": country
        }

        try:
            response = requests.post(
                f"{API_URL}/users",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:

                data = response.json()

                st.success("Compte créé avec succès")

                st.write(
                    f"Votre identifiant utilisateur est : "
                    f"**{data['user']['app_user_id']}**"
                )

            else:
                try:
                    st.error(response.json())

                except ValueError:
                    st.error(
                        f"Erreur API {response.status_code} : "
                        f"{response.text}"
                    )

        except requests.RequestException as e:
            st.error(
                f"Impossible de contacter l'API : {e}"
            )


# =========================
# Recherche de livres
# =========================

elif menu == "Rechercher un livre":

    st.header("🔎 Rechercher un livre")

    query = st.text_input(
        "Titre ou auteur",
        placeholder="Ex. 1984, Harry Potter, Stephen King..."
    )

    top_n = st.slider(
        "Nombre de recommandations",
        min_value=1,
        max_value=20,
        value=5
    )

    if query:

        try:
            response = requests.get(
                f"{API_URL}/books/search",
                params={
                    "q": query,
                    "limit": 20
                },
                timeout=10
            )

            if response.status_code == 200:

                results = response.json()["results"]

                if not results:
                    st.warning("Aucun livre trouvé.")

                else:
                    st.write(
                        f"**{len(results)} livre(s) trouvé(s)**"
                    )

                    # On conserve maintenant le book_key
                    # et non plus l'ISBN.
                    options = {
                        (
                            f"{book['title']} — "
                            f"{book['author']} "
                            f"({book['year_of_publication'] or 'année inconnue'})"
                        ): book
                        for book in results
                    }

                    # Sélection du livre
                    selected_label = st.selectbox(
                        "Sélectionne un livre",
                        options.keys()
                    )

                    selected_book = options[selected_label]
                    selected_book_key = selected_book["book_key"]

                    # Affichage du livre sélectionné
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        image_url = selected_book.get("image_url_m")

                        if image_url:
                            image_url = image_url.replace(
                                "http://",
                                "https://",
                                1
                            )

                            st.image(
                                image_url,
                                width=180
                            )
                        else:
                            st.info("Couverture indisponible")
                       

                    with col2:
                        st.markdown(
                            f"""
                            ### 📖 {selected_book['title']}

                            **Auteur :** {selected_book['author']}  
                            **Année :** {selected_book['year_of_publication'] or 'Inconnue'}  
                            **Éditeur :** {selected_book['publisher'] or 'Inconnu'}
                            """
                        )

                    if st.button(
                        "Recommander à partir de ce livre"
                    ):

                        # Nouvelle API :
                        # GET /recommend/book?book_key=...
                        reco_response = requests.get(
                            f"{API_URL}/recommend/book",
                            params={
                                "book_key": selected_book_key,
                                "top_n": top_n
                            },
                            timeout=10
                        )

                        if reco_response.status_code == 200:

                            data = reco_response.json()

                            st.success(
                                "Recommandations générées"
                            )

                            st.subheader(
                                "Livres similaires"
                            )

                            for reco in data["recommendations"]:

                                st.markdown(
                                    f"""
                                    ### 📚 {reco['title']}

                                    **Auteur :** {reco['author']}  
                                    **Score de similarité :** {reco['similarity_score']}
                                    """
                                )

                                st.divider()

                        elif reco_response.status_code == 404:

                            st.warning(
                                "Ce livre n'est pas encore présent "
                                "dans le modèle de recommandation."
                            )

                        else:
                            try:
                                st.error(
                                    reco_response.json()
                                )

                            except ValueError:
                                st.error(
                                    f"Erreur API "
                                    f"{reco_response.status_code} : "
                                    f"{reco_response.text}"
                                )

            else:
                try:
                    st.error(response.json())

                except ValueError:
                    st.error(
                        f"Erreur API {response.status_code} : "
                        f"{response.text}"
                    )

        except requests.RequestException as e:
            st.error(
                f"Impossible de contacter l'API : {e}"
            )


# =========================
# Ajouter une note
# =========================

elif menu == "Noter un livre":

    st.header("⭐ Noter un livre")

    app_user_id = st.number_input(
        "Votre identifiant utilisateur",
        min_value=1,
        step=1
    )

    query = st.text_input(
        "Rechercher le livre à noter",
        placeholder="Titre ou auteur..."
    )

    if query:

        try:
            response = requests.get(
                f"{API_URL}/books/search",
                params={
                    "q": query,
                    "limit": 20
                },
                timeout=10
            )

            if response.status_code == 200:

                results = response.json()["results"]

                if results:

                    options = {
                        (
                            f"{book['title']} — "
                            f"{book['author']}"
                        ): book["book_key"]
                        for book in results
                    }

                    selected_label = st.selectbox(
                        "Sélectionne le livre",
                        list(options.keys()),
                        key="rating_book"
                    )

                    selected_book_key = (
                        options[selected_label]
                    )

                    rating = st.slider(
                        "Note",
                        min_value=1,
                        max_value=10,
                        value=5
                    )

                    if st.button(
                        "Enregistrer la note"
                    ):

                        payload = {
                            "app_user_id": app_user_id,
                            "book_key": selected_book_key,
                            "rating": rating
                        }

                        rating_response = requests.post(
                            f"{API_URL}/ratings",
                            json=payload,
                            timeout=10
                        )

                        if rating_response.status_code == 200:

                            st.success(
                                "Note enregistrée avec succès"
                            )

                        else:
                            try:
                                st.error(
                                    rating_response.json()
                                )

                            except ValueError:
                                st.error(
                                    f"Erreur API "
                                    f"{rating_response.status_code} : "
                                    f"{rating_response.text}"
                                )

                else:
                    st.warning(
                        "Aucun livre trouvé."
                    )

            else:
                try:
                    st.error(response.json())

                except ValueError:
                    st.error(
                        f"Erreur API {response.status_code} : "
                        f"{response.text}"
                    )

        except requests.RequestException as e:
            st.error(
                f"Impossible de contacter l'API : {e}"
            )


# =========================
# Recommandations utilisateur
# =========================

elif menu == "Mes recommandations":

    st.header("✨ Mes recommandations")

    app_user_id = st.number_input(
        "Votre identifiant utilisateur",
        min_value=1,
        step=1
    )

    top_n = st.slider(
        "Nombre de recommandations",
        min_value=1,
        max_value=20,
        value=5,
        key="user_top_n"
    )

    if st.button(
        "Obtenir mes recommandations"
    ):

        try:
            response = requests.get(
                f"{API_URL}/recommend/user/{app_user_id}",
                params={
                    "top_n": top_n
                },
                timeout=10
            )

            if response.status_code == 200:

                data = response.json()

                st.success(
                    "Recommandations générées"
                )

                for reco in data["recommendations"]:

                    st.markdown(
                        f"""
                        ### 📚 {reco['title']}

                        **Auteur :** {reco['author']}  
                        **Score :** {reco['similarity_score']}
                        """
                    )

                    st.divider()

            elif response.status_code == 404:

                try:
                    detail = response.json().get(
                        "detail",
                        "Aucune recommandation disponible."
                    )

                    st.warning(detail)

                except ValueError:
                    st.warning(
                        "Aucune recommandation disponible."
                    )

            else:
                try:
                    st.error(response.json())

                except ValueError:
                    st.error(
                        f"Erreur API {response.status_code} : "
                        f"{response.text}"
                    )

        except requests.RequestException as e:
            st.error(
                f"Impossible de contacter l'API : {e}"
            )