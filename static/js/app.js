// Configuration
const API_BASE = '';

// ========== SAUVEGARDE AUTOMATIQUE ANTI-PERTE (debounce 1s + sync avant changement d'onglet) ==========
const DRAFT_DEBOUNCE_MS = 1000;
const STORAGE_KEYS = { message: 'foyer_draft_message', task: 'foyer_draft_task' };
let _debounceMessage = null;
let _debounceTask = null;
const _pendingSaves = new Set();

function debounce(fn, ms) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), ms);
        return t;
    };
}

function saveMessageDraftToStorage() {
    const texteEl = document.getElementById('message-texte');
    const auteur = getCurrentUser();
    if (!texteEl || !auteur) return;
    const destCheckboxes = document.querySelectorAll('input[name="destinataires"]:checked');
    const destinataires = destCheckboxes.length ? Array.from(destCheckboxes).map(cb => cb.value) : ['toute_la_famille'];
    const draft = {
        auteur,
        texte: (texteEl.value || '').trim(),
        destinataires: destinataires.includes('toute_la_famille') ? ['toute_la_famille'] : destinataires,
        image_url: window._pendingMessageImageUrl || null
    };
    if (!draft.texte && !draft.image_url) {
        try { localStorage.removeItem(STORAGE_KEYS.message); } catch (e) {}
        return;
    }
    try {
        localStorage.setItem(STORAGE_KEYS.message, JSON.stringify(draft));
    } catch (e) {
        console.warn('Auto-save message draft:', e);
    }
}

function saveTaskDraftToStorage() {
    const nom = document.getElementById('tache-nom');
    const icone = document.getElementById('tache-icone');
    const type = document.getElementById('tache-type');
    const points = document.getElementById('tache-points');
    const statut = document.getElementById('tache-statut');
    const responsables = document.querySelectorAll('input[name="responsables"]:checked');
    if (!nom) return;
    const draft = {
        nom: (nom.value || '').trim(),
        icone: (icone && icone.value) || 'sparkles',
        type: (type && type.value) || 'quotidienne',
        points: points ? parseInt(points.value, 10) : 10,
        statut: (statut && statut.value) || 'a_faire',
        responsables: Array.from(responsables).map(cb => cb.value)
    };
    if (!draft.nom && !draft.responsables.length) {
        try { localStorage.removeItem(STORAGE_KEYS.task); } catch (e) {}
        return;
    }
    try {
        localStorage.setItem(STORAGE_KEYS.task, JSON.stringify(draft));
    } catch (e) {
        console.warn('Auto-save task draft:', e);
    }
}

function restoreDraftsFromStorage() {
    try {
        const msg = localStorage.getItem(STORAGE_KEYS.message);
        if (msg) {
            const d = JSON.parse(msg);
            const texteEl = document.getElementById('message-texte');
            if (texteEl && (d.texte || d.image_url)) {
                texteEl.value = d.texte || '';
                if (d.image_url) window._pendingMessageImageUrl = d.image_url;
                document.querySelectorAll('input[name="destinataires"]').forEach(cb => { cb.checked = d.destinataires && d.destinataires.includes(cb.value); });
            }
        }
        const task = localStorage.getItem(STORAGE_KEYS.task);
        if (task) {
            const d = JSON.parse(task);
            const nomEl = document.getElementById('tache-nom');
            if (nomEl && (d.nom || (d.responsables && d.responsables.length))) {
                if (nomEl) nomEl.value = d.nom || '';
                const icone = document.getElementById('tache-icone');
                if (icone) icone.value = d.icone || 'sparkles';
                const type = document.getElementById('tache-type');
                if (type) type.value = d.type || 'quotidienne';
                const points = document.getElementById('tache-points');
                if (points) points.value = String(d.points || 10);
                const statut = document.getElementById('tache-statut');
                if (statut) statut.value = d.statut || 'a_faire';
                document.querySelectorAll('input[name="responsables"]').forEach(cb => { cb.checked = d.responsables && d.responsables.includes(cb.value); });
            }
        }
    } catch (e) {
        console.warn('Restore drafts:', e);
    }
}

function flushDraftsBeforeTabSwitch() {
    clearTimeout(_debounceMessage);
    clearTimeout(_debounceTask);
    _debounceMessage = null;
    _debounceTask = null;
    saveMessageDraftToStorage();
    saveTaskDraftToStorage();
    return Promise.all(Array.from(_pendingSaves));
}

function trackPendingSave(promise) {
    if (!promise || typeof promise.then !== 'function') return promise;
    _pendingSaves.add(promise);
    promise.finally(() => { _pendingSaves.delete(promise); });
    return promise;
}

