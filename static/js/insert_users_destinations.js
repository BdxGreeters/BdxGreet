/**
 * Gestionnaire de filtrage dynamique des utilisateurs par Cluster et Destination.
 * Ce script synchronise plusieurs listes déroulantes suite à des changements
 * de critères ou à des créations d'utilisateurs via modales.
 */
(function() {
    'use strict';

    const CONFIG = {
        triggers: ['id_code_cluster', 'id_code_dest'],
        userFields: ['id_manager_dest', 'id_referent_dest', 'id_matcher_dest', 'id_matcher_alt_dest', 'id_finance_dest']
    };

    async function refreshUserSelectFields() {
        const codeCluster = document.getElementById('id_code_cluster')?.value || '';
        const codeDest = document.getElementById('id_code_dest')?.value || '';

        if (!codeCluster) {
            updateDomSelects([]);
            return;
        }

        // URLSearchParams gère proprement l'encodage des paramètres
        const params = new URLSearchParams({ 
            code_cluster: codeCluster, 
            code_dest: codeDest 
        });

        try {
            const response = await fetch(`${window.AJAX_FILTER_USERS_URL}?${params.toString()}`);
            if (!response.ok) throw new Error('Erreur API');
            const users = await response.json();
            updateDomSelects(users);
        } catch (err) {
            console.error("Erreur refresh users:", err);
        }
    }

    function updateDomSelects(users) {
        CONFIG.userFields.forEach(fieldId => {
            const select = document.getElementById(fieldId);
            if (!select) return;

            const currentVal = select.value;
            select.innerHTML = '<option value="">---------</option>';
            
            users.forEach(u => {
                const opt = new Option(u.text, u.id);
                select.add(opt);
            });

            // On ne restaure la valeur que si elle est toujours présente dans la liste filtrée
            select.value = currentVal; 
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        CONFIG.triggers.forEach(id => {
            document.getElementById(id)?.addEventListener('change', refreshUserSelectFields);
        });
        refreshUserSelectFields();
    });

    window.refreshUserSelectFields = refreshUserSelectFields;
})();