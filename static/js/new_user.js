/**
 * Script de gestion dynamique des utilisateurs pour Cluster et Destination.
 */
document.addEventListener('DOMContentLoaded', function() {
    // 1. Initialisation des éléments et détection du contexte
    const clusterField = document.getElementById('id_code_cluster');
    const destField = document.getElementById('id_code_dest');
    const newUserButtons = document.querySelectorAll('[data-target-field]');
    
    // Détection du type de formulaire (défini via Crispy FormHelper)
    let formElement = document.querySelector('form[data-form-type]');
    let formType = 'default';

    if (formElement) {
        formType = formElement.getAttribute('data-form-type');
    } else if (destField) {
        formType = 'destination'; // Si le champ code_dest existe, on est forcément dans ce contexte
    }

    console.log("--- Initialisation du script ---");
    console.log("Boutons de création détectés :", newUserButtons.length);
    console.log("Contexte formulaire détecté :", formType);

    /**
     * Vide tous les sélecteurs d'utilisateurs
     */
    function clearUserSelects() {
        const userSelectIds = [
            'id_admin_cluster', 'id_admin_alt_cluster', 'id_manager_dest', 
            'id_referent_dest', 'id_matcher_dest', 'id_matcher_alt_dest', 'id_finance_dest'
        ];
        console.log("[Clean] Vidage des sélecteurs d'utilisateurs.");
        userSelectIds.forEach(id => {
            const select = document.getElementById(id);
            if (select) select.innerHTML = '<option value="">---------</option>';
        });
    }

    /**
     * Récupère le jeton CSRF
     */
    function getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput && csrfInput.value) return csrfInput.value;
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const getBaseUrl = () => {
        const lang = document.documentElement.lang || 'fr';
        return `/${lang}/core/get-users/`;
    };

    /**
     * Rafraîchit les selects selon les codes Cluster et Destination
     */
    async function refreshUserSelectFields(forceValue, targetId) {
        const clusterCode = clusterField?.value || '';
        const destCode = destField?.value || '';
        
        console.log(`[Refresh] Début (Form: ${formType}, Cluster: ${clusterCode}, Dest: ${destCode})`);
        
        // --- LOGIQUE DE FILTRAGE STRICTE ---
        if (formType === 'destination') {
            // Dans le formulaire Destination, les deux sont obligatoires
            if (!clusterCode || !destCode) {
                console.warn("[Refresh] Annulé : Cluster ou Destination manquant pour le mode 'destination'.");
                clearUserSelects();
                return;
            }
        } else {
            // Dans le formulaire Cluster (ou autre), seul le cluster est obligatoire
            if (!clusterCode) {
                console.warn("[Refresh] Annulé : ClusterCode obligatoire.");
                clearUserSelects();
                return;
            }
        }

        const params = new URLSearchParams({ code_cluster: clusterCode, code_dest: destCode });
        console.log("[Fetch] Récupération des utilisateurs avec params :", params.toString());
        
        try {
            const response = await fetch(`${getBaseUrl()}?${params.toString()}`);
            if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);
            
            const users = await response.json();
            console.log(`[Fetch] Utilisateurs reçus (${users.length}) :`, users);
            const userSelectIds = [
                'id_admin_cluster', 'id_admin_alt_cluster', 'id_manager_dest', 
                'id_referent_dest', 'id_matcher_dest', 'id_matcher_alt_dest', 'id_finance_dest'
            ];

            userSelectIds.forEach(id => {
                const select = document.getElementById(id);
                if (select) {
                    const currentVal = select.value;
                    console.log(`[A mettre à jour] Champ '${id}' (Valeur forcée: ${forceValue || 'aucune'})`);
                    
                    select.innerHTML = '<option value="">---------</option>';
                    users.forEach(u => select.add(new Option(u.text, u.id)));
                    
                    // Mise à jour de la sélection
                    if (id === targetId && forceValue) {
                        select.value = forceValue;
                        console.log(`[Selection] Champ '${id}' fixé sur le nouvel utilisateur ID: ${forceValue}`);
                    } else {
                        select.value = currentVal;
                    }
                }
            });
        } catch (err) { 
            console.error("Erreur rafraîchissement:", err);
            clearUserSelects(); 
        }
    }

    // Écouteurs sur les changements de code
    [clusterField, destField].forEach(el => {
        el?.addEventListener('change', () => {
            console.log(`[Event] Changement sur ${el.id}`);
            refreshUserSelectFields();
        });
    });

    /**
     * Gestion de la création d'utilisateur via SweetAlert2
     */
    newUserButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const targetFieldId = this.getAttribute('data-target-field');
            const pendingFieldId = this.getAttribute('data-pending-field');

            console.group("--- Création Utilisateur ---");
            console.log("Cible (Select)  :", targetFieldId);
            console.log("Cible (Pending) :", pendingFieldId);
            console.groupEnd();

            let langOptions = "";
            try {
                const res = await fetch(`/${document.documentElement.lang || 'fr'}/core/get-languages/`);
                const langs = await res.json();
                langOptions = langs.map(l => `<option value="${l.code}">${l.name}</option>`).join('');
            } catch (e) { console.error("Erreur langues:", e); }

            Swal.fire({
                title: gettext('Créer un utilisateur'),
                html: `
                    <div class="text-start">
                        <input type="email" id="swal-email" class="swal2-input" placeholder="${gettext('Email')}" autocomplete="off" required>
                        <input type="text" id="swal-first" class="swal2-input" placeholder="${gettext('Prénom')}" autocomplete="off" required>
                        <input type="text" id="swal-last" class="swal2-input" placeholder="${gettext('Nom')}" autocomplete="off" required>
                        <input type="text" id="swal-phone" class="swal2-input" placeholder="${gettext('Téléphone')}" autocomplete="off">
                        <select id="swal-lang" class="swal2-select" style="width:70%">${langOptions}</select>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: gettext('Créer'),
                preConfirm: () => {
                    const csrfToken = getCsrfToken();
                    const payload = {
                        email: document.getElementById('swal-email').value,
                        first_name: document.getElementById('swal-first').value,
                        last_name: document.getElementById('swal-last').value,
                        cellphone: document.getElementById('swal-phone').value,
                        lang_com: document.getElementById('swal-lang').value
                    };

                    console.log("[POST] Envoi des données :", payload);

                    if (!csrfToken) {
                        Swal.showValidationMessage(gettext('Jeton CSRF manquant.'));
                        return;
                    }

                    return fetch(getBaseUrl(), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                        body: JSON.stringify(payload)
                    })
                    .then(response => {
                        if (!response.ok) return response.json().then(err => { throw new Error(err.erreur); });
                        return response.json();
                    })
                    .catch(error => Swal.showValidationMessage(error.message));
                }
            }).then(async (result) => {
                if (result.isConfirmed && result.value) {
                    const newUser = result.value;
                    console.log("[Succès] Utilisateur créé :", newUser.id);
                    
                    await refreshUserSelectFields(newUser.id, targetFieldId);

                    const hiddenEl = document.getElementById(pendingFieldId);
                    if (hiddenEl) {
                        hiddenEl.value = newUser.id;
                        console.log(`[Pending] '${pendingFieldId}' mis à jour.`);
                    }

                    Swal.fire(gettext('Succès'), gettext('Utilisateur créé et sélectionné.'), 'success');
                }
            });
        });
    });

    window.refreshUserSelectFields = refreshUserSelectFields;
});