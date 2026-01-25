document.addEventListener('DOMContentLoaded', function() {
    const parentSelect = document.querySelector('#id_code_parent_dest'); // ID généré par Django
    const managerSelect = document.querySelector('#id_manager_dest');
    const referentSelect = document.querySelector('#id_referent_dest');

    parentSelect.addEventListener('change', function() {
        const parentId = this.value;

        if (parentId) {
            // Appel AJAX pour récupérer les données du parent
            fetch(`/get-parent-info/?parent_id=${parentId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.manager_id) {
                        managerSelect.value = data.manager_id;
                        managerSelect.disabled = true; // Désactiver
                    }
                    if (data.referent_id) {
                        referentSelect.value = data.referent_id;
                        referentSelect.disabled = true; // Désactiver
                    }
                });
        } else {
            // Réinitialiser si le parent est effacé
            managerSelect.disabled = false;
            referentSelect.disabled = false;
        }
    });
});