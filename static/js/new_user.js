/**
 * Script de gestion dynamique des utilisateurs pour Cluster et Destination.    
 * 
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des éléments globaux
    const clusterField = document.getElementById('id_code_cluster');
    const destField = document.getElementById('id_code_dest');
    const newUserButtons = document.querySelectorAll('[data-target-field]');

    console.log("--- Initialisation du script ---");
    console.log("Boutons de création détectés :", newUserButtons.length);

    /**
     * Récupère le jeton CSRF de manière robuste.
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
     * Rafraîchit les selects et force la sélection si un nouvel ID est fourni.
     */
    async function refreshUserSelectFields(forceValue, targetId) {
        const clusterCode = clusterField?.value || '';
        const destCode = destField?.value || '';
        
        console.log(`[Refresh] Début du rafraîchissement (Cluster: ${clusterCode}, Dest: ${destCode})`);
        
        if (!clusterCode) {
        throw new Error("Opération annulée : le 'clusterCode' est obligatoire.");
        };

        const params = new URLSearchParams({ code_cluster: clusterCode, code_dest: destCode });
        console.log("[Fetch] Récupération des utilisateurs avec params :", params.toString());
        try {
            const response = await fetch(`${getBaseUrl()}?${params.toString()}`);
            const users = await response.json();

            const userSelectIds = [
                'id_admin_cluster', 'id_admin_alt_cluster', 'id_manager_dest', 
                'id_referent_dest', 'id_matcher_dest', 'id_matcher_alt_dest', 'id_finance_dest'
            ];

            userSelectIds.forEach(id => {
                const select = document.getElementById(id);
                if (select) {
                    const currentVal = select.value;
                    console.log(`[A mettre à jour] Mise à jour du champ '${id}' (Valeur actuelle: ${forceValue})`);
                    select.innerHTML = '<option value="">---------</option>';
                    users.forEach(u => select.add(new Option(u.text, u.id)));
                    
                    // Mise en avant si c'est le champ ciblé
                    if (id === targetId && forceValue) {
                        select.value = forceValue;
                        console.log(`[Selection] Champ '${id}' mis à jour avec le nouvel utilisateur (ID: ${forceValue})`);
                    } else {
                        select.value = currentVal;
                    }
                }
            });
        } catch (err) { console.error("Erreur rafraîchissement:", err); }
    }

    // Écouteurs sur les changements de code
    [clusterField, destField].forEach(el => {
        el?.addEventListener('change', () => {
            console.log(`[Event] Changement sur ${el.id}`);
            refreshUserSelectFields();
        });
    });

    /**
     * Gestion de la création d'utilisateur
     */
    newUserButtons.forEach(button => {
        button.addEventListener('click', async function() {
            // Déclaration des cibles
            const targetFieldId = this.getAttribute('data-target-field');
            const pendingFieldId = this.getAttribute('data-pending-field');

            console.group("--- Création Utilisateur ---");
            console.log("Cible (Select)  :", targetFieldId);
            console.log("Cible (Pending) :", pendingFieldId);
            console.groupEnd();

            // Récupération des langues pour la modale
            let langOptions = "";
            try {
                const res = await fetch(`/${document.documentElement.lang || 'fr'}/core/get-languages/`);
                const langs = await res.json();
                langOptions = langs.map(l => `<option value="${l.code}">${l.name}</option>`).join('');
            } catch (e) { console.error(e); }

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
                    console.log("[Succès] Utilisateur créé avec l'ID :", newUser.id);
                    console.log("Détails du champ cible:", targetFieldId);
                    // Mise à jour et pré-remplissage du Select
                    await refreshUserSelectFields(newUser.id, targetFieldId);

                    // Mise à jour du champ caché PENDING
                    const hiddenEl = document.getElementById(pendingFieldId);
                    if (hiddenEl) {
                        hiddenEl.value = newUser.id;
                        console.log(`[Pending] Champ '${pendingFieldId}' mis à jour avec la valeur :`, hiddenEl.value);
                    } else {
                        console.warn(`[Pending] Le champ caché '${pendingFieldId}' est introuvable dans le DOM.`);
                    }

                    Swal.fire(gettext('Succès'), gettext('Utilisateur créé et sélectionné.'), 'success');
                }
            });
        });
    });

    window.refreshUserSelectFields = refreshUserSelectFields;
});