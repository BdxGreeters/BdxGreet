document.addEventListener('DOMContentLoaded', function() {
    console.log("Langs com greeter script loaded");

    // 1. Sélection des éléments
    const clusterInput = document.querySelector('#id_cluster'); 
    const destInput = document.querySelector('#id_destination');
    const form = document.querySelector('#GreeterForm') || document.querySelector('form');

    if (!clusterInput || !destInput) {
        console.error("Erreur: Les champs cluster ou destination sont introuvables.");
        return;
    }

    // Extraction de la langue depuis l'URL (ex: /fr/...)
    const pathParts = window.location.pathname.split('/');
    const lang = pathParts[1] || 'fr'; 

    /**
     * Met à jour les cases à cocher dynamiquement
     */
    function updateCheckboxes(fieldName, items, labelKey = 'name') {
        const container = document.querySelector(`#div_id_${fieldName}`);
        if (!container) return;

        // Cible le conteneur interne de Crispy
        const wrapper = container.querySelector('.controls') || container.querySelector('div:not(.form-check)') || container;
        
        // Supprime les anciennes options sans toucher au label principal
        const oldOptions = container.querySelectorAll('.form-check');
        oldOptions.forEach(opt => opt.remove());

        if (!items || items.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'form-check text-muted small ps-3 italic';
            emptyMsg.innerText = "Aucune option disponible pour ce secteur";
            wrapper.appendChild(emptyMsg);
            return;
        }

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'form-check form-check-inline'; 

            const inputId = `id_${fieldName}_${item.id}`;
            const labelText = item[labelKey] || item.name;
            
            div.innerHTML = `
                <input type="checkbox" name="${fieldName}" value="${item.id}" class="form-check-input" id="${inputId}">
                <label class="form-check-label" for="${inputId}">
                    ${labelText}
                </label>
            `;
            wrapper.appendChild(div);
        });
    }

    /**
     * Met à jour un menu déroulant (Select)
     */
    function updateSelect(selector, items, defaultId = null) {
        const select = document.querySelector(selector);
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '';
        
        // Option vide par défaut si nécessaire
        if (!defaultId) {
            select.add(new Option("---------", ""));
        }

        items.forEach(item => {
            const opt = new Option(item.name, item.id);
            // On garde la sélection si elle existe déjà, sinon on prend le defaultId
            if (item.id == (defaultId || currentValue)) opt.selected = true;
            select.add(opt);
        });
    }

    /**
     * Appel API et mise à jour globale
     */
    function updateFields() {
        const clusterVal = clusterInput.value;
        const destVal = destInput.value;

        if (!clusterVal && !destVal) return;

        console.log(`Fetch data for Cluster: ${clusterVal}, Dest: ${destVal}`);

        fetch(`/${lang}/api/get-cluster-data/?code_cluster=${clusterVal}&code_dest=${destVal}`)
            .then(response => {
                if (!response.ok) throw new Error('Erreur réseau');
                return response.json();
            })
            .then(data => {
                // 1. Éléments liés au Cluster
                if (data.interests) updateCheckboxes('interest_greeter', data.interests);
                if (data.experiences) updateCheckboxes('experiences_greeters', data.experiences);

                // 2. Destinations (si on a changé de cluster)
                if (data.destinations) {
                    updateSelect('#id_destination', data.destinations, data.default_dest_id);
                }           

                // 3. Éléments liés à la Destination
                if (data.places) {
                    updateCheckboxes('list_places_greeter', data.places, 'list_places_dest');
                }

                // 4. Langues et Pays
                if (data.langs) {
                    updateSelect('#id_lang_com', data.langs, data.default_lang);
                }

                if (data.pays_id) {   
                    const countryField = document.querySelector('#id_country_greeter');
                    if (countryField) {
                        countryField.value = data.pays_id;
                        countryField.disabled = true; // On le bloque car il est déduit de la destination
                    }
                }
            })
            .catch(error => console.error("Erreur API:", error));
    }

    // --- Écouteurs d'événements ---

    clusterInput.addEventListener('change', updateFields);
    destInput.addEventListener('change', updateFields);

    // Initialisation immédiate si les champs sont déjà remplis (cas de la modification)
    if (clusterInput.value || destInput.value) {
        updateFields();
    }

    // --- Gestion des contraintes de dates ---

    const dateConstraints = [
        { start: '#id_begin_indisponibility', end: '#id_end_indisponibility' },
        { start: '#id_arrival_greeter', end: '#id_departure_greeter' }
    ];

    dateConstraints.forEach(pair => {
        const startEl = document.querySelector(pair.start);
        const endEl = document.querySelector(pair.end);

        if (startEl && endEl) {
            startEl.addEventListener('change', function() {
                if (this.value) {
                    endEl.min = this.value;
                    if (endEl.value && endEl.value < this.value) {
                        endEl.value = this.value;
                    }
                }
            });
        }
    });

    // --- Sécurité avant soumission ---

    if (form) {
        form.addEventListener('submit', function() {
            // On réactive TOUS les champs disabled pour que Django reçoive les données
            const disabledFields = form.querySelectorAll('[disabled]');
            disabledFields.forEach(field => {
                field.disabled = false;
            });
        });
    }
});