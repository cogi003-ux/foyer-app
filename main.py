import streamlit as st

st.set_page_config(page_title="Foyer Magique", page_icon="✨")

# Style pour que ça ressemble à un jeu mobile
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .mission-card {
        background: white; border-radius: 20px; padding: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-left: 10px solid #FFD700;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Missions de Super-Héros")

# --- BARRE DE PROGRESSION VERS LE CADEAU ---
# On simule un trésor de 25 points pour commencer
if 'points' not in st.session_state: st.session_state.points = 25

st.header("🏆 Objectif : Sortie Cinéma")
objectif = 100
progression = min(st.session_state.points / objectif, 1.0)

st.progress(progression)
st.subheader(f"🌟 {st.session_state.points} / {objectif} Points")
st.caption(f"Encore {max(0, objectif - st.session_state.points)} points pour gagner la surprise !")

# --- LISTE DES MISSIONS ---
missions = [
    {"nom": "🍽️ Chef de Table", "desc": "Mettre le couvert proprement", "pts": 10},
    {"nom": "🧸 Magicien du Salon", "desc": "Ranger tous les jouets éparpillés", "pts": 15},
    {"nom": "🚀 Mission Décollage", "desc": "Faire son lit et ranger son pyjama", "pts": 10},
    {"nom": "🦷 Sourire de Star", "desc": "Brossage de dents sans rappel", "pts": 5}
]

st.write("### Tes missions du jour :")

for m in missions:
    with st.container():
        st.markdown(f"""
        <div class="mission-card">
            <span style="float:right; font-weight:bold; color:#FFD700;">+{m['pts']} pts</span>
            <h3>{m['nom']}</h3>
            <p>{m['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Mission {m['nom']} accomplie !", key=m['nom']):
            st.session_state.points += m['pts']
            st.balloons()
            st.success(f"Bravo ! Ton trésor grandit de {m['pts']} points !")
            st.rerun()