import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Foyer App", layout="centered")

# --- FICHIER DE SAUVEGARDE ---
DB_FILE = "foyer_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).to_dict('records')
    return [
        {"tâche": "Mettre le couvert", "points": 5, "statut": "À faire"},
        {"tâche": "Ranger la chambre", "points": 10, "statut": "À faire"}
    ]

if 'tasks' not in st.session_state:
    st.session_state.tasks = load_data()
if 'solde' not in st.session_state:
    st.session_state.solde = sum(t['points'] for t in st.session_state.tasks if t['statut'] == "Terminé")

# --- INTERFACE ---
st.title("🏠 Notre Foyer")

user = st.selectbox("Qui utilise l'app ?", ["Papa", "Maman", "Enfant 1"])

tab1, tab2 = st.tabs(["📋 Tâches", "🎁 Boutique"])

with tab1:
    st.subheader("Tâches du jour")
    for i, t in enumerate(st.session_state.tasks):
        if t['statut'] != "Terminé":
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{t['tâche']}** ({t['points']} pts)")
            if col2.button("Fait", key=f"t_{i}"):
                st.session_state.tasks[i]['statut'] = "Terminé"
                st.session_state.solde += t['points']
                pd.DataFrame(st.session_state.tasks).to_csv(DB_FILE, index=False)
                st.rerun()

with tab2:
    st.subheader("Boutique de récompenses")
    st.metric("Votre Solde", f"{st.session_state.solde} pts")
    
    recompenses = {"30 min de Console": 50, "Dessert au choix": 30, "Petit jouet": 100}
    
    for item, prix in recompenses.items():
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{item}**")
        if col2.button(f"{prix} pts", key=item):
            if st.session_state.solde >= prix:
                st.session_state.solde -= prix
                st.success(f"Bravo ! Tu as acheté : {item}")
            else:
                st.error("Pas assez de points !")