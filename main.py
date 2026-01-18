import streamlit as st
from datetime import datetime
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Foyer Magique 🏡", page_icon="✨", layout="centered")

# Style CSS pour une interface ludique
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .mission-card {
        background: white; border-radius: 15px; padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 8px solid #FFD700;
        margin-bottom: 15px;
    }
    .pts-tag { float: right; font-weight: bold; color: #4CAF50; background: #e8f5e9; padding: 2px 8px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# Initialisation du score global dans la session
if 'points_foyer' not in st.session_state:
    st.session_state.points_foyer = 0

st.title("🏡 Le Foyer Magique")

# --- SÉLECTION DU PROFIL ---
user = st.selectbox("Qui es-tu aujourd'hui ?", ["Papa", "Maman", "Ados", "Enfant 1", "Enfant 2"])

# --- STRUCTURE DES MISSIONS ---
# Catégories : 'Enfant', 'Ado/Parent', 'Parent'
missions_data = [
    # MISSIONS ENFANTS
    {"nom": "🚀 Mission Décollage", "desc": "Faire son lit et ranger son pyjama", "pts": 10, "freq": "Quotidien", "cat": "Enfant"},
    {"nom": "🦷 Sourire de Star", "desc": "Brossage de dents (sans rouspéter)", "pts": 5, "freq": "2x / jour", "cat": "Enfant"},
    {"nom": "🍽️ Maître du Couvert", "desc": "Mettre la table proprement", "pts": 10, "freq": "Chaque repas", "cat": "Enfant"},
    {"nom": "🧼 Ranger l'assiette", "desc": "Débarrasser la table", "pts": 10, "freq": "Chaque repas", "cat": "Enfant"},
    {"nom": "🧸 Magicien du Salon", "desc": "Ranger les jouets éparpillés", "pts": 15, "freq": "Quotidien", "cat": "Enfant"},
    {"nom": "🏰 Gardien de la Chambre", "desc": "Ranger sa chambre à fond", "pts": 25, "freq": "Hebdomadaire", "cat": "Enfant"},
    
    # MISSIONS ADOS / PARENTS
    {"nom": "🗑️ Alerte Déchets", "desc": "Sortir les poubelles (Lundi ou Mercredi soir)", "pts": 20, "freq": "1 sem / 2", "cat": "Ado/Parent"},
    {"nom": "🌀 Tornade Aspirateur", "desc": "Passer l'aspirateur au rez-de-chaussée", "pts": 15, "freq": "2x / semaine", "cat": "Ado/Parent"},
    {"nom": "✨ Miroir d'Eau", "desc": "Passer la serpillière en bas", "pts": 20, "freq": "Hebdomadaire", "cat": "Ado/Parent"},
    {"nom": "📦 Lutin du Recyclage", "desc": "Vider les petites poubelles intérieures", "pts": 10, "freq": "Si nécessaire", "cat": "Ado/Parent"},
    {"nom": "🍽️ Plongeur d'élite", "desc": "Faire la vaisselle", "pts": 15, "freq": "Si nécessaire", "cat": "Ado/Parent"},
    {"nom": "🏎️ Car Wash Privé", "desc": "Laver la voiture familiale", "pts": 40, "freq": "Mensuel", "cat": "Ado/Parent"},
    {"nom": "🚜 Maître de la Jungle", "desc": "Tondre la pelouse (Saisonnier)", "pts": 40, "freq": "1 sem / 2 (Eté)", "cat": "Ado/Parent"},
    {"nom": "👟 Gardien du Hall", "desc": "Aligner les chaussures dans l'entrée", "pts": 5, "freq": "Quotidien", "cat": "Ado/Parent"},
    {"nom": "🧺 Expert du Linge", "desc": "Plier une panière de linge propre", "pts": 15, "freq": "Si nécessaire", "cat": "Ado/Parent"},

    # MISSIONS PARENTS UNIQUEMENT
    {"nom": "🍳 Chef Étoilé", "desc": "Cuisiner un bon repas", "pts": 20, "freq": "Quotidien", "cat": "Parent"},
    {"nom": "🛁 Opération Éclat", "desc": "Nettoyer les WC Haut et Bas", "pts": 30, "freq": "Hebdomadaire", "cat": "Parent"},
    {"nom": "⚡ Micro-Onde Brillant", "desc": "Laver l'intérieur du micro-onde", "pts": 15, "freq": "1 sem / 2", "cat": "Parent"},
    {"nom": "🌬️ Chasse à la Poussière", "desc": "Faire les poussières en bas", "pts": 10, "freq": "1 sem / 2", "cat": "Parent"},
    {"nom": "🏰 Grand Nettoyage", "desc": "Haut : Aspi + Serpi + Poussière + SdB", "pts": 40, "freq": "1 sem / 2", "cat": "Parent"},
    {"nom": "🧊 Frigo comme Neuf", "desc": "Nettoyage complet du réfrigérateur", "pts": 20, "freq": "Mensuel", "cat": "Parent"},
    {"nom": "🔥 Mission Pyrolyse", "desc": "Laver le four", "pts": 50, "freq": "Mensuel", "cat": "Parent"},
    {"nom": "💎 Vue Cristalline", "desc": "Nettoyer les vitres", "pts": 50, "freq": "Tous les 2 mois", "cat": "Parent"}
]

# --- AFFICHAGE DU SCORE ---
st.sidebar.header("🏆 Trésor du Foyer")
st.sidebar.metric("Points cumulés", f"{st.session_state.points_foyer} pts")
st.sidebar.progress(min(st.session_state.points_foyer / 500, 1.0))
st.sidebar.write("Objectif : 500 pts pour une surprise !")

# --- FILTRAGE DES MISSIONS ---
if user in ["Enfant 1", "Enfant 2"]:
    ma_liste = [m for m in missions_data if m['cat'] == "Enfant"]
elif user == "Ados":
    ma_liste = [m for m in missions_data if m['cat'] == "Ado/Parent"]
else: # Parents
    ma_liste = [m for m in missions_data if m['cat'] in ["Parent", "Ado/Parent"]]

# --- AFFICHAGE DES CARTES ---
st.subheader(f"Missions pour {user} :")

for m in ma_liste:
    with st.container():
        st.markdown(f"""
        <div class="mission-card">
            <span class="pts-tag">+{m['pts']} pts</span>
            <div style="font-size: 0.8em; color: gray;">{m['freq']}</div>
            <strong style="font-size: 1.1em;">{m['nom']}</strong><br>
            <span style="color: #555;">{m['desc']}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Valider : {m['nom']}", key=m['nom']):
            st.session_state.points_foyer += m['pts']
            st.balloons()
            st.success(f"Bravo {user} ! Tu as gagné {m['pts']} points.")
            st.rerun()