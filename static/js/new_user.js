/**
 * Script de gestion dynamique des utilisateurs pour Cluster et Destination.
 */
document.addEventListener('DOMContentLoaded', function() {
    const clusterField = document.getElementById('id_code_cluster');
    const destField = document.getElementById('id_code_dest');
    const newUserButtons = document.querySelectorAll('[data-target-field]');

    /**
     * Récupère le jeton CSRF de manière robuste.
     * Priorité à l'input masqué (64 car.) généré par {% csrf_token %}
     * Fallback sur le cookie (32 car.)
     */
    function getCsrfToken() {
        // 1. Essayer de trouver l'input masqué de Django
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput && csrfInput.value) {
            return csrfInput.value;
        }
        // 2. Fallback sur le cookie
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

    /** 
     * Récupère les paramètres de langue et l'URL de base
     */
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
        if (!clusterCode) return;

        const params = new URLSearchParams({ code_cluster: clusterCode, code_dest: destCode });

        try {
            const response = await fetch(`${getBaseUrl()}?${params.toString()}`);
            const users = await response.json();

            // Liste de tous les IDs de Select possibles
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
        } catch (err) { console.error("Erreur de rafraîchissement:", err); }
    }

    // Écouteurs sur les changements de code
    [clusterField, destField].forEach(el => el?.addEventListener('change', refreshUserSelectFields));

    /**
     * Gestion de la création d'utilisateur
     */
    newUserButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const btn = this; // Référence au bouton pour accéder aux data-attributes
            const targetFieldId = btn.getAttribute('data-target-field');
            const pendingFieldId = btn.getAttribute('data-pending-field');
            

            // 1. Récupération des langues pour la modale
            let langOptions = "";
            try {
                const res = await fetch(`/${document.documentElement.lang || 'fr'}/core/get-languages/`);
                const langs = await res.json();
                langOptions = langs.map(l => `<option value="${l.code}">${l.name}</option>`).join('');
            } catch (e) { console.error(e); }

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
                    
                    // Debug console pour vérifier la validité du token avant envoi
                    console.log("Token CSRF envoyé :", csrfToken);
                    console.log("Longueur du token :", csrfToken ? csrfToken.length : 0);
                    console.log("Champ Pending");
                    
                    const payload = {
                        email: document.getElementById('swal-email').value,
                        first_name: document.getElementById('swal-first').value,
                        last_name: document.getElementById('swal-last').value,
                        cellphone: document.getElementById('swal-phone').value,
                        lang_com: document.getElementById('swal-lang').value
                    };


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
                    .catch(error => Swal.showValidationMessage(error.message));
                }
            }).then(async (result) => {
                if (result.isConfirmed && result.value) {
                    const newUser = result.value;

                    // Mise à jour de toutes les listes
                    await refreshUserSelectFields();

                    // Sélection automatique dans le champ ciblé
                    const selectEl = document.getElementById(targetFieldId);
                    if (selectEl) selectEl.value = newUser.id;

                    // Remplissage du champ caché SPÉCIFIQUE via l'attribut Data
                    const hiddenEl = document.getElementById(pendingFieldId);
                    if (hiddenEl) hiddenEl.value = newUser.id;

                    Swal.fire(gettext('Succès'), gettext('Utilisateur saisi avec succès.'), 'success');
                }
            });
        });
    });

    window.refreshUserSelectFields = refreshUserSelectFields;
});