// ========== GALAXIE CANVAS (arrière-plan) ==========
(function initGalaxy() {
    const canvas = document.getElementById('galaxy-bg');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const STAR_COUNT = 1500;
    const NEBULA_COLORS = ['#00d2ff', '#9d50bb', '#6e48aa', '#00d2ff'];
    let stars = [];
    let nebulaAngle = 0;
    let animationId = null;

    function resize() {
        const w = window.innerWidth;
        const h = window.innerHeight;
        canvas.width = w;
        canvas.height = h;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';
        initStars(w, h);
    }

    function initStars(w, h) {
        stars = [];
        for (let i = 0; i < STAR_COUNT; i++) {
            stars.push({
                x: Math.random() * w,
                y: Math.random() * h,
                size: 0.3 + Math.random() * 1.8,
                opacity: 0.3 + Math.random() * 0.7,
                speed: 0.05 + Math.random() * 0.15
            });
        }
    }

    function drawNebula(w, h) {
        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.max(w, h) * 0.6;
        const cloudRadius = Math.max(w, h) * 0.35;
        const offsets = [
            { r: 0.25 * radius, a: 0 },
            { r: 0.3 * radius, a: Math.PI * 0.6 },
            { r: 0.28 * radius, a: Math.PI * 1.3 },
            { r: 0.22 * radius, a: Math.PI * 1.9 }
        ];
        ctx.save();
        ctx.globalAlpha = 0.055;
        for (let i = 0; i < 4; i++) {
            const o = offsets[i];
            const x = cx + Math.cos(nebulaAngle + o.a) * o.r;
            const y = cy + Math.sin(nebulaAngle + o.a) * o.r;
            const g = ctx.createRadialGradient(x, y, 0, x, y, cloudRadius);
            g.addColorStop(0, NEBULA_COLORS[i]);
            g.addColorStop(0.5, NEBULA_COLORS[i]);
            g.addColorStop(1, 'transparent');
            ctx.beginPath();
            ctx.arc(x, y, cloudRadius, 0, Math.PI * 2);
            ctx.fillStyle = g;
            ctx.fill();
        }
        ctx.restore();
        nebulaAngle += 0.00015;
    }

    function drawStars(w, h) {
        for (let i = 0; i < stars.length; i++) {
            const s = stars[i];
            s.y -= s.speed;
            if (s.y < 0) s.y += h;
            ctx.save();
            ctx.globalAlpha = s.opacity * (0.7 + 0.3 * Math.sin(Date.now() * 0.002 + i % 10));
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    function loop() {
        const w = canvas.width;
        const h = canvas.height;
        if (!w || !h) { animationId = requestAnimationFrame(loop); return; }
        ctx.fillStyle = '#020111';
        ctx.fillRect(0, 0, w, h);
        drawNebula(w, h);
        drawStars(w, h);
        animationId = requestAnimationFrame(loop);
    }

    resize();
    window.addEventListener('resize', resize);
    loop();
})();

// Format 24h et conventions belges (séparateur milliers : espace, décimales : virgule)
function formatBelgianNumber(n) {
    return Number(n).toLocaleString('fr-BE');
}
function formatDateTime24h(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleString('fr-BE', { hour12: false, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// État de l'application
let appData = {
    taches: [],
    messages: [],
    rewards: [],
    totalPoints: 0,
    currentUser: null,
    isParent: false,
    configFamille: null,
    attenteValidation: [],
    questPhotoProofs: {} // tacheId -> dataURL (preuves photo par quête)
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
    
    // Initialiser le sélecteur d'utilisateur (modal PIN si parent)
    initializeUserSelector();
    
    // Charger les données
    await loadTaches();
    await loadMessages();
    calculateTotalPoints();
    await loadRewards();
    await loadClassement();
    await loadAttenteValidation();
    
    // Restaurer les brouillons (message + formulaire tâche) après chargement config
    restoreDraftsFromStorage();

    // Auto-save (debounce 1s) sur les champs message
    const messageTexte = document.getElementById('message-texte');
    if (messageTexte) {
        const scheduleMessageDraft = debounce(saveMessageDraftToStorage, DRAFT_DEBOUNCE_MS);
        messageTexte.addEventListener('input', scheduleMessageDraft);
        messageTexte.addEventListener('change', scheduleMessageDraft);
    }
    document.querySelectorAll('input[name="destinataires"]').forEach(cb => {
        cb.addEventListener('change', debounce(saveMessageDraftToStorage, DRAFT_DEBOUNCE_MS));
    });

    // Auto-save (debounce 1s) sur le formulaire tâche
    const taskFields = ['tache-nom', 'tache-icone', 'tache-type', 'tache-points', 'tache-statut'];
    taskFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', debounce(saveTaskDraftToStorage, DRAFT_DEBOUNCE_MS));
    });
    document.querySelectorAll('input[name="responsables"]').forEach(cb => {
        cb.addEventListener('change', debounce(saveTaskDraftToStorage, DRAFT_DEBOUNCE_MS));
    });

    // Écouter les formulaires
    document.getElementById('tacheForm').addEventListener('submit', handleTacheSubmit);
    document.getElementById('messageForm').addEventListener('submit', handleMessageSubmit);
    initMessagePhotoPicker();
    const messageModalClose = document.getElementById('messageExpandModalClose');
    const messageModal = document.getElementById('messageExpandModal');
    if (messageModalClose) messageModalClose.addEventListener('click', closeMessageModal);
    if (messageModal && messageModal.querySelector('.message-expand-backdrop')) {
        messageModal.querySelector('.message-expand-backdrop').addEventListener('click', closeMessageModal);
    }
    
    // Mettre à jour le tableau de bord et la barre de progression
    updateDashboard();
    updateQuestProgressBar();
    applyBodyTheme();
    updateQuestFormVisibility();

    // Démarrer la surveillance des changements (nouveaux messages / tâches) toutes les 60 s
    startNotificationPolling();

    const capturePhotoInput = document.getElementById('capture-photo');
    if (capturePhotoInput) {
        capturePhotoInput.addEventListener('change', handleCapturePhotoChange);
    }
}

// ========== NOTIFICATION LIVE (surveillance toutes les 60 s) ==========
let _lastCheckTachesCount = null;
let _lastCheckMessagesCount = null;
let _notificationPollingInterval = null;

function startNotificationPolling() {
    async function setBaseline() {
        try {
            const [tachesRes, messagesRes] = await Promise.all([
                fetch(`${API_BASE}/api/taches`),
                fetch(`${API_BASE}/api/messages`)
            ]);
            if (tachesRes.ok && messagesRes.ok) {
                const tachesData = await tachesRes.json();
                const messagesData = await messagesRes.json();
                _lastCheckTachesCount = (tachesData.taches || []).length;
                _lastCheckMessagesCount = (messagesData.messages || []).length;
            }
        } catch (e) {
            console.warn('Notification polling: erreur baseline', e);
        }
    }

    async function checkForUpdates() {
        try {
            const [tachesRes, messagesRes] = await Promise.all([
                fetch(`${API_BASE}/api/taches`),
                fetch(`${API_BASE}/api/messages`)
            ]);
            if (!tachesRes.ok || !messagesRes.ok) return;
            const tachesData = await tachesRes.json();
            const messagesData = await messagesRes.json();
            const tachesCount = (tachesData.taches || []).length;
            const messagesCount = (messagesData.messages || []).length;
            if (_lastCheckTachesCount === null || _lastCheckMessagesCount === null) {
                _lastCheckTachesCount = tachesCount;
                _lastCheckMessagesCount = messagesCount;
                return;
            }
            if (tachesCount !== _lastCheckTachesCount || messagesCount !== _lastCheckMessagesCount) {
                showNotificationBanner();
            }
        } catch (e) {
            console.warn('Notification polling: erreur', e);
        }
    }

    setBaseline().then(() => {
        _notificationPollingInterval = setInterval(checkForUpdates, 60000);
    });

    const bannerRefresh = document.getElementById('notificationBannerRefresh');
    if (bannerRefresh) {
        bannerRefresh.addEventListener('click', async () => {
            const banner = document.getElementById('notificationBanner');
            if (banner) {
                banner.classList.remove('notification-banner--visible');
                banner.setAttribute('aria-hidden', 'true');
            }
            await updateData();
            _lastCheckTachesCount = (appData.taches || []).length;
            _lastCheckMessagesCount = (appData.messages || []).length;
        });
    }
}

function showNotificationBanner() {
    const banner = document.getElementById('notificationBanner');
    if (banner) {
        banner.classList.add('notification-banner--visible');
        banner.setAttribute('aria-hidden', 'false');
    }
}

// ——— Rafraîchissement des données sans rechargement (SPA) ——— //
async function updateData(activeTab) {
    try {
        await loadTaches();
        await loadMessages();
        calculateTotalPoints();
        await loadAttenteValidation();
        await loadRewards();
        await loadClassement();
        updateDashboard();
        updateQuestProgressBar();
        if (activeTab === 'calendrier') await loadCalendrier('aujourdhui');
        else if (activeTab === 'classement') { /* déjà fait */ }
        else if (activeTab === 'famille' && appData.isParent) await loadFamille();
        if (activeTab === 'taches') await loadAttenteValidation(); // Badge en temps réel
        if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();
    } catch (e) {
        console.warn('updateData:', e);
    }
}

// Synchronisation finale avant changement d'onglet : drafts en localStorage + attente des sauvegardes Supabase en vol
async function saveDraftMessageIfAny() {
    await flushDraftsBeforeTabSwitch();
}

// ——— Transition "Portal Wipe" : masque circulaire 0→150% + bordure dorée 0.6s ease-in-out ——— //
const PORTAL_DURATION_MS = 600;

function runPortalTransition(switchContentCallback) {
    const overlay = document.getElementById('portal-overlay');
    if (overlay) return;

    const container = document.querySelector('.container');
    const wrap = document.createElement('div');
    wrap.id = 'portal-overlay';
    wrap.setAttribute('aria-hidden', 'true');
    const ring = document.createElement('div');
    ring.className = 'portal-ring';
    wrap.appendChild(ring);
    document.body.appendChild(wrap);

    container.classList.add('portal-wipe-start');
    if (typeof switchContentCallback === 'function') switchContentCallback();

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            container.classList.remove('portal-wipe-start');
            container.classList.add('portal-wipe-active');
            ring.classList.add('portal-ring--active');
        });
    });

    setTimeout(() => {
        container.classList.remove('portal-wipe-active');
        wrap.remove();
    }, PORTAL_DURATION_MS);
}

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const targetTab = button.getAttribute('data-tab');
            const currentActive = document.querySelector('.tab-content.active');
            const targetContent = document.getElementById(targetTab);
            if (!targetContent || currentActive === targetContent) return;

            await saveDraftMessageIfAny();

            runPortalTransition(() => {
                currentActive.classList.remove('active');
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                targetContent.classList.add('active');
                lucide.createIcons();
                updateData(targetTab);
            });
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
                updateDestinatairesCheckboxes();
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
    const heroesHint = document.getElementById('heroesHint');
    if (heroesHint) {
        heroesHint.style.display = allMembers.length >= 2 ? 'block' : 'none';
        heroesHint.textContent = "Plusieurs cochés = L'Équipe de Super-Héros";
    }
}

