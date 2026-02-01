// Configuration
const API_BASE = '';

// État de l'application
let appData = {
    taches: [],
    messages: [],
    rewards: [],
    totalPoints: 0,
    currentUser: null,
    isParent: false,
    configFamille: null,
    attenteValidation: [] // Stocker les validations en attente pour l'affichage
};

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Initialiser les onglets
    initializeTabs();
    
    // Charger la configuration famille
    await loadConfigFamille();
    
    // Initialiser le sélecteur d'utilisateur
    initializeUserSelector();
    
    // Initialiser le bouton d'authentification parent
    document.getElementById('btnAuthParent').addEventListener('click', openAuthModal);
    
    // Charger les données
    await loadTaches();
    await loadMessages();
    calculateTotalPoints();
    await loadRewards();
    await loadClassement();
    await loadAttenteValidation();
    
    // Écouter les formulaires
    document.getElementById('tacheForm').addEventListener('submit', handleTacheSubmit);
    document.getElementById('messageForm').addEventListener('submit', handleMessageSubmit);
    
    // Mettre à jour le tableau de bord
    updateDashboard();
}

// Gestion des onglets
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Désactiver tous les onglets
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activer l'onglet sélectionné
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Charger les données spécifiques selon l'onglet
            if (targetTab === 'calendrier') {
                loadCalendrier('aujourdhui');
            } else if (targetTab === 'classement') {
                loadClassement();
            } else if (targetTab === 'famille' && appData.isParent) {
                loadFamille();
            }
            
            // Réinitialiser les icônes Lucide
            lucide.createIcons();
        });
    });
}

// Charger la configuration famille
async function loadConfigFamille() {
    try {
        const response = await fetch(`${API_BASE}/api/config/famille`);
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                appData.configFamille = data.config;
                updateUserSelector();
                updateResponsablesCheckboxes();
                // Vérifier si l'utilisateur actuel est parent
                const currentUser = getCurrentUser();
                if (currentUser) {
                    checkIfParent(currentUser);
                }
            }
        }
    } catch (error) {
        console.error('Erreur lors du chargement de la config:', error);
    }
}

// Mettre à jour les cases à cocher des responsables
function updateResponsablesCheckboxes() {
    const container = document.getElementById('responsablesCheckboxes');
    if (!container || !appData.configFamille) return;
    
    container.innerHTML = '';
    
    // Récupérer tous les membres de la famille
    const allMembers = [
        ...(appData.configFamille.parents || []),
        ...(appData.configFamille.ados || []),
        ...(appData.configFamille.enfants || [])
    ];
    
    if (allMembers.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">Aucun membre dans la famille. Ajoutez-en dans l\'onglet Famille.</p>';
        return;
    }
    
    allMembers.forEach(member => {
        const checkboxItem = document.createElement('div');
        checkboxItem.className = 'checkbox-item';
        const checkboxId = `responsable-${member.replace(/\s+/g, '-')}`;
        
        checkboxItem.innerHTML = `
            <input type="checkbox" id="${checkboxId}" name="responsables" value="${escapeHtml(member)}">
            <label for="${checkboxId}">${escapeHtml(member)}</label>
        `;
        
        container.appendChild(checkboxItem);
    });
}

