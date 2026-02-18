console.log('Langs com greeter script loaded'); // Debug
document.addEventListener('DOMContentLoaded', function() {
    const clusterInput = document.querySelector('#id_code_cluster'); // Adaptez l'ID
    const destInput = document.querySelector('#id_destination');      // Adaptez l'ID

    function updateFields() {
        const clusterVal = clusterInput.value;
        const destVal = destInput.value;
        console.log(`Cluster: ${clusterVal}, Destination: ${destVal}`); // Debug
        fetch(`/api/get-cluster-data/?code_cluster=${clusterVal}&code_dest=${destVal}`)
            .then(response => response.json())
            .then(data => {
                if (data.interests) {
                    updateSelectOptions('#id_interest_greeter', data.interests);
                }
                if (data.experiences) {
                    updateSelectOptions('#id_experiences_greeters', data.experiences);
                }
                if (data.langs) {
                    updateSelectOptions('#id_lang_com', data.langs, data.default_lang);
                }
                if (data.places) {
                    updateSelectOptions('#id_list_places_greeter', data.places);
                }
            });
    }

    function updateSelectOptions(selector, items, defaultId = null) {
        const select = document.querySelector(selector);
        if (!select) return;
        
        select.innerHTML = ''; // Vide les options actuelles
        items.forEach(item => {
            const opt = new Option(item.name, item.id);
            if (item.id === defaultId) opt.selected = true;
            select.add(opt);
        });
    }

    clusterInput.addEventListener('change', updateFields);
    destInput.addEventListener('change', updateFields);
});