function updateDestinatairesCheckboxes() {
    const container = document.getElementById('destinatairesCheckboxes');
    if (!container || !appData.configFamille) return;
    container.innerHTML = '';
    const allMembers = [
        ...(appData.configFamille.parents || []),
        ...(appData.configFamille.ados || []),
        ...(appData.configFamille.enfants || [])
    ];
    const destinataireId = (label) => `dest-${label.replace(/\s+/g, '-')}`;
    const touteLaFamilleId = 'dest-toute-la-famille';
    const item = document.createElement('div');
    item.className = 'checkbox-item';
    item.innerHTML = `<input type="checkbox" id="${touteLaFamilleId}" name="destinataires" value="toute_la_famille"><label for="${touteLaFamilleId}">Toute la famille</label>`;
    container.appendChild(item);
    allMembers.forEach(member => {
        const div = document.createElement('div');
        div.className = 'checkbox-item';
        const id = destinataireId(member);
        div.innerHTML = `<input type="checkbox" id="${id}" name="destinataires" value="${escapeHtml(member)}"><label for="${id}">${escapeHtml(member)}</label>`;
        container.appendChild(div);
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
        updateQuestProgressBar();
    } catch (error) {
        console.error('Erreur lors du chargement des tâches:', error);
        appData.taches = [];
        displayTaches([]);
        updateQuestProgressBar();
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
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px; font-weight: 600;">Aucune quête dans le Grimoire pour le moment</p>';
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

        const isRecurring = tache.type === 'quotidienne' || tache.type === 'hebdomadaire';
        const responsableTrim = (tache.responsable || '').trim();
        const noHeroAssigned = isRecurring && tache.statut === 'a_faire' && !responsableTrim;
        const currentUser = getCurrentUser();
        const canAssignSelf = currentUser && tache.responsables && Array.isArray(tache.responsables) &&
            tache.responsables.some(r => (r || '').trim().toLowerCase() === (currentUser || '').trim().toLowerCase());

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
            const curUser = getCurrentUser() || '';
            const isAssignedHero = responsableTrim && curUser && (responsableTrim.toLowerCase() === curUser.trim().toLowerCase());
            if (tacheIdForActions && isAssignedHero) {
                actionButton = `<button onclick="terminerTache(${tacheIdForActions})" class="btn-complete">Terminer la mission</button>`;
            }
        } else if (tache.statut === 'en_cours') {
            const tacheIdForActions = tache.id || tache._id;
            const curUser = getCurrentUser() || '';
            const respTrim = (tache.responsable || '').trim();
            const isAssignedHero = respTrim && curUser && (respTrim.toLowerCase() === curUser.trim().toLowerCase());
            if (tacheIdForActions && isAssignedHero) {
                actionButton = `<button onclick="terminerTache(${tacheIdForActions})" class="btn-complete">
                    <i data-lucide="check"></i>
                    <span>Terminer la mission</span>
                </button>`;
            }
        } else if (tache.statut === 'termine') {
            statusIcon = '✅';
            actionButton = `<p class="done-msg" style="color: #22c55e; font-weight: 600;">Mission réussie !</p>`;
        }

        const tacheId = tache.id || tache._id;
        if (noHeroAssigned && canAssignSelf) {
            actionButton = `<button type="button" class="btn-action btn-je-m-en-occupe" onclick="assignMeToTask(${tacheId})">🙋 Je m'en occupe</button>
                <button type="button" class="btn-secondary btn-choose-hero" onclick="openHeroChoiceModal(${tacheId})" title="Choisir qui fait cette quête">Choisir le héros</button>`;
        } else if (noHeroAssigned) {
            actionButton = `<button type="button" class="btn-secondary btn-choose-hero" onclick="openHeroChoiceModal(${tacheId})" title="Choisir qui fait cette quête">Choisir le héros</button>`;
        }
        const heroNameDisplay = getCurrentUserDisplayForTache(tache);
        const showPhotoProof = !appData.isParent && (tache.statut === 'a_faire' || tache.statut === 'en_cours');
        const photoBlock = showPhotoProof ? `
            <div class="quest-photo-wrap quest-photo-block">
                <div class="quest-photo-polaroid" id="photoPolaroid-${tacheId}" style="display: none;">
                    <img class="quest-photo-thumbnail" id="photoThumb-${tacheId}" src="" alt="Preuve">
                </div>
                <span class="quest-photo-sent" id="photoSentLabel-${tacheId}" style="display: none;">Preuve envoyée !</span>
            </div>` : '';

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

        if (!tacheId) {
            console.error('Tâche sans ID:', tache);
        }
        
        card.innerHTML = `
            <div class="pts-badge">
                <i data-lucide="coins"></i>
                <span>${formatBelgianNumber(tache.points || 10)} pts</span>
            </div>
            <div class="mission-header">
                <div class="mission-icone">
                    <i data-lucide="${iconName}"></i>
            </div>
                <div class="mission-nom">${escapeHtml(tache.nom)}${(tache.type === 'quotidienne' || tache.type === 'hebdomadaire') ? ' <span class="quest-recurring" title="Quête récurrente">🔄</span>' : ''}</div>
            </div>
            ${showPhotoProof ? `<button type="button" class="btn-action btn-photo-proof" onclick="prendrePhoto(${tacheId})" title="Ouvrir la caméra pour prendre une preuve photo">📸 Preuve Photo</button>` : ''}
            <div class="mission-info">
                <div class="mission-responsable">
                    ${tache.statut === 'en_attente' && appData.isParent 
                        ? `<strong>Accomplie par:</strong> ${getValidationUserDisplay(tache)}`
                        : noHeroAssigned 
                            ? `<strong>${getHeroesLabel(tache)}:</strong> Personne ne s'en occupe encore`
                            : `<strong>${getHeroesLabel(tache)}:</strong> ${getCurrentUserDisplayForTache(tache)}`
                    }
            </div>
                <div class="mission-statut ${tache.statut}">
                    ${statusIcon}
                    ${tache.statut === 'en_attente' ? '<span class="sablier-animation">⏳</span>' : ''}
            </div>
            </div>
            ${photoBlock}
            <div class="mission-actions">
                ${actionButton}
            </div>
            <div class="quest-hero-mission">Héros en mission : ${noHeroAssigned ? '—' : heroNameDisplay}</div>
            ${tacheId && appData.isParent ? `<button class="btn-delete" onclick="deleteTache(${tacheId})" title="Supprimer">
                <i data-lucide="trash-2"></i>
            </button>` : ''}
        `;
        container.appendChild(card);
        if (showPhotoProof && appData.questPhotoProofs[tacheId]) {
            const thumb = document.getElementById(`photoThumb-${tacheId}`);
            const polaroid = document.getElementById(`photoPolaroid-${tacheId}`);
            const sentLabel = document.getElementById(`photoSentLabel-${tacheId}`);
            if (thumb) {
                thumb.src = appData.questPhotoProofs[tacheId];
            }
            if (polaroid) polaroid.style.display = 'inline-block';
            if (sentLabel) {
                sentLabel.textContent = 'Preuve envoyée !';
                sentLabel.style.display = 'block';
            }
        }
        console.log('Tâche ajoutée au DOM:', tache.nom, 'ID:', tacheId);
    });
    
    // Réinitialiser les icônes Lucide
    lucide.createIcons();
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
        const validationsResponse = await fetch(`${API_BASE}/api/attente-validation`);
        const validations = await validationsResponse.json();
        const validation = validations.validations?.find(v => v.task_id === id || v.task_nom === tache.nom);
        const user_name = validation?.user_name;
        if (!user_name) {
            showToast('Erreur : impossible de déterminer qui a accompli la quête', 'error');
            return;
        }

        const card = document.querySelector(`.mission-box button[onclick*="validateTache(${id})"]`);
        const cardEl = card ? card.closest('.mission-box') : null;
        const isChildTheme = document.body.classList.contains('theme-enfant');
        if (cardEl && isChildTheme) {
            const overlay = document.createElement('div');
            overlay.className = 'quest-explode-overlay';
            const n = 14;
            for (let i = 0; i < n; i++) {
                const angle = (i / n) * Math.PI * 2;
                const dist = 80 + Math.random() * 40;
                const star = document.createElement('span');
                star.className = 'quest-explode-star';
                star.style.setProperty('--tx', `${Math.cos(angle) * dist}px`);
                star.style.setProperty('--ty', `${Math.sin(angle) * dist}px`);
                overlay.appendChild(star);
            }
            cardEl.style.position = 'relative';
            cardEl.appendChild(overlay);
            playDingSound();
            setTimeout(() => {
                overlay.remove();
                cardEl.classList.add('quest-fly-away');
                cardEl.addEventListener('animationend', function onDone() {
                    cardEl.removeEventListener('animationend', onDone);
                    finishValidateTache(id, tache, validation);
                }, { once: true });
            }, 500);
            return;
        }
        if (cardEl) {
            cardEl.classList.add('quest-fly-away');
            cardEl.addEventListener('animationend', function onDone() {
                cardEl.removeEventListener('animationend', onDone);
                finishValidateTache(id, tache, validation);
            }, { once: true });
            return;
        }
        await finishValidateTache(id, tache, validation);
    } catch (error) {
        console.error('Erreur lors de la validation:', error);
        showToast('Erreur lors de la validation', 'error');
    }
}

async function finishValidateTache(id, tache, validation) {
    try {
        if (validation && validation.id) {
            await fetch(`${API_BASE}/api/attente-validation/${validation.id}`, { method: 'DELETE' });
        }
        await trackPendingSave(fetch(`${API_BASE}/api/taches/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ statut: 'termine' })
        }));
        const user_name = validation?.user_name;
        if (user_name) {
            // Attribution du mérite : les points vont au Héros (exécutant), pas au parent qui valide
            await fetch(`${API_BASE}/api/classement`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_name: user_name,
                    points: tache.points || 10
                })
            });
        }
        const isRecurring = tache.type === 'quotidienne' || tache.type === 'hebdomadaire';
        if (isRecurring) {
            await trackPendingSave(fetch(`${API_BASE}/api/taches/${id}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ statut: 'a_faire', responsable: '' })
            }));
        }
        const configResponse = await fetch(`${API_BASE}/api/config/famille`);
        const config = await configResponse.json();
        if (config.success) {
            const newPoints = (config.config.points_foyer || 0) + (tache.points || 10);
            await trackPendingSave(fetch(`${API_BASE}/api/config/famille`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ points_foyer: newPoints })
            }));
        }
        await loadTaches();
        await loadAttenteValidation(); /* Compteur mis à jour immédiatement ; si 0, badge masqué (display: none) */
        calculateTotalPoints();
        const heroName = user_name || 'Héros';
        const pts = tache.points || 10;
        showToast(`Félicitations ${heroName}, tu as gagné ${pts} points ! 🎉`, 'success');
        showCoinsRain();
        if (typeof confetti === 'function') {
            const gold = ['#ffd700', '#ffec8b', '#ffdf00', '#f0e68c', '#daa520'];
            confetti({ particleCount: 150, spread: 80, origin: { y: 0.65 }, colors: gold });
            confetti({ particleCount: 80, spread: 100, origin: { y: 0.6 }, scalar: 1.2, colors: gold });
            setTimeout(() => {
                confetti({ particleCount: 60, angle: 60, spread: 55, origin: { x: 0.2 }, colors: gold });
                confetti({ particleCount: 60, angle: 120, spread: 55, origin: { x: 0.8 }, colors: gold });
            }, 120);
        }
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
    submitBtn.querySelector('span').textContent = 'Création...';
    
    // Récupérer les responsables sélectionnés (cases à cocher)
    const responsablesCheckboxes = document.querySelectorAll('input[name="responsables"]:checked');
    const responsables = Array.from(responsablesCheckboxes).map(cb => cb.value);
    
    if (responsables.length === 0) {
        showToast('Choisis au moins un Héros (ou l\'Équipe de Super-Héros)', 'error');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Créer la quête';
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
            try { localStorage.removeItem(STORAGE_KEYS.task); } catch (e) {}
            if (responsables.length === 1) {
                showToast('Quête créée pour le Héros ! ✨', 'success');
            } else {
                showToast(`Quête créée pour l'Équipe de Super-Héros (${responsables.length}) ! ✨`, 'success');
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
            showToast(data.error || 'Erreur lors de la création', 'error');
            console.error('Erreur API:', data);
        }
    } catch (error) {
        console.error('Erreur lors de l\'envoi:', error);
        showToast('Erreur lors de la création de la quête', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Créer la quête';
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

function messageIsForCurrentUser(message) {
    const currentUser = getCurrentUser();
    if (!currentUser) return true;
    let dest = message.destinataires;
    if (typeof dest === 'string') {
        try {
            dest = JSON.parse(dest);
        } catch (e) {
            dest = ['toute_la_famille'];
        }
    }
    if (!Array.isArray(dest) || dest.length === 0) return true;
    if (dest.includes('toute_la_famille')) return true;
    return dest.some(d => (d || '').trim().toLowerCase() === currentUser.trim().toLowerCase());
}

// Modal lecture message agrandi
function openMessageModal(message) {
    const modal = document.getElementById('messageExpandModal');
    if (!modal) return;
    document.getElementById('messageExpandAuteur').textContent = message.auteur || '';
    document.getElementById('messageExpandTexte').textContent = message.texte || '';
    const imgContainer = document.getElementById('messageExpandImage');
    imgContainer.innerHTML = '';
    const imgUrl = (message.image_url || '').trim();
    if (imgUrl && (imgUrl.startsWith('http://') || imgUrl.startsWith('https://'))) {
        const img = document.createElement('img');
        img.src = imgUrl;
        img.alt = 'Photo du message';
        img.loading = 'lazy';
        imgContainer.appendChild(img);
    }
    document.getElementById('messageExpandDate').textContent = message.created_at ? formatDateTime24h(message.created_at) : '';
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
}

function closeMessageModal() {
    const modal = document.getElementById('messageExpandModal');
    if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }
}

// Afficher les messages (filtrés : uniquement ceux adressés à l'utilisateur ou à toute la famille)
function displayMessages(messages) {
    const messagesWall = document.getElementById('messagesWall');
    if (!messagesWall) return;
    
    messagesWall.innerHTML = '';
    
    const filtered = (messages || []).filter(messageIsForCurrentUser);
    if (filtered.length === 0) {
        messagesWall.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px; font-weight: 600; grid-column: 1 / -1;">Aucun message pour toi pour le moment</p>';
        return;
    }
    
    const sortedMessages = [...filtered].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    sortedMessages.forEach((message) => {
        const messageItem = document.createElement('div');
        messageItem.className = 'message-item';
        messageItem.dataset.messageId = message.id;
        
        const dateStr = formatDateTime24h(message.created_at);
        const imgUrl = (message.image_url || '').trim();
        const imageHtml = (imgUrl && (imgUrl.startsWith('http://') || imgUrl.startsWith('https://')))
            ? `<img class="message-item-image" src="${imgUrl.replace(/"/g, '&quot;')}" alt="" loading="lazy">`
            : '';
        
        messageItem.innerHTML = `
            <div class="message-auteur">${escapeHtml(message.auteur)}</div>
            <div class="message-texte">${escapeHtml(message.texte)}</div>
            ${imageHtml}
            <div class="message-date">${dateStr}</div>
            <button class="btn-delete" onclick="event.stopPropagation(); deleteMessage(${message.id})" title="Supprimer">
                <i data-lucide="x"></i>
            </button>
        `;
        
        messageItem.addEventListener('click', (e) => {
            if (e.target.closest('.btn-delete')) return;
            openMessageModal(message);
        });
        
        messagesWall.appendChild(messageItem);
    });
    
    lucide.createIcons();
}

function initMessagePhotoPicker() {
    const btn = document.getElementById('messagePhotoBtn');
    const input = document.getElementById('message-photo-input');
    const preview = document.getElementById('message-photo-preview');
    if (!btn || !input || !preview) return;
    btn.addEventListener('click', () => input.click());
    input.addEventListener('change', async () => {
        const file = input.files && input.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('image', file);
        try {
            const res = await fetch(`${API_BASE}/api/upload-message-image`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json().catch(() => ({}));
            if (data.success && data.url) {
                window._pendingMessageImageUrl = data.url;
                preview.innerHTML = `
                    <img src="${data.url}" alt="Aperçu">
                    <button type="button" class="message-photo-remove" id="messagePhotoRemove">Retirer</button>
                `;
                document.getElementById('messagePhotoRemove').addEventListener('click', () => {
                    window._pendingMessageImageUrl = null;
                    preview.innerHTML = '';
                    input.value = '';
                });
            } else {
                showToast(data.error || 'Erreur upload image', 'error');
            }
        } catch (err) {
            console.error(err);
            showToast('Erreur lors de l\'upload', 'error');
        }
        input.value = '';
    });
}


// Gérer la soumission du formulaire de message
async function handleMessageSubmit(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = 'Publication...';
    
    const auteur = getCurrentUser() || '';
    if (!auteur) {
        showToast('Choisis qui tu es (Qui es-tu ?) pour envoyer un message', 'error');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Publier le message';
        return;
    }
    const checked = document.querySelectorAll('input[name="destinataires"]:checked');
    let destinataires = Array.from(checked).map(cb => cb.value);
    if (destinataires.length === 0) {
        showToast('Choisis au moins un destinataire (ou Toute la famille)', 'error');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Publier le message';
        return;
    }
    if (destinataires.includes('toute_la_famille')) {
        destinataires = ['toute_la_famille'];
    }
    const texteEl = document.getElementById('message-texte');
    if (!texteEl || !texteEl.value.trim()) {
        showToast('Écris ton message', 'error');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Publier le message';
        return;
    }
    const formData = {
        auteur: String(auteur),
        texte: texteEl.value.trim(),
        destinataires: destinataires
    };
    if (window._pendingMessageImageUrl) {
        formData.image_url = window._pendingMessageImageUrl;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json().catch(() => ({}));
        
        if (data.success) {
            try { localStorage.removeItem(STORAGE_KEYS.message); } catch (e) {}
            showToast('Message publié ! 💌', 'success');
            e.target.reset();
            document.querySelectorAll('input[name="destinataires"]').forEach(cb => { cb.checked = false; });
            window._pendingMessageImageUrl = null;
            const preview = document.getElementById('message-photo-preview');
            if (preview) preview.innerHTML = '';
            await loadMessages();
        } else {
            showToast(data.error || 'Erreur lors de la publication', 'error');
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
    const messagesForMe = messages.filter(messageIsForCurrentUser);
    if (nbMessagesEl) nbMessagesEl.textContent = messagesForMe.length;
    
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

let _photoForTacheId = null;

function prendrePhoto(tacheId) {
    _photoForTacheId = tacheId;
    const input = document.getElementById('capture-photo');
    if (input) {
        input.value = '';
        input.click();
    }
}

function playDingSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 880;
        osc.type = 'sine';
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.2);
    } catch (e) {
        console.debug('Son ding non disponible', e);
    }
}

function showCoinsRain() {
    let wrap = document.getElementById('coins-rain');
    if (wrap) wrap.remove();
    wrap = document.createElement('div');
    wrap.id = 'coins-rain';
    const count = 12;
    for (let i = 0; i < count; i++) {
        const coin = document.createElement('span');
        coin.className = 'coin-fall';
        coin.style.left = Math.random() * 100 + '%';
        coin.style.animationDelay = (i * 0.08) + 's';
        wrap.appendChild(coin);
    }
    document.body.appendChild(wrap);
    setTimeout(() => wrap.remove(), 2500);
}

function handleCapturePhotoChange(e) {
    const input = e.target;
    const file = input && input.files && input.files[0];
    if (!file || !file.type.startsWith('image/')) {
        _photoForTacheId = null;
        return;
    }
    const tacheId = _photoForTacheId;
    _photoForTacheId = null;
    const reader = new FileReader();
    reader.onload = function(ev) {
        const dataUrl = ev.target.result;
        appData.questPhotoProofs[tacheId] = dataUrl;
        const thumb = document.getElementById(`photoThumb-${tacheId}`);
        const polaroid = document.getElementById(`photoPolaroid-${tacheId}`);
        const sentLabel = document.getElementById(`photoSentLabel-${tacheId}`);
        if (thumb) thumb.src = dataUrl;
        if (polaroid) polaroid.style.display = 'inline-block';
        if (sentLabel) {
            sentLabel.textContent = 'Preuve envoyée !';
            sentLabel.style.display = 'block';
        }
        showToast('📸 Preuve envoyée !', 'success');
    };
    reader.readAsDataURL(file);
    input.value = '';
}

function handleQuestPhoto(tacheId, inputElement) {
    const file = inputElement && inputElement.files && inputElement.files[0];
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        appData.questPhotoProofs[tacheId] = e.target.result;
        const thumb = document.getElementById(`photoThumb-${tacheId}`);
        const polaroid = document.getElementById(`photoPolaroid-${tacheId}`);
        const sentLabel = document.getElementById(`photoSentLabel-${tacheId}`);
        if (thumb) thumb.src = e.target.result;
        if (polaroid) polaroid.style.display = 'inline-block';
        if (sentLabel) {
            sentLabel.textContent = 'Preuve envoyée !';
            sentLabel.style.display = 'block';
        }
        showToast('📸 Preuve envoyée !', 'success');
    };
    reader.readAsDataURL(file);
    inputElement.value = '';
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
        return tache.responsables.map(r => escapeHtml(r)).join(', ');
    } else if (tache.responsable) {
        return escapeHtml(tache.responsable);
    }
    return 'Non défini';
}

function getHeroesLabel(tache) {
    let n = 0;
    if (tache.responsables && Array.isArray(tache.responsables)) {
        n = tache.responsables.filter(r => r && String(r).trim()).length;
    } else if (tache.responsable) {
        n = 1;
    }
    return n > 1 ? "L'Équipe de Super-Héros" : "Héros";
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
    
    showToast('📋 Quête chargée ! Modifiez si besoin puis créez.', 'success');
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
    updateQuestFormVisibility();
    applyBodyTheme();
}

function updateFamilleTabVisibility() {
    const tabFamille = document.getElementById('tabFamille');
    if (tabFamille) {
        tabFamille.style.display = appData.isParent ? 'flex' : 'none';
    }
}

function updateQuestFormVisibility() {
    const section = document.getElementById('questFormSection');
    if (section) {
        section.style.display = appData.isParent ? 'block' : 'none';
    }
}

function applyBodyTheme() {
    const user = getCurrentUser();
    document.body.classList.remove('theme-enfant', 'theme-ado', 'theme-parent');
    if (!user || !appData.configFamille) return;
    const parents = appData.configFamille.parents || [];
    const ados = appData.configFamille.ados || [];
    const enfants = appData.configFamille.enfants || [];
    if (parents.includes(user)) {
        document.body.classList.add('theme-parent');
    } else if (ados.includes(user)) {
        document.body.classList.add('theme-ado');
    } else if (enfants.includes(user)) {
        document.body.classList.add('theme-enfant');
    }
}

function updateQuestProgressBar() {
    const bar = document.getElementById('questProgressBar');
    const fill = document.getElementById('questProgressFill');
    const label = document.getElementById('questProgressLabel');
    if (!bar || !fill || !label) return;
    const total = appData.taches.length;
    const completed = appData.taches.filter(t => t.statut === 'termine').length;
    const active = total - completed;
    if (total === 0) {
        bar.setAttribute('aria-hidden', 'true');
        return;
    }
    bar.setAttribute('aria-hidden', 'false');
    const pct = Math.round((completed / total) * 100);
    fill.style.width = pct + '%';
    label.textContent = `Quêtes accomplies : ${completed} / ${total}`;
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
            const isParentUser = appData.configFamille &&
                (appData.configFamille.parents || []).includes(selectedUser);

            if (isParentUser && !appData.isParent) {
                _pendingParentAuth = selectedUser;
                showToast('🔐 Entre le code du Grand Mage', 'info');
                openAuthModal();
                return;
            }

            setCurrentUser(selectedUser);
            checkIfParent(selectedUser);
            showToast(`Connecté en tant que ${selectedUser}`, 'success');
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
        
        // Toujours afficher le dernier utilisateur dans le sélecteur (mémorisation localStorage)
        if (allMembers.includes(savedUser)) {
            userSelect.value = savedUser;
            const isParentUser = (appData.configFamille.parents || []).includes(savedUser);
            if (isParentUser && !appData.isParent) {
                // Parent : on restaure l'affichage "Qui es-tu ?" mais pas les droits parent (PIN requis)
                appData.currentUser = savedUser;
                // localStorage déjà rempli par la session précédente
                return;
            }
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
let _pendingParentAuth = null;

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
        const errEl = document.getElementById('authError');
        if (errEl) errEl.style.display = 'none';
    }
    if (_pendingParentAuth && !appData.isParent) {
        const userSelect = document.getElementById('currentUser');
        if (userSelect) userSelect.value = '';
        appData.currentUser = null;
        showToast('Profil parent annulé. Choisis qui tu es.', 'info');
    }
    _pendingParentAuth = null;
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
            const parentSelected = _pendingParentAuth;
            _pendingParentAuth = null;
            updateParentIndicator();
            updateFamilleTabVisibility();
            closeAuthModal();
            showToast('✅ Bienvenue, Grand Mage !', 'success');
            const userSelect = document.getElementById('currentUser');
            if (userSelect && parentSelected) {
                userSelect.value = parentSelected;
                setCurrentUser(parentSelected);
                checkIfParent(parentSelected);
            }
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
        const response = await trackPendingSave(fetch(`${API_BASE}/api/config/famille`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(appData.configFamille)
        }));
        
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
    if (!currentUser) {
        showToast('Choisis qui tu es (Qui es-tu ?) pour terminer la mission', 'error');
        return;
    }
    
    const validation = await canValidateTask(id, currentUser);
    if (!validation.canValidate) {
        showToast(validation.message, 'error');
        return;
    }
    
    // Validation automatique si le héros est un parent
    if (appData.isParent) {
        try {
            const today = new Date().toISOString().split('T')[0];
            await trackPendingSave(fetch(`${API_BASE}/api/taches/${id}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ statut: 'termine' })
            }));
            await fetch(`${API_BASE}/api/taches-completees`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: id,
                    task_nom: tache.nom,
                    user_name: currentUser,
                    date_completion: today,
                    points: tache.points || 10,
                    validated: true
                })
            });
            await fetch(`${API_BASE}/api/classement`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_name: currentUser, points: tache.points || 10 })
            });
            const configRes = await fetch(`${API_BASE}/api/config/famille`);
            const configData = await configRes.json();
            if (configData.success && configData.config) {
                const newPoints = (configData.config.points_foyer || 0) + (tache.points || 10);
                await trackPendingSave(fetch(`${API_BASE}/api/config/famille`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ points_foyer: newPoints })
                }));
            }
            const isRecurring = tache.type === 'quotidienne' || tache.type === 'hebdomadaire';
            if (isRecurring) {
                await trackPendingSave(fetch(`${API_BASE}/api/taches/${id}`, {
                    method: 'PATCH',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ statut: 'a_faire', responsable: '' })
                }));
            }
            await loadTaches();
            calculateTotalPoints();
            showToast(`Mission validée ! +${tache.points || 10} pts 🎉`, 'success');
            showCoinsRain();
            if (typeof confetti === 'function') {
                const gold = ['#ffd700', '#ffec8b', '#daa520'];
                confetti({ particleCount: 100, spread: 70, origin: { y: 0.65 }, colors: gold });
            }
        } catch (e) {
            console.error(e);
            showToast('Erreur lors de la validation', 'error');
        }
        return;
    }
    
    try {
        const response = await trackPendingSave(fetch(`${API_BASE}/api/taches/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ statut: 'en_attente' })
        }));
        
        if (response.ok) {
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
            await loadTaches();
        } else {
            showToast('Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        console.error('Erreur lors de la complétion:', error);
        showToast('Erreur lors de la complétion', 'error');
    }
}

