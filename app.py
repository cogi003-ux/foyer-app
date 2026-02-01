from flask import Flask, render_template, request, jsonify
import datetime
import os
from dotenv import load_dotenv
load_dotenv()
from database import (
    get_all_taches, add_tache as add_tache_db, delete_tache as delete_tache_db, update_tache_db,
    get_all_messages, add_message as add_message_db, delete_message as delete_message_db,
    get_config_famille, update_config_famille, verify_parent_pin,
    add_tache_completee, get_taches_completees,
    add_attente_validation, get_attente_validation, delete_attente_validation,
    get_classement, update_classement,
    get_recompenses_personnalisees, add_recompense_personnalisee,
    get_recompenses_achetees, add_recompense_achetee
)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Vérifier que les variables d'environnement sont bien chargées
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n" + "="*50)
    print("❌ ERREUR : Clés Supabase introuvables dans les variables d'environnement")
    print("="*50)
    print("Assurez-vous que SUPABASE_URL et SUPABASE_KEY sont définies :")
    print("  - Dans le fichier .env (développement local)")
    print("  - Dans le tableau de bord Render (production)")
    print("="*50 + "\n")
    import sys
    sys.exit(1)
else:
    print(f"✅ Supabase connecté : {SUPABASE_URL[:20]}...")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/sw.js')
def service_worker():
    return app.send_static_file('sw.js'), 200, {'Content-Type': 'application/javascript'}

@app.route('/static/manifest.json')
def manifest():
    return app.send_static_file('manifest.json'), 200, {'Content-Type': 'application/json'}

