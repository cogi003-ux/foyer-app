import streamlit as st
import pandas as pd

# --- CONFIGURATION SÉCURITÉ ---
PIN_PARENT = "1234" 

st.set_page_config(page_title="Foyer Magique 🏡", page_icon="✨", layout="wide")

# --- INITIALISATION ---
if 'config' not in st.session_state:
    st.session_state.config = {"parents": ["Papa", "Maman"], "ados": ["Ado 1"], "enfants": ["Enfant 1", "Enfant 2"]}
if 'points_foyer' not in st.session_state:
    st.session_state.points_foyer = 0
if 'attente_validation' not in st.session_state:
    st.session_state.attente_validation = []
if 'parent_authenticated' not in st.session_state:
    st.session_state.parent_authenticated = False
if 'classement' not in st.session_state:
    st.session_state.classement = {}
if 'achats_en_attente' not in st.session_state:
    st.session_state.achats_en_attente = []

# --- STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .mission-card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 6px solid #FFD700; margin-bottom: 10px; }
    .reward-card { background: white; border-radius: 12px; padding: 15px; border-top: 5px solid #FF4B4B; text-align: center; margin-bottom: 5px; }
    .category-header { background: #343a40; color: white; padding: 8px 15px; border-radius: 8px; margin-top: 20px; font-weight: bold; text-transform: uppercase; }
    .pts-badge { float: right; color: #28a745; font-weight: bold; margin-left: 10px; }
    .freq-badge { float: right; color: #FF4B4B; font-size: 0.8em; font-weight: bold; background: #ffebee; padding: 2px 6px; border-radius: 4px; }
    .desc-text { font-size: 0.85em; color: #666; margin-top: 4px; display: block; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
mode = st.sidebar.radio("Menu", ["🚀 Missions", "🏆 Classement", "🎁 Boutique", "⚙️ Gérer & Valider"])
st.sidebar.divider()
st.sidebar.metric("💰 Trésor Commun", f"{st.session_state.points_foyer} pts")

if st.sidebar.button("🔒 Verrouiller l'accès Parent"):
    st.session_state.parent_authenticated = False
    st.rerun()

# 1. GESTION
if mode == "⚙️ Gérer & Valider":
    if not st.session_state.parent_authenticated:
        pin = st.text_input("PIN Parent :", type="password")
        if pin == PIN_PARENT:
            st.session_state.parent_authenticated = True
            st.rerun()
        st.stop()
    
    st.title("🛡️ Espace Parents")
    col_v, col_a = st.columns(2)
    with col_v:
        st.subheader("✅ Missions à confirmer")
        if not st.session_state.attente_validation: st.info("Rien à valider.")
        for idx, d in enumerate(st.session_state.attente_validation):
            if st.button(f"Valider {d['user']} : {d['task']}", key=f"v_{idx}"):
                st.session_state.points_foyer += d['pts']
                st.session_state.classement[d['user']] = st.session_state.classement.get(d['user'], 0) + d['pts']
                st.session_state.attente_validation.pop(idx)
                st.rerun()
    with col_a:
        st.subheader("🎁 Achats à livrer")
        if not st.session_state.achats_en_attente: st.info("Aucun achat.")
        for idx, a in enumerate(st.session_state.achats_en_attente):
            if st.button(f"Livrer {a['item']} à {a['user']}", key=f"l_{idx}"):
                st.session_state.achats_en_attente.pop(idx)
                st.rerun()

# 2. CLASSEMENT
elif mode == "🏆 Classement":
    st.title("🏆 Tableau d'Honneur")
    if st.session_state.classement:
        df = pd.DataFrame(list(st.session_state.classement.items()), columns=['Héros', 'Points']).sort_values(by='Points', ascending=False)
        st.table(df)

# 3. BOUTIQUE
elif mode == "🎁 Boutique":
    st.title("🎁 La Boutique")
    user_list = st.session_state.config["parents"] + st.session_state.config["ados"] + st.session_state.config["enfants"]
    shopper = st.selectbox("Qui fait ses courses ?", user_list)
    pts = st.session_state.classement.get(shopper, 0)
    st.metric("Tes points disponibles", f"{pts} pts")

    recompenses = [
        {"item": "📺 30 min d'écran", "prix": 50},
        {"item": "🍦 Dessert au choix", "prix": 30},
        {"item": "🎬 Soirée Cinéma", "prix": 100},
        {"item": "🍕 Menu Pizza", "prix": 150}
    ]

    c1, c2 = st.columns(2)
    for i, r in enumerate(recompenses):
        with (c1 if i % 2 == 0 else c2):
            st.markdown(f"<div class='reward-card'><b>{r['item']}</b><br>💰 {r['prix']} pts</div>", unsafe_allow_html=True)
            if st.button(f"Acheter {r['item']}", key=f"buy_{i}"):
                if pts >= r['prix']:
                    st.session_state.classement[shopper] -= r['prix']
                    st.session_state.achats_en_attente.append({"user": shopper, "item": r['item']})
                    st.success("Demande envoyée !")
                else: st.error("Pas assez de points !")

# 4. MISSIONS
else:
    all_users = st.session_state.config["parents"] + st.session_state.config["ados"] + st.session_state.config["enfants"]
    current_user = st.selectbox("Qui es-tu ?", all_users)
    is_parent = current_user in st.session_state.config["parents"]
    
    if is_parent and not st.session_state.parent_authenticated:
        p = st.text_input("PIN Parent requis :", type="password")
        if p == PIN_PARENT:
            st.session_state.parent_authenticated = True
            st.rerun()
        st.stop()

    tasks = [
        # CUISINE
        {"n": "🍳 Chef Étoilé", "p": 20, "f": "1x/j", "c": "Cuisine", "r": ["Parent"], "d": "Préparer un bon repas."},
        {"n": "🍽️ Maître du Couvert", "p": 10, "f": "Repas", "c": "Cuisine", "r": ["Enfant"], "d": "Mettre la table."},
        {"n": "🧼 Ranger l'assiette", "p": 10, "f": "Repas", "c": "Cuisine", "r": ["Enfant"], "d": "Débarrasser la table."},
        {"n": "🍽️ Plongeur d'élite", "p": 15, "f": "Besoin", "c": "Cuisine", "r": ["Parent", "Ado"], "d": "Vaisselle ou lave-vaisselle."},
        {"n": "⚡ Micro-Onde Brillant", "p": 15, "f": "1 sem/2", "c": "Cuisine", "r": ["Parent"], "d": "Laver l'intérieur."},
        {"n": "🧊 Frigo comme Neuf", "p": 20, "f": "1x/mois", "c": "Cuisine", "r": ["Parent"], "d": "Nettoyer l'intérieur."},
        {"n": "🔥 Mission Pyrolyse", "p": 50, "f": "1x/mois", "c": "Cuisine", "r": ["Parent"], "d": "Laver le four."},
        # MÉNAGE
        {"n": "🌀 Tornade Aspirateur", "p": 15, "f": "2x/sem", "c": "Ménage", "r": ["Parent", "Ado"], "d": "Aspirateur tout le bas."},
        {"n": "✨ Miroir d'Eau", "p": 20, "f": "1x/sem", "c": "Ménage", "r": ["Parent", "Ado"], "d": "Serpillière en bas."},
        {"n": "🌬️ Chasse à la Poussière", "p": 10, "f": "1 sem/2", "c": "Ménage", "r": ["Parent"], "d": "Poussières en bas."},
        {"n": "🏰 Grand Nettoyage", "p": 40, "f": "1 sem/2", "c": "Ménage", "r": ["Parent"], "d": "Haut : Aspi+Serpi+Poussière+SdB."},
        {"n": "🧸 Magicien du Salon", "p": 15, "f": "1x/j", "c": "Ménage", "r": ["Enfant"], "d": "Ramasser tous les jouets."},
        {"n": "🚀 Mission Décollage", "p": 10, "f": "1x/j", "c": "Ménage", "r": ["Enfant"], "d": "Faire son lit et ranger son pyjama."},
        {"n": "🏰 Gardien de la Chambre", "p": 25, "f": "1x/sem", "c": "Ménage", "r": ["Enfant"], "d": "Ranger sa chambre à fond."},
        {"n": "🧺 Expert du Linge", "p": 15, "f": "Besoin", "c": "Ménage", "r": ["Parent", "Ado"], "d": "Plier le linge propre."},
        {"n": "👟 Gardien du Hall", "p": 5, "f": "1x/j", "c": "Ménage", "r": ["Parent", "Ado", "Enfant"], "d": "Ranger les chaussures."},
        # HYGIÈNE & DÉCHETS
        {"n": "🦷 Sourire de Star", "p": 5, "f": "2x/j", "c": "Hygiène", "r": ["Enfant"], "d": "Brossage de dents complet."},
        {"n": "🚿 Éclat Sanitaire", "p": 30, "f": "1x/sem", "c": "Hygiène", "r": ["Parent"], "d": "Laver les WC."},
        {"n": "🗑️ Alerte Déchets", "p": 20, "f": "Lun/Mer", "c": "Déchets", "r": ["Parent", "Ado"], "d": "Sortir les poubelles extérieures."},
        {"n": "📦 Lutin du Recyclage", "p": 10, "f": "Besoin", "c": "Déchets", "r": ["Parent", "Ado", "Enfant"], "d": "Vider les poubelles intérieures."},
        # EXTÉRIEUR
        {"n": "🚜 Maître de la Jungle", "p": 40, "f": "1 sem/2", "c": "Extérieur", "r": ["Parent", "Ado"], "d": "Tondre la pelouse."},
        {"n": "🏎️ Car Wash Privé", "p": 40, "f": "1x/mois", "c": "Extérieur", "r": ["Parent", "Ado"], "d": "Laver l'extérieur de la voiture."},
        {"n": "💎 Vue Cristalline", "p": 50, "f": "2 mois", "c": "Extérieur", "r": ["Parent"], "d": "Laver toutes les fenêtres."}
    ]

    pending = [d['task'] for d in st.session_state.attente_validation if d['user'] == current_user]
    role = "Parent" if is_parent else "Ado" if current_user in st.session_state.config["ados"] else "Enfant"

    for cat in ["Cuisine", "Ménage", "Hygiène", "Déchets", "Extérieur"]:
        cat_t = [t for t in tasks if t["c"] == cat and role in t["r"]]
        if cat_t:
            st.markdown(f"<div class='category-header'>{cat}</div>", unsafe_allow_html=True)
            for t in cat_t:
                col_i, col_b = st.columns([5, 1.5])
                with col_i: 
                    st.markdown(f"""
                        <div class='mission-card'>
                            <span class='pts-badge'>+{t['p']} pts</span>
                            <span class='freq-badge'>🗓️ {t['f']}</span>
                            <b>{t['n']}</b><br>
                            <span class='desc-text'>📝 {t['d']}</span>
                        </div>""", unsafe_allow_html=True)
                with col_b:
                    st.write("")
                    if t['n'] in pending: st.button("⌛ Attente", key=f"p_{t['n']}_{current_user}", disabled=True)
                    else:
                        label = "Valider ✅" if is_parent else "Fini ! 🚀"
                        if st.button(label, key=f"f_{t['n']}_{current_user}"):
                            if is_parent:
                                st.session_state.points_foyer += t['p']
                                st.session_state.classement[current_user] = st.session_state.classement.get(current_user, 0) + t['p']
                            else: st.session_state.attente_validation.append({"user": current_user, "task": t['n'], "pts": t['p']})
                            st.rerun()