async function assignMeToTask(tacheId) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('Choisis qui tu es (Qui es-tu ?) pour t\'assigner', 'error');
        return;
    }
    try {
        const res = await trackPendingSave(fetch(`${API_BASE}/api/taches/${tacheId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ responsable: currentUser, statut: 'en_cours' })
        }));
        if (res.ok) {
            showToast('Tu t\'es assigné à cette quête ! 🙋', 'success');
            await loadTaches();
            lucide.createIcons();
        } else {
            showToast('Erreur lors de l\'assignation', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Erreur lors de l\'assignation', 'error');
    }
}

let _heroChoiceTacheId = null;
function openHeroChoiceModal(tacheId) {
    _heroChoiceTacheId = tacheId;
    const modal = document.getElementById('heroChoiceModal');
    const list = document.getElementById('heroChoiceList');
    if (!modal || !list) return;
    const tache = appData.taches.find(t => t.id === tacheId);
    const members = (tache && tache.responsables && Array.isArray(tache.responsables))
        ? tache.responsables
        : [
            ...(appData.configFamille?.parents || []),
            ...(appData.configFamille?.ados || []),
            ...(appData.configFamille?.enfants || [])
        ];
    list.innerHTML = members.map(name => {
        const safeName = escapeHtml(String(name || ''));
        const initial = (name || '')[0].toUpperCase();
        return `<button type="button" class="hero-bubble" data-hero-name="${safeName.replace(/"/g, '&quot;')}">
            <span class="hero-bubble-avatar">${initial}</span>
            <span class="hero-bubble-name">${safeName}</span>
        </button>`;
    }).join('');
    list.querySelectorAll('.hero-bubble').forEach(btn => {
        btn.addEventListener('click', () => {
            const heroName = btn.getAttribute('data-hero-name');
            if (heroName) chooseHeroForTask(heroName);
        });
    });
    modal.style.display = 'flex';
    if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();
}

function closeHeroChoiceModal() {
    const modal = document.getElementById('heroChoiceModal');
    if (modal) modal.style.display = 'none';
    _heroChoiceTacheId = null;
}

async function chooseHeroForTask(userName) {
    const tacheId = _heroChoiceTacheId;
    closeHeroChoiceModal();
    if (!tacheId) return;
    try {
        const res = await trackPendingSave(fetch(`${API_BASE}/api/taches/${tacheId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ responsable: userName, statut: 'en_cours' })
        }));
        if (res.ok) {
            showToast(`${userName} s'en occupe ! 🙋`, 'success');
            await loadTaches();
            lucide.createIcons();
        } else {
            showToast('Erreur lors de l\'assignation', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Erreur lors de l\'assignation', 'error');
    }
}

