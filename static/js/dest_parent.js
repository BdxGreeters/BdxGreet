document.addEventListener('DOMContentLoaded', function() {
    const parentSelect = document.querySelector('#id_code_parent_dest');
    
    // Configuration des champs cibles
    const targetFields = {
        manager: {
            el: document.querySelector('#id_manager_dest'),
            keyId: 'manager_id',
            keyName: 'manager_name'
        },
        referent: {
            el: document.querySelector('#id_referent_dest'),
            keyId: 'referent_id',
            keyName: 'referent_name'
        },
        finance: {
            el: document.querySelector('#id_finance_dest'),
            keyId: 'finance_id',
            keyName: 'finance_name'
        }
    };

    // Fonction pour verrouiller un champ et garantir l'affichage du nom
    function setFieldState(fieldObj, lock, id = '', name = '') {
        const { el } = fieldObj;
        if (!el) return;

        if (lock && id) {
            // Vérifier si l'option existe déjà
            let option = el.querySelector(`option[value="${id}"]`);
            
            if (!option && name) {
                // Création de l'option si absente (évite le champ vide)
                option = new Option(name, id, true, true);
                el.add(option);
            }
            
            el.value = id;
            el.style.pointerEvents = "none";
            el.style.backgroundColor = "#e9ecef"; // Aspect readonly
            el.tabIndex = -1;
            // Marqueur pour éviter que new_user.js n'écrase la valeur
            el.setAttribute('data-locked-by-parent', 'true');
        } else {
            // Déverrouillage
            el.style.pointerEvents = "auto";
            el.style.backgroundColor = "";
            el.tabIndex = 0;
            el.removeAttribute('data-locked-by-parent');
        }
        
        // Notification pour les autres scripts (Select2, etc.)
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    if (parentSelect) {
        parentSelect.addEventListener('change', function() {
            const parentId = this.value;
            const apiUrl = this.dataset.ajaxUrl; // URL générée par Django {% url %}

            if (parentId && apiUrl) {
                const params = new URLSearchParams({ parent_id: parentId });
                
                fetch(`${apiUrl}?${params.toString()}`)
                    .then(response => {
                        if (!response.ok) throw new Error('Erreur destination parente');
                        return response.json();
                    })
                    .then(data => {
                        // Mise à jour de chaque champ avec les données de la vue
                        setFieldState(targetFields.manager, !!data.manager_id, data.manager_id, data.manager_name);
                        setFieldState(targetFields.referent, !!data.referent_id, data.referent_id, data.referent_name);
                        setFieldState(targetFields.finance, !!data.finance_id, data.finance_id, data.finance_name);
                    })
                    .catch(error => console.error('Erreur:', error));
            } else {
                // Si on vide le choix du parent, on déverrouille tout
                Object.values(targetFields).forEach(field => setFieldState(field, false));
            }
        });
    }
});