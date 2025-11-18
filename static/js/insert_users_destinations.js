document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. Définitions des champs ---
    const clusterField = document.getElementById('id_code_cluster');
    const destField = document.getElementById('id_code_dest');
    
    const fieldsToUpdate = [
        'id_manager_dest',
        'id_referent_dest',
        'id_matcher_dest',
        'id_matcher_alt_dest',
        'id_finance_dest'
    ];

    // --- 2. Fonction de nettoyage ---
    function clearSelects() {
        fieldsToUpdate.forEach(function(fieldId) {
            const select = document.getElementById(fieldId);
            if (select) {
                select.innerHTML = ''; // Vide toutes les options
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Veuillez d\'abord saisir les codes';
                select.appendChild(defaultOption);
            }
        });
    }

    // --- 3. Fonction AJAX (Pure JS) pour la mise à jour ---
    function updateUserSelects() {
        const clusterCode = clusterField.value;
        const codeDest = destField.value;
        
        // Assurez-vous d'avoir l'URL correcte ici.
        // Puisqu'on est en JS pur, vous ne pouvez pas utiliser {% url '...' %}
        // Vous devez la générer côté serveur et la stocker dans une variable JS.
        // Exemple (à adapter dans votre template Django) :
        const url = window.AJAX_FILTER_USERS_URL; 
        
        if (!clusterCode || !codeDest) {
            clearSelects();
            return;
        }

        // Création des paramètres de requête (Pure JS)
        const params = new URLSearchParams({
            cluster_code: clusterCode,
            code_dest: codeDest
        });

        // Utilisation de l'API native fetch() (Pure JS)
        fetch(`${url}?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(users => {
                fieldsToUpdate.forEach(function(fieldId) {
                    const select = document.getElementById(fieldId);
                    if (!select) return;

                    const selectedValue = select.value;
                    select.innerHTML = ''; // Vider

                    // Option vide
                    const initialOption = document.createElement('option');
                    initialOption.value = '';
                    initialOption.textContent = '---------';
                    select.appendChild(initialOption);

                    // Ajouter les nouveaux utilisateurs
                    users.forEach(function(user) {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = user.text;
                        select.appendChild(option);
                    });

                    // Tenter de re-sélectionner l'ancienne valeur
                    select.value = selectedValue;
                });
            })
            .catch(error => {
                console.error("Erreur lors du filtrage AJAX:", error);
                // Optionnel: Afficher un message d'erreur à l'utilisateur
            });
    }

    // --- 4. Attacher les écouteurs d'événements (Pure JS) ---
    if (clusterField) {
        clusterField.addEventListener('change', updateUserSelects);
    }
    if (destField) {
        destField.addEventListener('change', updateUserSelects);
    }
    
    // --- 5. Exécution initiale (Si le formulaire est pré-rempli) ---
    updateUserSelects();
});

// IMPORTANT : Pour que cela fonctionne, dans votre template Django,
// vous devez définir la variable JS URL avant ce script :
/*
<script>
    window.AJAX_FILTER_USERS_URL = "{% url 'ajax_filter_users' %}";
</script>
<script src="votre-script.js"></script>
*/