// Charger les tâches depuis l'API
async function loadTaches() {
    try {
        const response = await fetch(`${API_BASE}/api/taches`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        appData.taches = data.taches || [];
        
        // Normaliser les données responsables (Supabase peut retourner des arrays PostgreSQL comme strings)
        appData.taches = appData.taches.map(tache => {
            if (tache.responsables && typeof tache.responsables === 'string') {
                try {
                    // Format PostgreSQL array: {val1,val2} -> ["val1","val2"]
                    const cleaned = tache.responsables.replace(/^{|}$/g, '').replace(/"/g, '');
                    tache.responsables = cleaned ? cleaned.split(',') : [];
                } catch (e) {
                    console.error('Erreur parsing responsables:', e, tache.responsables);
                    tache.responsables = [];
                }
            }
            // S'assurer que responsables est toujours un array
            if (!Array.isArray(tache.responsables)) {
                tache.responsables = tache.responsable ? [tache.responsable] : [];
            }
            return tache;
        });
        
        // Mettre à jour le sélecteur de templates
        updateTacheTemplates();
        
        console.log('Tâches chargées depuis API:', appData.taches.length);
        console.log('Exemple de tâche:', appData.taches[0]);
        
        // Filtrer les tâches selon l'utilisateur actuel avec les nouvelles règles
        let tachesToDisplay = appData.taches;
        const currentUser = getCurrentUser();
        
        console.log('Filtrage - Utilisateur actuel:', currentUser, 'Est parent:', appData.isParent);
        
        if (appData.isParent) {
            // RÈGLE 2 : Les parents voient toutes les tâches, surtout celles en attente
            tachesToDisplay = appData.taches;
        } else if (currentUser) {
            // RÈGLE 1 : Les enfants ne voient QUE leurs tâches avec statut 'a_faire' ou 'en_cours'
            // RÈGLE 2 : Les tâches en 'en_attente' n'apparaissent PAS chez les enfants
            tachesToDisplay = appData.taches.filter(t => {
                // Exclure les tâches en attente et terminées pour les enfants
                if (t.statut === 'en_attente' || t.statut === 'termine') {
                    console.log(`❌ Tâche "${t.nom}" - Statut "${t.statut}" exclu pour enfant`);
                    return false;
                }
                
                const user = currentUser.trim();
                const userLower = user.toLowerCase();
                
                // Vérifier dans l'array responsables (normalisé lors du chargement)
                if (t.responsables && Array.isArray(t.responsables) && t.responsables.length > 0) {
                    const match = t.responsables.some(r => {
                        const rTrimmed = (r || '').trim();
                        return rTrimmed.toLowerCase() === userLower;
                    });
                    if (match) {
                        console.log(`✅ Tâche "${t.nom}" - User "${user}" trouvé dans responsables: ${JSON.stringify(t.responsables)}`);
                        return true;
                    }
                }
                
                // Vérifier dans responsable (ancien format ou compatibilité)
                const responsable = (t.responsable || '').trim();
                const match = responsable.toLowerCase() === userLower;
                if (match) {
                    console.log(`✅ Tâche "${t.nom}" - User "${user}" match avec responsable: "${responsable}"`);
                } else {
                    console.log(`❌ Tâche "${t.nom}" - User "${user}" ne match pas. Responsables: ${JSON.stringify(t.responsables || [])}, Responsable: "${t.responsable}"`);
                }
                return match;
            });
        }
        // Si pas d'utilisateur sélectionné, afficher toutes les tâches pour permettre la sélection
        
        console.log('Tâches à afficher:', tachesToDisplay.length, tachesToDisplay);
        displayTaches(tachesToDisplay);
        updateDashboard();
    } catch (error) {
        console.error('Erreur lors du chargement des tâches:', error);
        appData.taches = [];
        displayTaches([]);
    }
}

// Fonction pour afficher les tâches avec le système de "Sablier"
function displayTaches(taches) {
    const container = document.getElementById('tachesList');
    if (!container) {
        console.error('Container tachesList introuvable');
        return;
    }
    
    console.log('Affichage de', taches.length, 'tâches');
    container.innerHTML = '';

    if (taches.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px; font-weight: 600;">Aucune tâche pour le moment</p>';
        return;
    }

    taches.forEach(tache => {
        const card = document.createElement('div');
        // On définit la couleur selon le type (Quotidien, Hebdo, Ponctuel)
        const typeMap = {
            'quotidienne': 'quotidienne',
            'hebdomadaire': 'hebdomadaire',
            'ponctuelle': 'ponctuelle'
        };
        const colorClass = typeMap[tache.type] || 'quotidienne';
        card.className = `mission-box ${colorClass}`;

        let actionButton = '';
        let statusIcon = '';

        if (tache.statut === 'en_attente') {
            // RÈGLE 2 : Les tâches en attente n'apparaissent QUE chez les parents
            // Si on arrive ici et qu'on n'est pas parent, c'est une erreur (ne devrait pas arriver)
            if (!appData.isParent) {
                console.warn('Tâche en attente affichée pour un non-parent, ce ne devrait pas arriver');
                return; // Ne pas afficher cette tâche
            }
            
            // C'est ici que la magie du sablier opère
            statusIcon = '<div class="sablier-animation">⏳</div>';
            
            // Récupérer qui a terminé la tâche depuis l'attente de validation
            const tacheIdForActions = tache.id || tache._id;
            if (tacheIdForActions && appData.isParent) {
                // Afficher le bouton de validation pour le parent
                actionButton = `<button onclick="validateTache(${tacheIdForActions})" class="btn-validate">
                    <i data-lucide="check-circle"></i>
                    <span>Valider la mission</span>
                </button>`;
            } else {
                actionButton = `<p class="waiting-msg">En attente de validation parent...</p>`;
            }
        } else if (tache.statut === 'a_faire') {
            const tacheIdForActions = tache.id || tache._id;
            if (tacheIdForActions) {
                actionButton = `<button onclick="terminerTache(${tacheIdForActions})" class="btn-complete">Terminer la mission</button>`;
            }
        } else if (tache.statut === 'en_cours') {
            const tacheIdForActions = tache.id || tache._id;
            if (tacheIdForActions) {
                actionButton = `<button onclick="terminerTache(${tacheIdForActions})" class="btn-complete">
                    <i data-lucide="check"></i>
                    <span>Terminer la mission</span>
                </button>`;
            }
        } else if (tache.statut === 'termine') {
            statusIcon = '✅';
            actionButton = `<p class="done-msg" style="color: #22c55e; font-weight: 600;">Mission réussie !</p>`;
        }

        // Mapper les icônes Lucide
        const iconMap = {
            'sparkles': 'sparkles',
            'home': 'home',
            'utensils': 'utensils',
            'shirt': 'shirt',
            'broom': 'broom',
            'shopping-cart': 'shopping-cart',
            'leaf': 'leaf',
            'wrench': 'wrench'
        };
        const iconName = iconMap[tache.icone] || 'sparkles';

        // Vérifier que tache.id existe (peut être 'id' depuis Supabase ou '_id' depuis mémoire)
        const tacheId = tache.id || tache._id;
        if (!tacheId) {
            console.error('Tâche sans ID:', tache);
        }
        
        card.innerHTML = `
            <div class="pts-badge">
                <i data-lucide="coins"></i>
                <span>${tache.points || 10} pts</span>
            </div>
            <div class="mission-header">
                <div class="mission-icone">
                    <i data-lucide="${iconName}"></i>
            </div>
                <div class="mission-nom">${escapeHtml(tache.nom)}</div>
            </div>
            <div class="mission-info">
                <div class="mission-responsable">
                    ${tache.statut === 'en_attente' && appData.isParent 
                        ? `<strong>Terminée par:</strong> ${getValidationUserDisplay(tache)}`
                        : `<strong>Responsable:</strong> ${getCurrentUserDisplayForTache(tache)}`
                    }
            </div>
                <div class="mission-statut ${tache.statut}">
                    ${statusIcon}
                    ${tache.statut === 'en_attente' ? '<span class="sablier-animation">⏳</span>' : ''}
            </div>
            </div>
            <div class="mission-actions">
                ${actionButton}
            </div>
            ${tacheId && appData.isParent ? `<button class="btn-delete" onclick="deleteTache(${tacheId})" title="Supprimer">
                <i data-lucide="trash-2"></i>
            </button>` : ''}
        `;
        container.appendChild(card);
        console.log('Tâche ajoutée au DOM:', tache.nom, 'ID:', tacheId);
    });
    
    // Réinitialiser les icônes Lucide
    lucide.createIcons();
}

// Fonction appelée quand quelqu'un clique sur "Terminer"
async function terminerTache(id) {
    const tache = appData.taches.find(t => t.id === id);
    if (!tache) return;
    
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('Veuillez sélectionner un utilisateur', 'error');
        return;
    }
    
    // Vérifier si l'utilisateur est bien responsable de cette tâche
    let responsables = [];
    if (tache.responsables) {
        if (Array.isArray(tache.responsables)) {
            responsables = tache.responsables;
        } else if (typeof tache.responsables === 'string') {
            try {
                responsables = JSON.parse(tache.responsables.replace(/{/g, '[').replace(/}/g, ']'));
            } catch (e) {
                responsables = [tache.responsables];
            }
        }
    }
    if (responsables.length === 0 && tache.responsable) {
        responsables = [tache.responsable];
    }
    
    const isResponsable = responsables.some(r => (r || '').trim().toLowerCase() === currentUser.trim().toLowerCase());
    if (!isResponsable) {
        showToast('Vous n\'êtes pas responsable de cette tâche', 'error');
        return;
    }
    
    // RÈGLE 2 : Seuls les enfants peuvent mettre une tâche en attente
    // Les parents valident directement (pas de terminerTache pour eux)
    if (appData.isParent) {
        showToast('Les parents doivent utiliser le bouton "Valider"', 'info');
        return;
    }
    
    try {
        // RÈGLE 2 : On change le statut en "en_attente" - la tâche disparaît de l'enfant
        // et apparaît uniquement chez le parent pour validation
        const response = await fetch(`${API_BASE}/api/taches/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ statut: 'en_attente' })
        });
        
        if (response.ok) {
            // Ajouter à l'historique des tâches complétées (non validée)
            // RÈGLE 3 : Pas de points ajoutés ici, seulement lors de la validation parent
            const today = new Date().toISOString().split('T')[0];
            
            await fetch(`${API_BASE}/api/taches-completees`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: id,
                    task_nom: tache.nom,
                    user_name: currentUser,
                    date_completion: today,
                    points: tache.points || 10,
                    validated: false // RÈGLE 3 : Pas encore validée
                })
            });
            
            // Ajouter à l'attente de validation
            await fetch(`${API_BASE}/api/attente-validation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_name: currentUser,
                    task_nom: tache.nom,
                    task_id: id,
                    points: tache.points || 10,
                    date_completion: today
                })
            });
            
            showToast('⏳ Mission terminée ! En attente de validation parent...', 'success');
            // RÈGLE 2 : La tâche disparaît de la vue de l'enfant (statut en_attente)
            await loadTaches();
        } else {
            showToast('Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de la complétion:', error);
        showToast('Erreur lors de la complétion', 'error');
    }
}

