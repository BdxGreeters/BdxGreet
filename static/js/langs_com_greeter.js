
document.addEventListener('DOMContentLoaded', function() {
    console.log("Langs com greeter script loaded");

    // Sélection des éléments déclencheurs (IDs corrigés d'après votre forms.py)
    const clusterInput = document.querySelector('#id_cluster'); 
    const destInput = document.querySelector('#id_destination');
    console.log("Cluster input:", clusterInput);
    console.log("Destination input:", destInput);
    if (!clusterInput || !destInput) {
        console.error("Erreur: Les champs cluster ou destination sont introuvables.");
        return;
    }
    const path = window.location.pathname; // Retourne "/fr/accueil"
    const parts = path.split('/'); // ["", "fr", "accueil"]

    // Le code langue est généralement le premier élément après le premier slash
    const lang = parts[1]; 

    console.log(lang); // "fr"
    /**
     * Met à jour un groupe de cases à cocher (CheckboxSelectMultiple)
     * @param {string} fieldName - Le nom du champ Django (ex: 'interest_greeter')
     * @param {Array} items - Les données reçues du serveur
     * @param {string} labelKey - La clé JSON contenant le texte à afficher
     */
    function updateCheckboxes(fieldName, items, labelKey = 'name') {
        const container = document.querySelector(`#div_id_${fieldName}`);
        if (!container) return;

        // On cible le wrapper interne de Crispy (souvent une div ou un span)
        let wrapper = container.querySelector('.controls') || container.querySelector('div:not(.form-check)');
        // Si on ne trouve pas de wrapper spécifique, on crée une protection pour le label
        const mainLabel = container.querySelector('label.form-label, label.control-label');
    
        // 2. On vide uniquement les anciennes options, pas le label
        // On supprime tous les éléments avec la classe .form-check
        const oldOptions = container.querySelectorAll('.form-check');
        oldOptions.forEach(opt => opt.remove());

        if (items.length === 0) {
            const emptyMsg = document.createElement('p');
            emptyMsg.className = 'text-muted small form-check ps-3';
            emptyMsg.innerText = "Aucune option disponible";
            container.appendChild(emptyMsg);
            return;
        }

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'form-check form-check-inline'; // Classe Bootstrap

            const inputId = `id_${fieldName}_${item.id}`;
            const labelText = item[labelKey] || item.name;
            console.log(`Ajout checkbox: ${labelText} (ID: ${item.id})`);
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
     * Met à jour un menu déroulant classique (Select)
     */
    function updateSelect(selector, items, defaultId = null) {
        const select = document.querySelector(selector);
        if (!select) return;
        
        select.innerHTML = '';
        items.forEach(item => {
            const opt = new Option(item.name, item.id);
            if (item.id == defaultId) opt.selected = true;
            select.add(opt);
        });
    }

    /**
     * Fonction principale de récupération des données
     */
    function updateFields() {
        const clusterVal = clusterInput.value;
        const destVal = destInput.value;

        if (!clusterVal && !destVal) return;

        console.log(`Fetch: Cluster=${clusterVal}, Dest=${destVal}`);

        // Note: Le / initial est crucial pour éviter les erreurs 404
        fetch(`/${lang}/api/get-cluster-data/?code_cluster=${clusterVal}&code_dest=${destVal}`)
            .then(response => {
                if (!response.ok) throw new Error('Erreur serveur (500)');
                return response.json();
            })
            .then(data => {
                console.log("Données JSON reçues:", data);

                // 1. Mise à jour des Checkboxes du Cluster
                if (data.interests) {
                    updateCheckboxes('interest_greeter', data.interests, 'name');
                }
                if (data.experiences) {
                    updateCheckboxes('experiences_greeters', data.experiences, 'name');
                }

                // 2. Mise à jour des Checkboxes de la Destination
                if (data.places) {
                    // Utilise 'list_places_dest' car c'est le nom du champ dans votre modèle
                    updateCheckboxes('list_places_greeter', data.places, 'list_places_dest');
                }

                // 3. Mise à jour du Select des Langues
                if (data.langs) {
                    updateSelect('#id_lang_com', data.langs, data.default_lang);
                }
            })
            .catch(error => {
                console.error("Erreur lors de la mise à jour des champs:", error);
            });
    }

    // Écouteurs d'événements
    clusterInput.addEventListener('change', updateFields);
    destInput.addEventListener('change', updateFields);
});