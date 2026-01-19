/**
 * Script de gestion dynamique des utilisateurs pour Cluster et Destination.    
 * 
 * /**
 * Script de gestion dynamique des utilisateurs pour Cluster et Destination.
 */
document.addEventListener('DOMContentLoaded', function() {
    // --- 1. INITIALISATION ET RÉCUPÉRATION DES ÉLÉMENTS ---
    const clusterField = document.getElementById('id_code_cluster');
    const destField = document.getElementById('id_code_dest');
    const newUserButtons = document.querySelectorAll('[data-target-field]');

    console.log("--- Initialisation du script ---");
    console.log("Nombre de boutons de création trouvés :", newUserButtons.length);

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
     * Rafraîchit tous les champs Select d'utilisateurs
     */
    async function refreshUserSelectFields() {
        const clusterCode = clusterField?.value || '';
        const destCode = destField?.value || '';
        
        console.log(`Rafraîchissement des listes (Cluster: ${clusterCode}, Dest: ${destCode})`);
        
        if (!clusterCode) {
            console.warn("Pas de code cluster, abandon du rafraîchissement.");
            return;
        }

        const params = new URLSearchParams({ code_cluster: clusterCode, code_dest: destCode });

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
                    select.innerHTML = '<option value="">---------</option>';
                    users.forEach(u => select.add(new Option(u.text, u.id)));
                    select.value = currentVal;
                }
            });
            console.log("Mise à jour des listes Select réussie.");
        } catch (err) { 
            console.error("Erreur de rafraîchissement:", err); 
        }
    }

    // Écouteurs sur les changements de code
    [clusterField, destField].forEach(el => {
        el?.addEventListener('change', () => {
            console.log(`Changement détecté sur le champ : ${el.id}`);
            refreshUserSelectFields();
        });
    });

    /**
     * GESTION DE LA CRÉATION D'UTILISATEUR
     */
    newUserButtons.forEach(button => {
        button.addEventListener('click', async function() {
            // Déclaration des cibles issues du bouton
            const targetFieldId = this.getAttribute('data-target-field');
            const pendingFieldId = this.getAttribute('data-pending-field');

            console.group("Action : Ouverture Modale Création");
            console.log("Bouton cliqué :", this);
            console.log("ID Target (Select) :", targetFieldId);
            console.log("ID Pending (Hidden) :", pendingFieldId);
            console.groupEnd();

            // 1. Récupération des langues
            let langOptions = "";
            try {
                const res = await fetch(`/${document.documentElement.lang || 'fr'}/core/get-languages/`);
                const langs = await res.json();
                langOptions = langs.map(l => `<option value="${l.code}">${l.name}</option>`).join('');
            } catch (e) { console.error("Erreur fetch langues:", e); }

            // 2. Ouverture de la modale SweetAlert2
            Swal.fire({
                title: gettext('Créer un utilisateur'),
                html: `
                    <div class="text-start">
                        <input type="email" id="swal-email" class="swal2-input" placeholder="${gettext('Email')}" required>
                        <input type="text" id="swal-first" class="swal2-input" placeholder="${gettext('Prénom')}" required>
                        <input type="text" id="swal-last" class="swal2-input" placeholder="${gettext('Nom')}" required>
                        <input type="text" id="swal-phone" class="swal2-input" placeholder="${gettext('Téléphone')}">
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

                    console.log("Tentative d'envoi du payload :", payload);
                    console.log("Jeton CSRF utilisé :", csrfToken);

                    if (!csrfToken) {
                        Swal.showValidationMessage(gettext('Erreur de sécurité : Jeton CSRF manquant.'));
                        return;
                    }

                    if (!payload.email || !payload.first_name || !payload.last_name) {
                        Swal.showValidationMessage(gettext('Veuillez remplir les champs obligatoires'));
                        return;
                    }

                    return fetch(getBaseUrl(), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify(payload)
                    })
                    .then(response => {
                        if (!response.ok) return response.json().then(err => { throw new Error(err.erreur); });
                        return response.json();
                    })
                    .catch(error => {
                        console.error("Erreur lors de l'appel POST :", error);
                        Swal.showValidationMessage(error.message);
                    });
                }
            }).then(async (result) => {
                if (result.isConfirmed && result.value) {
                    const newUser = result.value;
                    console.log("Nouvel utilisateur créé avec succès :", newUser);

                    // Mise à jour de toutes les listes
                    await refreshUserSelectFields();

                    // Sélection automatique dans le champ ciblé
                    const selectEl = document.getElementById(targetFieldId);
                    if (selectEl) {
                        selectEl.value = newUser.id;
                        console.log(`Champ Select (${targetFieldId}) mis à jour.`);
                    }

                    // Remplissage du champ caché (pending)
                    const hiddenEl = document.getElementById(pendingFieldId);
                    if (hiddenEl) {
                        hiddenEl.value = newUser.id;
                        console.log(`Champ Pending (${pendingFieldId}) mis à jour.`);
                    }

                    Swal.fire(gettext('Succès'), gettext('Utilisateur saisi avec succès.'), 'success');
                }
            });
        });
    });

    window.refreshUserSelectFields = refreshUserSelectFields;
});