// Fonction pour valider une tâche (parent uniquement)
async function validateTache(id) {
    const tache = appData.taches.find(t => t.id === id);
    if (!tache) return;
    
    // Vérifier l'authentification parent
    if (!appData.isParent) {
        showToast('🔐 Authentification parent requise', 'error');
        openAuthModal();
        return;
    }
    
    try {
        // Récupérer la validation en attente correspondante
        const validationsResponse = await fetch(`${API_BASE}/api/attente-validation`);
        const validations = await validationsResponse.json();
        const validation = validations.validations?.find(v => v.task_id === id || v.task_nom === tache.nom);
        
        if (validation) {
            // Supprimer de l'attente
            await fetch(`${API_BASE}/api/attente-validation/${validation.id}`, {
                method: 'DELETE'
            });
        }
        
        // Mettre à jour le statut de la tâche à "termine"
        await fetch(`${API_BASE}/api/taches/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ statut: 'termine' })
        });
        
        // RÈGLE 3 : Ajouter les points UNIQUEMENT lors de la validation parent
        // Les points vont à la personne qui a terminé la tâche (dans validation.user_name)
        const user_name = validation?.user_name;
        if (!user_name) {
            showToast('Erreur : impossible de déterminer qui a terminé la tâche', 'error');
            return;
        }
        
        // Ajouter les points au classement de l'enfant qui a fait la tâche
        await fetch(`${API_BASE}/api/classement`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_name: user_name,
                points: tache.points || 10
            })
        });
        
        // Mettre à jour les points du foyer
        const configResponse = await fetch(`${API_BASE}/api/config/famille`);
        const config = await configResponse.json();
        if (config.success) {
            const newPoints = (config.config.points_foyer || 0) + (tache.points || 10);
            await fetch(`${API_BASE}/api/config/famille`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    points_foyer: newPoints
                })
            });
        }
        
        // Recharger les données
        await loadTaches();
        calculateTotalPoints();
        
        showToast(`✅ Mission validée ! +${tache.points || 10} points gagnés ! 🎉`, 'success');
    } catch (error) {
        console.error('Erreur lors de la validation:', error);
        showToast('Erreur lors de la validation', 'error');
    }
}

// Gérer la soumission du formulaire de tâche
async function handleTacheSubmit(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = 'Ajout en cours...';
    
    // Récupérer les responsables sélectionnés (cases à cocher)
    const responsablesCheckboxes = document.querySelectorAll('input[name="responsables"]:checked');
    const responsables = Array.from(responsablesCheckboxes).map(cb => cb.value);
    
    if (responsables.length === 0) {
        showToast('Veuillez sélectionner au moins un responsable', 'error');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Ajouter la tâche';
        return;
    }
    
    // Créer une seule tâche avec tous les responsables sélectionnés
    const nom = document.getElementById('tache-nom').value;
    const icone = document.getElementById('tache-icone').value;
    const type = document.getElementById('tache-type').value;
    const points = parseInt(document.getElementById('tache-points').value);
    const statut = document.getElementById('tache-statut').value;
    
    try {
        // Créer une seule tâche avec tous les responsables
    const formData = {
            nom: nom,
            icone: icone,
            responsables: responsables, // Liste de tous les responsables
            responsable: responsables[0], // Premier responsable pour compatibilité
            type: type,
            points: points,
            statut: statut
        };
        
        const response = await fetch(`${API_BASE}/api/taches`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (responsables.length === 1) {
                showToast('Tâche ajoutée ! ✨', 'success');
            } else {
                showToast(`Tâche ajoutée pour ${responsables.length} responsable(s) ! ✨`, 'success');
            }
            
            // Réinitialiser le formulaire avec les valeurs par défaut
            e.target.reset();
            document.getElementById('tache-type').value = 'quotidienne';
            document.getElementById('tache-points').value = '10';
            document.getElementById('tache-statut').value = 'a_faire';
            
            // Décocher toutes les cases à cocher des responsables
            document.querySelectorAll('input[name="responsables"]').forEach(cb => {
                cb.checked = false;
            });
            
            // Réinitialiser le sélecteur de template
            const templateSelect = document.getElementById('tacheTemplate');
            if (templateSelect) {
                templateSelect.value = '';
            }
            
            // Attendre un peu pour que la base de données enregistre
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Recharger les tâches pour afficher la nouvelle
            console.log('Rechargement des tâches après ajout...');
            await loadTaches();
            
            // S'assurer qu'on est sur l'onglet Tâches pour voir la nouvelle tâche
            const tachesTab = document.querySelector('[data-tab="taches"]');
            if (tachesTab && !tachesTab.classList.contains('active')) {
                tachesTab.click();
            }
            
            // Scroll vers la liste des tâches
            const tachesList = document.getElementById('tachesList');
            if (tachesList) {
                tachesList.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        } else {
            showToast(data.error || 'Erreur lors de l\'ajout', 'error');
            console.error('Erreur API:', data);
        }
    } catch (error) {
        console.error('Erreur lors de l\'envoi:', error);
        showToast('Erreur lors de l\'ajout', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Ajouter la tâche';
    }
}

// Supprimer une tâche
async function deleteTache(id) {
    if (!confirm('Voulez-vous vraiment supprimer cette tâche ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/taches/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Tâche supprimée', 'success');
            await loadTaches();
        } else {
            showToast('Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}

// Charger les messages depuis l'API
async function loadMessages() {
    try {
        const response = await fetch(`${API_BASE}/api/messages`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        appData.messages = data.messages || [];
        
        displayMessages(appData.messages);
        updateDashboard();
    } catch (error) {
        console.error('Erreur lors du chargement des messages:', error);
        appData.messages = [];
        displayMessages([]);
    }
}

// Afficher les messages
function displayMessages(messages) {
    const messagesWall = document.getElementById('messagesWall');
    if (!messagesWall) return;
    
    messagesWall.innerHTML = '';
    
    if (messages.length === 0) {
        messagesWall.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px; font-weight: 600; grid-column: 1 / -1;">Aucun message pour le moment</p>';
        return;
    }
    
    const sortedMessages = [...messages].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    sortedMessages.forEach((message) => {
        const messageItem = document.createElement('div');
        messageItem.className = 'message-item';
        
        const date = new Date(message.created_at);
        const dateStr = date.toLocaleDateString('fr-BE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageItem.innerHTML = `
            <div class="message-auteur">${escapeHtml(message.auteur)}</div>
            <div class="message-texte">${escapeHtml(message.texte)}</div>
            <div class="message-date">${dateStr}</div>
            <button class="btn-delete" onclick="deleteMessage(${message.id})" title="Supprimer">
                <i data-lucide="x"></i>
            </button>
        `;
        
        messagesWall.appendChild(messageItem);
    });
    
    lucide.createIcons();
}

// Gérer la soumission du formulaire de message
async function handleMessageSubmit(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = 'Publication...';
    
    const formData = {
        auteur: document.getElementById('message-auteur').value,
        texte: document.getElementById('message-texte').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Message publié ! 💌', 'success');
            e.target.reset();
            await loadMessages();
        } else {
            showToast('Erreur lors de la publication', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de l\'envoi:', error);
        showToast('Erreur lors de la publication', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Publier le message';
    }
}

// Supprimer un message
async function deleteMessage(id) {
    if (!confirm('Voulez-vous vraiment supprimer ce message ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/messages/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Message supprimé', 'success');
            await loadMessages();
        } else {
            showToast('Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}

// Mettre à jour le tableau de bord
function updateDashboard() {
    const taches = appData.taches || [];
    const messages = appData.messages || [];
    
    const tachesTerminees = taches.filter(t => t.statut === 'termine').length;
    const tachesEnCours = taches.filter(t => t.statut === 'en_cours').length;
    const tachesAFaire = taches.filter(t => t.statut === 'a_faire').length;
    
    const tachesTermineesEl = document.getElementById('tachesTerminees');
    const tachesEnCoursEl = document.getElementById('tachesEnCours');
    const tachesAFaireEl = document.getElementById('tachesAFaire');
    const nbMessagesEl = document.getElementById('nbMessages');
    
    if (tachesTermineesEl) tachesTermineesEl.textContent = tachesTerminees;
    if (tachesEnCoursEl) tachesEnCoursEl.textContent = tachesEnCours;
    if (tachesAFaireEl) tachesAFaireEl.textContent = tachesAFaire;
    if (nbMessagesEl) nbMessagesEl.textContent = messages.length;
    
    calculateTotalPoints();
}

// Calculer le total des points
function calculateTotalPoints() {
    const taches = appData.taches || [];
    const total = taches
        .filter(t => t.statut === 'termine')
        .reduce((sum, t) => sum + (t.points || 0), 0);
    
    appData.totalPoints = total;
    const totalPointsEl = document.getElementById('totalPoints');
    if (totalPointsEl) {
        totalPointsEl.textContent = total;
    }
    
    if (appData.rewards && appData.rewards.length > 0) {
        displayRewards();
    }
}

// Charger les récompenses
async function loadRewards() {
    appData.rewards = [
        {
            id: 1,
            title: 'Sortie au cinéma',
            description: 'Une sortie au cinéma en famille',
            icon: '🎬',
            price: 50,
            gradient: 'gradient-1'
        },
        {
            id: 2,
            title: 'Glace au choix',
            description: 'Une glace de ton choix',
            icon: '🍦',
            price: 20,
            gradient: 'gradient-2'
        },
        {
            id: 3,
            title: 'Jeu vidéo 30 min',
            description: '30 minutes de jeu vidéo',
            icon: '🎮',
            price: 30,
            gradient: 'gradient-3'
        },
        {
            id: 4,
            title: 'Repas au restaurant',
            description: 'Un repas au restaurant',
            icon: '🍽️',
            price: 100,
            gradient: 'gradient-4'
        },
        {
            id: 5,
            title: 'Activité sportive',
            description: 'Une activité sportive de ton choix',
            icon: '⚽',
            price: 40,
            gradient: 'gradient-5'
        },
        {
            id: 6,
            title: 'Cadeau surprise',
            description: 'Un cadeau surprise choisi par les parents',
            icon: '🎁',
            price: 150,
            gradient: 'gradient-6'
        }
    ];
    
    displayRewards();
}

// Afficher les récompenses
function displayRewards() {
    const rewardsGrid = document.getElementById('rewardsGrid');
    if (!rewardsGrid) return;
    
    rewardsGrid.innerHTML = '';
    
    appData.rewards.forEach((reward) => {
        const rewardCard = document.createElement('div');
        const canAfford = appData.totalPoints >= reward.price;
        rewardCard.className = `reward-card ${reward.gradient} ${canAfford ? '' : 'disabled'}`;
        
        rewardCard.innerHTML = `
            <div class="reward-content">
                <div class="reward-icon">${reward.icon}</div>
                <div class="reward-title">${escapeHtml(reward.title)}</div>
                <div class="reward-description">${escapeHtml(reward.description)}</div>
                <div class="reward-price">
                    <i data-lucide="coins"></i>
                    <span>${reward.price} points</span>
                </div>
            </div>
        `;
        
        if (canAfford) {
            rewardCard.addEventListener('click', () => purchaseReward(reward.id));
        }
        
        rewardsGrid.appendChild(rewardCard);
    });
    
    lucide.createIcons();
}

// Acheter une récompense
async function purchaseReward(rewardId) {
    const reward = appData.rewards.find(r => r.id === rewardId);
    if (!reward) return;
    
    if (appData.totalPoints < reward.price) {
        showToast('Points insuffisants', 'error');
        return;
    }
    
    if (confirm(`Voulez-vous acheter "${reward.title}" pour ${reward.price} points ?`)) {
        showToast(`Récompense "${reward.title}" achetée ! 🎉`, 'success');
    }
}

// Afficher une notification toast
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Échapper le HTML pour éviter les injections XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Fonction pour afficher les responsables (support multiple)
function getResponsablesDisplay(tache) {
    if (tache.responsables && Array.isArray(tache.responsables) && tache.responsables.length > 0) {
        // Nouveau format : array de responsables
        return tache.responsables.map(r => escapeHtml(r)).join(', ');
    } else if (tache.responsable) {
        // Ancien format : string unique
        return escapeHtml(tache.responsable);
    }
    return 'Non défini';
}

// Fonction pour afficher le nom du responsable actuel dans la tâche
function getCurrentUserDisplayForTache(tache) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        return getResponsablesDisplay(tache);
    }
    
    const user = currentUser.trim();
    const userLower = user.toLowerCase();
    
    // Vérifier dans l'array responsables (déjà normalisé)
    if (tache.responsables && Array.isArray(tache.responsables) && tache.responsables.length > 0) {
        const found = tache.responsables.find(r => (r || '').trim().toLowerCase() === userLower);
        if (found) {
            return escapeHtml(found.trim());
        }
    }
    
    // Vérifier dans responsable (ancien format)
    if (tache.responsable && tache.responsable.trim().toLowerCase() === userLower) {
        return escapeHtml(tache.responsable.trim());
    }
    
    // Si pas trouvé, afficher tous les responsables
    return getResponsablesDisplay(tache);
}

// Fonction pour afficher qui a terminé la tâche (pour les parents)
function getValidationUserDisplay(tache) {
    // Cette fonction sera appelée uniquement pour les tâches en attente chez les parents
    // Récupérer l'info depuis appData.attenteValidation si disponible
    if (appData.attenteValidation && Array.isArray(appData.attenteValidation)) {
        const validation = appData.attenteValidation.find(v => 
            v.task_id === tache.id || v.task_nom === tache.nom
        );
        if (validation && validation.user_name) {
            return escapeHtml(validation.user_name);
        }
    }
    // Fallback : afficher le premier responsable
    if (tache.responsables && Array.isArray(tache.responsables) && tache.responsables.length > 0) {
        return escapeHtml(tache.responsables[0]);
    }
    return escapeHtml(tache.responsable || 'Non défini');
}

// Mettre à jour le sélecteur de templates de tâches
function updateTacheTemplates() {
    const templateSelect = document.getElementById('tacheTemplate');
    if (!templateSelect) return;
    
    // Garder l'option par défaut
    templateSelect.innerHTML = '<option value="">-- Sélectionner une tâche à réutiliser --</option>';
    
    // Récupérer les tâches uniques (par nom) pour éviter les doublons
    const uniqueTaches = [];
    const seenNames = new Set();
    
    appData.taches.forEach(tache => {
        if (tache.nom && !seenNames.has(tache.nom.toLowerCase())) {
            seenNames.add(tache.nom.toLowerCase());
            uniqueTaches.push(tache);
        }
    });
    
    // Trier par nom
    uniqueTaches.sort((a, b) => a.nom.localeCompare(b.nom));
    
    // Ajouter les options
    uniqueTaches.forEach(tache => {
        const option = document.createElement('option');
        option.value = tache.id;
        option.textContent = `${tache.nom} (${tache.points || 10} pts, ${tache.type || 'quotidienne'})`;
        templateSelect.appendChild(option);
    });
}

// Charger un template de tâche dans le formulaire
function loadTacheTemplate(tacheId) {
    if (!tacheId) return;
    
    const tache = appData.taches.find(t => t.id == tacheId);
    if (!tache) return;
    
    // Pré-remplir le formulaire
    document.getElementById('tache-nom').value = tache.nom || '';
    document.getElementById('tache-icone').value = tache.icone || 'sparkles';
    document.getElementById('tache-type').value = tache.type || 'quotidienne';
    document.getElementById('tache-points').value = tache.points || 10;
    document.getElementById('tache-statut').value = 'a_faire'; // Toujours remettre à "à faire"
    
    // Cocher les responsables
    document.querySelectorAll('input[name="responsables"]').forEach(cb => {
        cb.checked = false;
    });
    
    let responsables = [];
    if (tache.responsables) {
        if (Array.isArray(tache.responsables)) {
            responsables = tache.responsables;
        } else if (typeof tache.responsables === 'string') {
            try {
                responsables = JSON.parse(tache.responsables.replace(/{/g, '[').replace(/}/g, ']'));
            } catch (e) {
                responsables = [tache.responsables];
            }
        }
    }
    if (responsables.length === 0 && tache.responsable) {
        responsables = [tache.responsable];
    }
    
    responsables.forEach(resp => {
        const checkbox = document.querySelector(`input[name="responsables"][value="${escapeHtml(resp)}"]`);
        if (checkbox) {
            checkbox.checked = true;
        }
    });
    
    showToast('📋 Tâche chargée ! Modifiez si nécessaire puis ajoutez.', 'success');
}

// Fonctions utilitaires pour gérer l'utilisateur actuel
function getCurrentUser() {
    return appData.currentUser || localStorage.getItem('currentUser') || sessionStorage.getItem('currentUser') || null;
}

function setCurrentUser(userName) {
    appData.currentUser = userName;
    localStorage.setItem('currentUser', userName);
    checkIfParent(userName);
}

function checkIfParent(userName) {
    if (!appData.configFamille || !userName) {
        appData.isParent = false;
        updateParentIndicator();
        return false;
    }
    const parents = appData.configFamille.parents || [];
    appData.isParent = parents.includes(userName);
    updateParentIndicator();
    updateFamilleTabVisibility();
    return appData.isParent;
}

function updateParentIndicator() {
    const indicator = document.getElementById('parentIndicator');
    if (indicator) {
        indicator.style.display = appData.isParent ? 'flex' : 'none';
    }
}

function updateFamilleTabVisibility() {
    const tabFamille = document.getElementById('tabFamille');
    if (tabFamille) {
        tabFamille.style.display = appData.isParent ? 'flex' : 'none';
    }
}

// ========== GESTION DU SÉLECTEUR D'UTILISATEUR ==========

function initializeUserSelector() {
    const userSelect = document.getElementById('currentUser');
    if (!userSelect) return;
    
    // Remplir le sélecteur avec les membres de la famille
    updateUserSelector();
    
    // Écouter les changements
    userSelect.addEventListener('change', async (e) => {
        const selectedUser = e.target.value;
        if (selectedUser) {
            // Vérifier si c'est un parent
            const isParentUser = appData.configFamille && 
                (appData.configFamille.parents || []).includes(selectedUser);
            
            if (isParentUser && !appData.isParent) {
                // Demander l'authentification parent
                showToast('🔐 Authentification parent requise', 'info');
                openAuthModal();
                // Ne pas changer l'utilisateur tant que l'authentification n'est pas réussie
                userSelect.value = getCurrentUser() || '';
                return;
            }
            
            setCurrentUser(selectedUser);
            checkIfParent(selectedUser);
            showToast(`Connecté en tant que ${selectedUser}`, 'success');
            // Recharger les tâches pour filtrer selon l'utilisateur
            await loadTaches();
        }
    });
    
    // Restaurer l'utilisateur précédent
    const savedUser = getCurrentUser();
    if (savedUser && appData.configFamille) {
        const allMembers = [
            ...(appData.configFamille.parents || []),
            ...(appData.configFamille.ados || []),
            ...(appData.configFamille.enfants || [])
        ];
        
        // Vérifier si l'utilisateur sauvegardé est un parent et nécessite une authentification
        const isParentUser = (appData.configFamille.parents || []).includes(savedUser);
        if (isParentUser && !appData.isParent) {
            // Ne pas restaurer automatiquement, demander l'authentification
            userSelect.value = '';
            return;
        }
        if (allMembers.includes(savedUser)) {
            userSelect.value = savedUser;
            setCurrentUser(savedUser);
        }
    }
}

function updateUserSelector() {
    const userSelect = document.getElementById('currentUser');
    if (!userSelect || !appData.configFamille) return;
    
    userSelect.innerHTML = '<option value="">-- Sélectionner --</option>';
    
    const allMembers = [
        ...(appData.configFamille.parents || []),
        ...(appData.configFamille.ados || []),
        ...(appData.configFamille.enfants || [])
    ];
    
    allMembers.forEach(member => {
        const option = document.createElement('option');
        option.value = member;
        option.textContent = member;
        userSelect.appendChild(option);
    });
    
    // Mettre à jour aussi les cases à cocher des responsables
    updateResponsablesCheckboxes();
}

// ========== AUTHENTIFICATION PARENT ==========

function openAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('pinParent').focus();
        lucide.createIcons();
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('pinParent').value = '';
        document.getElementById('authError').style.display = 'none';
    }
}

async function authenticateParent() {
    const pin = document.getElementById('pinParent').value;
    const errorDiv = document.getElementById('authError');
    
    if (!pin) {
        errorDiv.textContent = 'Veuillez entrer le code PIN';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/parent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin: pin })
        });
        
        const data = await response.json();
        
        if (data.success && data.authenticated) {
            appData.isParent = true;
            updateParentIndicator();
            updateFamilleTabVisibility();
            closeAuthModal();
            showToast('✅ Authentification réussie !', 'success');
            
            // Maintenant que l'authentification est réussie, mettre à jour l'utilisateur sélectionné
            const userSelect = document.getElementById('currentUser');
            const savedUser = localStorage.getItem('currentUser');
            if (userSelect && savedUser) {
                // Vérifier que l'utilisateur sauvegardé est bien un parent
                const isParentUser = appData.configFamille && 
                    (appData.configFamille.parents || []).includes(savedUser);
                if (isParentUser) {
                    // Confirmer la sélection
                    userSelect.value = savedUser;
                    setCurrentUser(savedUser);
                    checkIfParent(savedUser);
                }
            }
            
            // Recharger les données pour afficher les validations en attente
            await loadTaches();
            await loadAttenteValidation();
        } else {
            errorDiv.textContent = 'Code PIN incorrect';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Erreur lors de l\'authentification:', error);
        errorDiv.textContent = 'Erreur lors de l\'authentification';
        errorDiv.style.display = 'block';
    }
}

// Fermer le modal en cliquant en dehors
document.addEventListener('click', (e) => {
    const modal = document.getElementById('authModal');
    if (modal && e.target === modal) {
        closeAuthModal();
    }
});

// ========== GESTION DE LA FAMILLE ==========

async function loadFamille() {
    if (!appData.isParent) return;
    
    await loadConfigFamille();
    displayFamille();
}

function displayFamille() {
    if (!appData.configFamille) return;
    
    displayFamilleList('parents', appData.configFamille.parents || []);
    displayFamilleList('ados', appData.configFamille.ados || []);
    displayFamilleList('enfants', appData.configFamille.enfants || []);
}

function displayFamilleList(type, members) {
    const listId = `${type}List`;
    const list = document.getElementById(listId);
    if (!list) return;
    
    list.innerHTML = '';
    
    members.forEach((member, index) => {
        const item = document.createElement('div');
        item.className = 'famille-item';
        item.innerHTML = `
            <div class="famille-item-name">${escapeHtml(member)}</div>
            <div class="famille-item-actions">
                <button class="btn-edit" onclick="editMembre('${type}', ${index})">
                    <i data-lucide="edit"></i>
                    <span>Modifier</span>
                </button>
                <button class="btn-remove" onclick="removeMembre('${type}', ${index})">
                    <i data-lucide="trash-2"></i>
                    <span>Supprimer</span>
                </button>
            </div>
        `;
        list.appendChild(item);
    });
    
    lucide.createIcons();
}

async function addMembre(type) {
    const name = prompt(`Entrez le nom du ${type === 'parent' ? 'parent' : type === 'ado' ? 'ado' : 'enfant'}:`);
    if (!name || !name.trim()) return;
    
    if (!appData.configFamille) await loadConfigFamille();
    
    const typeKey = type === 'parent' ? 'parents' : type === 'ado' ? 'ados' : 'enfants';
    if (!appData.configFamille[typeKey]) appData.configFamille[typeKey] = [];
    
    appData.configFamille[typeKey].push(name.trim());
    
    await saveConfigFamille();
    displayFamille();
    updateUserSelector();
    showToast(`${name} ajouté(e) !`, 'success');
}

async function editMembre(type, index) {
    const typeKey = type === 'parent' ? 'parents' : type === 'ado' ? 'ados' : 'enfants';
    const oldName = appData.configFamille[typeKey][index];
    const newName = prompt(`Modifier le nom:`, oldName);
    
    if (!newName || !newName.trim() || newName === oldName) return;
    
    appData.configFamille[typeKey][index] = newName.trim();
    
    await saveConfigFamille();
    displayFamille();
    updateUserSelector();
    showToast('Membre modifié !', 'success');
}

async function removeMembre(type, index) {
    if (!confirm('Voulez-vous vraiment supprimer ce membre ?')) return;
    
    const typeKey = type === 'parent' ? 'parents' : type === 'ado' ? 'ados' : 'enfants';
    const removed = appData.configFamille[typeKey].splice(index, 1)[0];
    
    await saveConfigFamille();
    displayFamille();
    updateUserSelector();
    showToast(`${removed} supprimé(e)`, 'success');
}

async function saveConfigFamille() {
    try {
        const response = await fetch(`${API_BASE}/api/config/famille`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(appData.configFamille)
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la sauvegarde');
        }
    } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error);
        showToast('Erreur lors de la sauvegarde', 'error');
    }
}

// ========== CALENDRIER ==========

async function loadCalendrier(periode) {
    const content = document.getElementById('calendrierContent');
    if (!content) return;
    
    try {
        const today = new Date();
        let dateStart, dateEnd, label;
        
        if (periode === 'aujourdhui') {
            dateStart = today.toISOString().split('T')[0];
            dateEnd = dateStart;
            label = `Aujourd'hui - ${today.toLocaleDateString('fr-BE')}`;
        } else if (periode === 'semaine') {
            const monday = new Date(today);
            monday.setDate(today.getDate() - today.getDay() + 1);
            dateStart = monday.toISOString().split('T')[0];
            const sunday = new Date(monday);
            sunday.setDate(monday.getDate() + 6);
            dateEnd = sunday.toISOString().split('T')[0];
            label = `Semaine du ${monday.toLocaleDateString('fr-BE')} au ${sunday.toLocaleDateString('fr-BE')}`;
        } else {
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            dateStart = firstDay.toISOString().split('T')[0];
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            dateEnd = lastDay.toISOString().split('T')[0];
            label = today.toLocaleDateString('fr-BE', { month: 'long', year: 'numeric' });
        }
        
        const response = await fetch(`${API_BASE}/api/taches-completees?date_start=${dateStart}&date_end=${dateEnd}`);
        const data = await response.json();
        
        if (data.success) {
            displayCalendrier(data.taches || [], label);
        }
    } catch (error) {
        console.error('Erreur lors du chargement du calendrier:', error);
        content.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Erreur lors du chargement</p>';
    }
}