// Charger les validations en attente (compteur réel Supabase). Badge masqué si 0.
async function loadAttenteValidation() {
    const waitingMsg = document.querySelector('.waiting-msg-global');
    if (!appData.isParent) {
        appData.attenteValidation = [];
        if (waitingMsg) {
            waitingMsg.style.opacity = '0';
            setTimeout(() => {
                waitingMsg.textContent = '';
                waitingMsg.style.display = 'none';
            }, 300);
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/attente-validation`);
        const data = await response.json();
        
        appData.attenteValidation = data.validations || [];
        const count = Array.isArray(data.validations) ? data.validations.length : 0;
        
        if (waitingMsg) {
            if (count > 0) {
                waitingMsg.textContent = `⏳ ${count} mission(s) en attente de validation !`;
                waitingMsg.style.display = 'block';
                waitingMsg.style.opacity = '1';
            } else {
                waitingMsg.style.opacity = '0';
                setTimeout(() => {
                    waitingMsg.textContent = '';
                    waitingMsg.style.display = 'none';
                }, 300);
            }
        }
    } catch (error) {
        console.error('Erreur lors du chargement des validations:', error);
        if (waitingMsg) {
            waitingMsg.style.opacity = '0';
            setTimeout(() => {
                waitingMsg.textContent = '';
                waitingMsg.style.display = 'none';
            }, 300);
        }
    }
}
