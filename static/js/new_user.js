document.addEventListener('DOMContentLoaded', function() {
    const newUserButtons = document.querySelectorAll('[data-target-field]');
   
    // Fonction pour récupérer les langues disponibles
    async function fetchLanguages(lang) {
        const response = await fetch(`/${lang}/core/get-languages/`);
        if (!response.ok) {
            throw new Error('Failed to fetch languages');
        }
        return await response.json();
    }
    async function refreshUserSelectFields(lang) {

     // Récupérer les valeurs actuelles de code_cluster et code_dest
        const codeCluster = document.getElementById('id_code_cluster')?.value??'';
        const codeDest = document.getElementById('id_code_dest')?.value??'';
        console.log("codecluster:", codeCluster);
        console.log("codedest:", codeDest);

    // Construire l'URL avec les paramètres de filtrage
        const params = new URLSearchParams();
        if (codeCluster) params.append('code_cluster', codeCluster);
        if (codeDest) params.append('code_dest', codeDest);


    // Fonction pour rafraîchir les listes des utilisateurs

    
        const response = await fetch(`/${lang}/core/get-users/?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        const users = await response.json();

    // Liste des IDs des champs de sélection des utilisateurs
    const userSelectFields = [
        'id_manager_dest',
        'id_referent_dest',
        'id_matcher_dest',
        'id_matcher_alt_dest',
        'id_finance_dest'
    ];

    // Mettre à jour chaque champ de sélection s'il existe
    userSelectFields.forEach(fieldId => {
        const selectElement = document.getElementById(fieldId);
        if (selectElement) {  // Vérifie si le champ existe
            console.log(`Updating select field: ${fieldId}`);
            const currentValue = selectElement.value;
            selectElement.innerHTML = '';

            // Ajouter une option vide
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '---------';
            selectElement.appendChild(emptyOption);

            // Ajouter les nouvelles options
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = `${user.last_name} ${user.first_name}`;
                selectElement.appendChild(option);
            });

            // Restaurer la valeur sélectionnée si elle existe
            if (currentValue) {
                selectElement.value = currentValue;
            }
        }
    });
    }   

    // Événement au clic sur le bouton
    newUserButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const targetField = this.getAttribute('data-target-field');
            const pathParts = window.location.pathname.split('/');
            const lang = pathParts[1];  // Exemple : 'fr' dans '/fr/cluster/...'
            const url = `/${lang}/core/users_create/`;
            

            // Récupérer les langues disponibles
            let languages = [];
            try {
                languages = await fetchLanguages(lang);
            } catch (error) {
                console.error('Error fetching languages:', error);
            }

            // Générer les options de langue dynamiquement
            let langOptions = '';
            languages.forEach(lang => {
                langOptions += `<option value="${lang.code}">${lang.name}</option>`;
            });
            codecluster = document.getElementById('id_code_cluster')?.value ?? '' ;
            codedest = document.getElementById('id_code_dest')?.value?? '' ;
            // Afficher le popup SweetAlert2
            Swal.fire({
                title: gettext('Créer un nouvel utilisateur'),
                html: `
                    <form id="newUserForm" class="swal2-form">
                        <div class="form-group mb-2">
                            <label for="email">${gettext('Email')}</label>
                            <input type="email" id="email" class="form-control swal2-input" required autocomplete ="off">
                        </div>
                        <div class="form-group mb-2">
                            <label for="first_name">${gettext('Prénom')}</label>
                            <input type="text" id="first_name" class="form-control swal2-input" required autocomplete ="off">
                        </div>
                        <div class="form-group mb-2">
                            <label for="last_name">${gettext('Nom')}</label>
                            <input type="text" id="last_name" class="form-control swal2-input" required autocomplete ="off">
                        </div>
                        <div class="form-group mb-2">
                            <label for="cellphone">${gettext('Téléphone')}</label>
                            <input type="text" id="cellphone" class="form-control swal2-input">
                        </div>
                        <div class="form-group mb-2">
                            <label for="lang_com">${gettext('Langue')}</label>
                            <select id="lang_com" class="form-control swal2-input" required >
                                ${langOptions}
                            </select>
                        </div>
                        <div class="form-group mb-2">
                            <input type="text" id="code_cluster" class="form-control swal2-input" value="${codecluster}" hidden>
                        </div>
                        <div class="form-group mb-2">
                            <input type="text" id="code_dest" class="form-control swal2-input" value="${codedest}" hidden>
                        </div>
                    </form>
                `,
                showCancelButton: true,
                confirmButtonText: gettext('Créer'),
                cancelButtonText: gettext('Annuler'),
                focusConfirm: false,
                preConfirm: () => {
                    // Récupérer les valeurs du formulaire
                    const email = document.getElementById('email').value;
                    const first_name = document.getElementById('first_name').value;
                    const last_name = document.getElementById('last_name').value;
                    const cellphone = document.getElementById('cellphone').value;
                    const lang_com = document.getElementById('lang_com').value;
                    const code_cluster = document.getElementById('code_cluster').value;
                    const code_dest = document.getElementById('code_dest').value;
                    // Validation simple


                    if (!email || !first_name || !last_name || !lang_com) {
                        Swal.showValidationMessage(gettext('Veuillez remplir tous les champs requis'));
                        return;
                    }
                    // Envoyer les données au serveur via AJAX
                    return fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json;charset=utf-8',
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        body: JSON.stringify({
                            email: email,
                            first_name: first_name,
                            last_name: last_name,
                            cellphone: cellphone,
                            lang_com: lang_com,
                            code_cluster: code_cluster,
                            code_dest: code_dest   
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(data => {
                                // Extraire le message d'erreur de la réponse JSON
                                const errorMessage = data.erreur;
                                throw new Error(errorMessage);
                            });
                        }
                        return response.json();
                    })
                    .catch(error => {
                        Swal.showValidationMessage(`Erreur: ${error.message.replace(/[\[\],' ]/g, '')}`);
                    });
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    // Mettre à jour le champ adm, adm_alt, manager, refeent, matcher, matcher_alt ou fimance avec le nouvel utilisateur
                    const newUserId = result.value.id;
                    const selectElement = document.getElementById(targetField);
                    const newOption = new Option(result.value.text, newUserId, true, true);
                    selectElement.append(newOption);

                    refreshUserSelectFields(lang);
                    Swal.fire(gettext('Succès'), gettext('Utilisateur créé avec succès!'), 'success');
                }
            });
        });
    });
});