function displayCalendrier(taches, label) {
    const content = document.getElementById('calendrierContent');
    if (!content) return;
    
    if (taches.length === 0) {
        content.innerHTML = `<p style="color: var(--text-secondary); text-align: center; padding: 20px;">Aucune tâche complétée pour cette période.</p>`;
        return;
    }
    
    // Grouper par date
    const byDate = {};
    taches.forEach(tache => {
        const date = tache.date_completion;
        if (!byDate[date]) byDate[date] = [];
        byDate[date].push(tache);
    });
    
    let html = `<h3 style="color: var(--text-primary); margin-bottom: 20px;">${label}</h3>`;
    
    Object.keys(byDate).sort().reverse().forEach(date => {
        const dateObj = new Date(date);
        const dateStr = dateObj.toLocaleDateString('fr-BE', { 
            weekday: 'long', 
            day: 'numeric', 
            month: 'long' 
        });
        
        html += `<div class="calendrier-day">
            <div class="calendrier-day-header">📅 ${dateStr}</div>`;
        
        // Grouper par utilisateur
        const byUser = {};
        byDate[date].forEach(tache => {
            if (!byUser[tache.user_name]) byUser[tache.user_name] = [];
            byUser[tache.user_name].push(tache);
        });
        
        Object.keys(byUser).forEach(user => {
            const totalPoints = byUser[user].reduce((sum, t) => sum + (t.points || 0), 0);
            html += `<div style="margin-bottom: 10px;">
                <strong>${escapeHtml(user)}</strong> (${totalPoints} pts)
            </div>`;
            
            byUser[user].forEach(tache => {
                const status = tache.validated ? '✅' : '⏳';
                html += `<div class="calendrier-task">
                    <span>${status} ${escapeHtml(tache.task_nom)}</span>
                    <span style="font-weight: 600; color: var(--amber-600);">+${tache.points || 0} pts</span>
                </div>`;
            });
        });
        
        html += `</div>`;
    });
    
    content.innerHTML = html;
}

