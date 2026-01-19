document.addEventListener('DOMContentLoaded', function() {
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

    async function fetchLanguages(lang) {
        const response = await fetch(`/${lang}/core/get-languages/`);
        if (!response.ok) throw new Error('Failed to fetch languages');
        return await response.json();
    }

    async function refreshUserSelectFields(lang) {
        const codeCluster = document.getElementById('id_code_cluster')?.value ?? '';
        const codeDest = document.getElementById('id_code_dest')?.value ?? '';

        const params = new URLSearchParams();
        if (codeCluster) params.append('code_cluster', codeCluster);
        if (codeDest) params.append('code_dest', codeDest);

        const response = await fetch(`/${lang}/core/get-users/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch users');
        const users = await response.json();

        const userSelectFields = [
            'id_admin_cluster', 'id_admin_alt_cluster', 
            'id_manager_dest', 'id_referent_dest', 'id_matcher_dest', 
            'id_matcher_alt_dest', 'id_finance_dest'
        ];

        userSelectFields.forEach(fieldId => {
            const selectElement = document.getElementById(fieldId);
            if (selectElement) {
                const currentValue = selectElement.value;
                selectElement.innerHTML = '<option value="">---------</option>';
                users.forEach(user => {
                    const option = new Option(`${user.last_name} ${user.first_name}`, user.id);
                    selectElement.add(option);
                });
                if (currentValue) selectElement.value = currentValue;
            }
        });
    }   

    newUserButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const targetField = this.getAttribute('data-target-field');
            const pathParts = window.location.pathname.split('/');
            const lang = pathParts[1];
            const url = `/${lang}/core/users_create/`;
            
            let languages = [];
            try { languages = await fetchLanguages(lang); } catch (e) { console.error(e); }

            let langOptions = languages.map(l => `<option value="${l.code}">${l.name}</option>`).join('');

            Swal.fire({
                title: gettext('Créer un nouvel utilisateur'),
                html: `
                    <form id="newUserForm" class="swal2-form text-start">
                        <input type="email" id="email" class="swal2-input" placeholder="${gettext('Email')}" required>
                        <input type="text" id="first_name" class="swal2-input" placeholder="${gettext('Prénom')}" required>
                        <input type="text" id="last_name" class="swal2-input" placeholder="${gettext('Nom')}" required>
                        <input type="text" id="cellphone" class="swal2-input" placeholder="${gettext('Téléphone')}">
                        <select id="lang_com" class="swal2-select" required style="width:70%">${langOptions}</select>
                    </form>
                `,
                showCancelButton: true,
                confirmButtonText: gettext('Créer'),
                cancelButtonText: gettext('Annuler'),
                preConfirm: () => {
                    const csrfToken = getCsrfToken();
                    
                    // Debug console pour vérifier la validité du token avant envoi
                    console.log("Token CSRF envoyé :", csrfToken);
                    console.log("Longueur du token :", csrfToken ? csrfToken.length : 0);

                    const payload = {
                        email: document.getElementById('email').value,
                        first_name: document.getElementById('first_name').value,
                        last_name: document.getElementById('last_name').value,
                        cellphone: document.getElementById('cellphone').value,
                        lang_com: document.getElementById('lang_com').value,
                        is_active: false
                    };

                    if (!csrfToken) {
                        Swal.showValidationMessage(gettext('Erreur de sécurité : Jeton CSRF manquant.'));
                        return;
                    }

                    if (!payload.email || !payload.first_name || !payload.last_name) {
                        Swal.showValidationMessage(gettext('Veuillez remplir les champs obligatoires'));
                        return;
                    }

                    return fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify(payload)
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(err => { 
                                throw new Error(err.erreur || "Erreur serveur"); 
                            });
                        }
                        return response.json();
                    })
                    .catch(error => {
                        Swal.showValidationMessage(`${error.message}`);
                    });
                }
            }).then((result) => {
                if (result.isConfirmed && result.value) {
                    const newUserId = result.value.id;
                    const pathParts = window.location.pathname.split('/');
                    const lang = pathParts[1];

                   
                    // On rafraîchit toutes les listes pour inclure le nouveau "Pending"
                    // avant de forcer la sélection dans le champ cible.
                    refreshUserSelectFields(lang).then(() => {
                        const selectElement = document.getElementById(targetField);
                        print("Champ cible :", targetField);
                        if (selectElement) {
                            // On s'assure que le champ cible sélectionne bien le nouvel arrivant
                            selectElement.value = newUserId;
                        }
                    });
                    // =================

                    // Stocker dans le champ caché Crispy pour le lien final
                    const hiddenAdmin = document.getElementById('id_pending_adm_id');
                    const hiddenAdminAlt = document.getElementById('id_pending_adm_alt_id');
                    const hiddenManager = document.getElementById('id_pending_manager_id');
                    const hiddenReferent = document.getElementById('id_pending_referent_id');
                    const hiddenMatcher = document.getElementById('id_pending_matcher_id');
                    const hiddenMatcherAlt = document.getElementById('id_pending_matcher_alt_id');
                    const hiddenFinance = document.getElementById('id_pending_finance_id');
                    
                    if (hiddenAdmin) hiddenAdmin.value = newUserId;
                    if (hiddenAdminAlt) hiddenAdminAlt.value = newUserId;
                    if (hiddenManager) hiddenManager.value = newUserId;
                    if (hiddenReferent) hiddenReferent.value = newUserId;
                    if (hiddenMatcher) hiddenMatcher.value = newUserId;
                    if (hiddenMatcherAlt) hiddenMatcherAlt.value = newUserId;
                    if (hiddenFinance) hiddenFinance.value = newUserId;

                    Swal.fire(gettext('Succès'), gettext('Utilisateur créé temporairement.'), 'success');
                }
            });
        });
    });
});