# API pour les tâches
@app.route('/api/taches', methods=['GET'])
def get_taches():
    try:
        taches = get_all_taches()
        return jsonify({
            'taches': taches,
            'success': True
        })
    except Exception as e:
        print(f"[ERROR] Erreur lors du chargement des tâches: {e}")
        return jsonify({
            'taches': [],
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/taches', methods=['POST'])
def add_tache():
    try:
        if not request.json:
            return jsonify({'success': False, 'error': 'Aucune donnée reçue'}), 400
        
        data = request.json
        
        # Validation des données requises
        if 'nom' not in data or not data['nom'].strip():
            return jsonify({'success': False, 'error': 'Le nom de la tâche est requis'}), 400
        
        # Valider qu'il y a au moins un responsable (ancien ou nouveau format)
        has_responsable = 'responsable' in data and data.get('responsable', '').strip()
        has_responsables = 'responsables' in data and data.get('responsables')
        if isinstance(has_responsables, list):
            has_responsables = len([r for r in has_responsables if r and str(r).strip()]) > 0
        
        if not has_responsable and not has_responsables:
            return jsonify({'success': False, 'error': 'Au moins un responsable est requis'}), 400
        
        if 'statut' not in data:
            return jsonify({'success': False, 'error': 'Le statut est requis'}), 400
        
        # Validation du statut
        if data['statut'] not in ['a_faire', 'en_cours', 'en_attente', 'termine']:
            return jsonify({'success': False, 'error': 'Statut invalide'}), 400
        
        # Validation du type
        if 'type' in data and data['type'] not in ['quotidienne', 'hebdomadaire', 'ponctuelle']:
            return jsonify({'success': False, 'error': 'Type invalide'}), 400
        
        nouvelle_tache = {
            'nom': data['nom'].strip(),
            'icone': data.get('icone', 'sparkles'),
            'responsable': data.get('responsable', '').strip() if 'responsable' in data else '',
            'responsables': data.get('responsables', []),  # Support des multiples responsables
            'type': data.get('type', 'quotidienne'),
            'points': int(data.get('points', 10)),
            'statut': data['statut']
        }
        
        success, message = add_tache_db(nouvelle_tache)
        if success:
            return jsonify({'success': True, 'message': 'Tâche ajoutée !'})
        else:
            print(f"[ERROR] Échec de l'enregistrement Supabase: {message}")
            return jsonify({'success': False, 'error': message}), 500
                
    except ValueError as e:
        print(f"[ERROR] Erreur de validation: {e}")
        return jsonify({'success': False, 'error': f'Données invalides: {str(e)}'}), 400
    except Exception as e:
        print(f"[ERROR] Erreur inattendue dans add_tache: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Erreur serveur: {str(e)}'}), 500

@app.route('/api/taches/<int:tache_id>', methods=['DELETE'])
def delete_tache(tache_id):
    success = delete_tache_db(tache_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la suppression'}), 500

@app.route('/api/taches/<int:tache_id>', methods=['PATCH'])
def update_tache(tache_id):
    try:
        if not request.json:
            return jsonify({'success': False, 'error': 'Aucune donnée reçue'}), 400
        
        data = request.json
        
        success = update_tache_db(tache_id, data)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de la mise à jour'}), 500
    except Exception as e:
        print(f"[ERROR] Erreur lors de la mise à jour: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour les messages
@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        messages = get_all_messages()
        return jsonify({
            'messages': messages,
            'success': True
        })
    except Exception as e:
        print(f"[ERROR] Erreur lors du chargement des messages: {e}")
        return jsonify({
            'messages': [],
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages', methods=['POST'])
def add_message():
    try:
        if not request.json:
            return jsonify({'success': False, 'error': 'Aucune donnée reçue'}), 400
        
        data = request.json
        
        # Validation des données requises
        if 'auteur' not in data or not data['auteur'].strip():
            return jsonify({'success': False, 'error': "L'auteur est requis"}), 400
        
        if 'texte' not in data or not data['texte'].strip():
            return jsonify({'success': False, 'error': 'Le texte du message est requis'}), 400
        
        nouveau_message = {
            'auteur': data['auteur'].strip(),
            'texte': data['texte'].strip()
        }
        
        success, message = add_message_db(nouveau_message)
        if success:
            return jsonify({'success': True, 'message': 'Message publié !'})
        else:
            print(f"[ERROR] Échec de l'enregistrement Supabase: {message}")
            return jsonify({'success': False, 'error': message}), 500
                
    except ValueError as e:
        print(f"[ERROR] Erreur de validation: {e}")
        return jsonify({'success': False, 'error': f'Données invalides: {str(e)}'}), 400
    except Exception as e:
        print(f"[ERROR] Erreur inattendue dans add_message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Erreur serveur: {str(e)}'}), 500

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    success = delete_message_db(message_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la suppression'}), 500

# API pour l'authentification parent
@app.route('/api/auth/parent', methods=['POST'])
def verify_parent():
    try:
        data = request.json
        pin = data.get('pin', '')
        if verify_parent_pin(pin):
            return jsonify({'success': True, 'authenticated': True})
        else:
            return jsonify({'success': False, 'authenticated': False, 'error': 'PIN incorrect'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour la configuration famille
@app.route('/api/config/famille', methods=['GET'])
def get_config():
    try:
        config = get_config_famille()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/famille', methods=['PUT'])
def update_config():
    try:
        data = request.json
        if update_config_famille(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de la mise à jour'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour les tâches complétées
@app.route('/api/taches-completees', methods=['GET'])
def get_taches_completees_api():
    try:
        user_name = request.args.get('user_name')
        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')
        taches = get_taches_completees(user_name, date_start, date_end)
        return jsonify({'success': True, 'taches': taches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/taches-completees', methods=['POST'])
def add_tache_completee_api():
    try:
        data = request.json
        if add_tache_completee(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'ajout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour l'attente de validation
@app.route('/api/attente-validation', methods=['GET'])
def get_attente_validation_api():
    try:
        user_name = request.args.get('user_name')
        validations = get_attente_validation(user_name)
        return jsonify({'success': True, 'validations': validations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attente-validation', methods=['POST'])
def add_attente_validation_api():
    try:
        data = request.json
        if add_attente_validation(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'ajout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attente-validation/<int:validation_id>', methods=['DELETE'])
def delete_attente_validation_api(validation_id):
    try:
        if delete_attente_validation(validation_id):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de la suppression'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour le classement
@app.route('/api/classement', methods=['GET'])
def get_classement_api():
    try:
        classement = get_classement()
        return jsonify({'success': True, 'classement': classement})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classement', methods=['POST'])
def update_classement_api():
    try:
        data = request.json
        user_name = data.get('user_name')
        points = data.get('points', 0)
        if update_classement(user_name, points):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de la mise à jour'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour les récompenses personnalisées
@app.route('/api/recompenses/personnalisees', methods=['GET'])
def get_recompenses_personnalisees_api():
    try:
        recompenses = get_recompenses_personnalisees()
        return jsonify({'success': True, 'recompenses': recompenses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recompenses/personnalisees', methods=['POST'])
def add_recompense_personnalisee_api():
    try:
        data = request.json
        if add_recompense_personnalisee(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'ajout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API pour les récompenses achetées
@app.route('/api/recompenses/achetees', methods=['GET'])
def get_recompenses_achetees_api():
    try:
        recompenses = get_recompenses_achetees()
        return jsonify({'success': True, 'recompenses': recompenses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recompenses/achetees', methods=['POST'])
def add_recompense_achetee_api():
    try:
        data = request.json
        if add_recompense_achetee(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'ajout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)