// ========== CLASSEMENT ==========

async function loadClassement() {
    try {
        const response = await fetch(`${API_BASE}/api/classement`);
        const data = await response.json();
        
        if (data.success) {
            displayClassement(data.classement || []);
        }
    } catch (error) {
        console.error('Erreur lors du chargement du classement:', error);
    }
}

function displayClassement(classement) {
    const list = document.getElementById('classementList');
    if (!list) return;
    
    if (classement.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">Aucun point enregistré pour le moment.</p>';
        return;
    }
    
    list.innerHTML = '';
    
    classement.forEach((entry, index) => {
        const item = document.createElement('div');
        item.className = 'classement-item';
        
        let rankClass = '';
        let rankIcon = '';
        if (index === 0) {
            rankClass = 'first';
            rankIcon = '🥇';
        } else if (index === 1) {
            rankClass = 'second';
            rankIcon = '🥈';
        } else if (index === 2) {
            rankClass = 'third';
            rankIcon = '🥉';
        }
        
        item.innerHTML = `
            <div class="classement-rank ${rankClass}">
                ${rankIcon || (index + 1)}
            </div>
            <div class="classement-info">
                <div class="classement-name">${escapeHtml(entry.user_name)}</div>
            </div>
            <div class="classement-points">${entry.points || 0} pts</div>
        `;
        
        list.appendChild(item);
    });
}

// ========== VALIDATION INTELLIGENTE SELON FRÉQUENCES ==========

async function canValidateTask(taskId, userId) {
    const tache = appData.taches.find(t => t.id === taskId);
    if (!tache) return { canValidate: false, message: 'Tâche introuvable' };
    
    const type = tache.type;
    const today = new Date().toISOString().split('T')[0];
    
    // Récupérer les tâches complétées de cet utilisateur pour cette tâche
    const response = await fetch(`${API_BASE}/api/taches-completees?user_name=${userId}`);
    const data = await response.json();
    
    if (!data.success) return { canValidate: true, message: '' };
    
    const userTasks = (data.taches || []).filter(t => 
        t.task_nom === tache.nom || t.task_id === taskId
    );
    
    if (type === 'quotidienne') {
        // Vérifier si déjà faite aujourd'hui
        const todayTasks = userTasks.filter(t => t.date_completion === today && t.validated);
        if (todayTasks.length > 0) {
            return { 
                canValidate: false, 
                message: `✅ Déjà complétée aujourd'hui (${todayTasks.length} fois)` 
            };
        }
        return { canValidate: true, message: '📅 Peut être complétée chaque jour' };
    }
    
    if (type === 'hebdomadaire') {
        // Calculer le début de la semaine (lundi)
        const todayDate = new Date();
        const monday = new Date(todayDate);
        monday.setDate(todayDate.getDate() - todayDate.getDay() + 1);
        const weekStart = monday.toISOString().split('T')[0];
        
        // Compter les tâches validées cette semaine
        const weekTasks = userTasks.filter(t => 
            t.date_completion >= weekStart && t.validated
        );
        
        // Déterminer le max par semaine (par défaut 1, mais peut varier selon la tâche)
        let maxPerWeek = 1;
        if (tache.nom.includes('Aspirateur') || tache.nom.includes('aspirateur')) {
            maxPerWeek = 2; // 2x par semaine pour l'aspirateur
        }
        
        if (weekTasks.length >= maxPerWeek) {
            return { 
                canValidate: false, 
                message: `⚠️ Déjà complétée ${weekTasks.length} fois cette semaine (max: ${maxPerWeek})` 
            };
        }
        return { 
            canValidate: true, 
            message: `📅 Peut être complétée ${maxPerWeek}x par semaine (${weekTasks.length}/${maxPerWeek} cette semaine)` 
        };
    }
    
    // Ponctuelle : toujours possible
    return { canValidate: true, message: '📅 Tâche ponctuelle - Peut être refaite' };
}

// Modifier terminerTache pour utiliser la validation intelligente
async function terminerTache(id) {
    const tache = appData.taches.find(t => t.id === id);
    if (!tache) return;
    
    const currentUser = getCurrentUser() || tache.responsable;
    
    // Vérifier si la tâche peut être validée selon sa fréquence
    const validation = await canValidateTask(id, currentUser);
    
    if (!validation.canValidate) {
        showToast(validation.message, 'error');
        return;
    }
    
    try {
        // On change le statut en "en_attente" pour afficher le sablier
        const response = await fetch(`${API_BASE}/api/taches/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ statut: 'en_attente' })
        });
        
        if (response.ok) {
            // Ajouter à l'historique des tâches complétées (non validée)
            const today = new Date().toISOString().split('T')[0];
            
            await fetch(`${API_BASE}/api/taches-completees`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: id,
                    task_nom: tache.nom,
                    user_name: currentUser,
                    date_completion: today,
                    points: tache.points || 10,
                    validated: false
                })
            });
            
            // Ajouter à l'attente de validation
            await fetch(`${API_BASE}/api/attente-validation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_name: currentUser,
                    task_nom: tache.nom,
                    task_id: id,
                    points: tache.points || 10,
                    date_completion: today
                })
            });
            
            showToast('⏳ Mission terminée ! En attente de validation parent...', 'success');
            await loadTaches(); // On recharge l'affichage pour afficher le sablier
        } else {
            showToast('Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de la complétion:', error);
        showToast('Erreur lors de la complétion', 'error');
    }
}

// Charger les validations en attente
async function loadAttenteValidation() {
    if (!appData.isParent) {
        appData.attenteValidation = [];
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/attente-validation`);
        const data = await response.json();
        
        // Stocker les validations en attente pour les utiliser dans l'affichage
        appData.attenteValidation = data.validations || [];
        
        if (data.success && data.validations && data.validations.length > 0) {
            // Afficher un message dans le tableau de bord
            const waitingMsg = document.querySelector('.waiting-msg-global');
            if (waitingMsg) {
                waitingMsg.textContent = `⏳ ${data.validations.length} mission(s) en attente de validation !`;
                waitingMsg.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Erreur lors du chargement des validations:', error);
    }
}
