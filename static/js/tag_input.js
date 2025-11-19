document.addEventListener("DOMContentLoaded", function () {
    // SÉLECTION INITIALE (Elle peut rester simple)
    const tagFields = document.querySelectorAll(".comma-input-field");
    let tagEditorCounter = 0;
    
    tagFields.forEach(originalInput => {
        
        // 🛑 VÉRIFICATIONS ANTI-DOUBLONNES ET ANTI-ENVELOPPEMENT 🛑
        
        // 1. Vérifier si l'élément a déjà été marqué (première vérification rapide)
        if (originalInput.hasAttribute("data-tag-processed")) {
            return;
        }
        
        // 2. Vérifier si son parent est déjà le conteneur du widget (empêche l'imbrication)
        // C'est la ligne la plus importante pour résoudre le problème du Wizard
        if (originalInput.parentNode && originalInput.parentNode.classList.contains("tag-input-wrapper")) {
            // Si l'input est déjà dans un wrapper, cela signifie que la première exécution a eu lieu.
            // On peut marquer l'input pour les futures vérifications et sortir.
            originalInput.setAttribute('data-tag-processed', 'true'); 
            return;
        }

        // -----------------------------------------------------------------------
        // Si le code arrive ici, l'input est valide et n'a pas été traité.
        // -----------------------------------------------------------------------
        
        // Marquer l'élément comme traité IMMÉDIATEMENT (avant la création du wrapper)
        originalInput.setAttribute('data-tag-processed', 'true');
        // Vérifie si le champ est désactivé
        const isDisabled = originalInput.hasAttribute("disabled") || originalInput.dataset.disabled === "true";

        const wrapper = document.createElement("div");
        wrapper.className = "tag-input-wrapper form-control d-flex flex-wrap align-items-center";
        if (isDisabled) {
            wrapper.style.backgroundColor = "#e9ecef"; // Fond gris
            wrapper.style.opacity = "1.0"; // Effet grisé
        }
        originalInput.style.display = "none";
        originalInput.parentNode.insertBefore(wrapper, originalInput);
        wrapper.appendChild(originalInput);

        const editor = document.createElement("input");
        editor.type = "text";
        editor.className = "tag-editor flex-grow-1 border-0";
        editor.placeholder = originalInput.placeholder || gettext("Ajouter un item");
        editor.id = `tag-editor-${tagEditorCounter++}`;
        editor.name = "tag-editor";
        wrapper.appendChild(editor);

        // Désactive l'éditeur si le champ est désactivé
        if (isDisabled) {
            editor.disabled = true;
            editor.style.cursor = "not-allowed";
        }

        const minItems = parseInt(originalInput.dataset.minItems || "0");
        const maxItems = parseInt(originalInput.dataset.maxItems || "10");
        let items = originalInput.value ? originalInput.value.split(',').map(i => i.trim()).filter(i => i) : [];
        let selectedIndex = null;

        function checkMinItems() {
            if (items.length < minItems) {
                const alertElement = document.createElement("div");
                alertElement.className = "alert alert-danger mt-2 min-items-alert";
                alertElement.textContent = interpolate(gettext(`Nombre minimum d'items %s non atteint !`), [minItems]);
                const inputHeight = originalInput.offsetHeight;
                alertElement.style.height = `${inputHeight}px`;
                if (!wrapper.querySelector(".min-items-alert")) {
                    wrapper.appendChild(alertElement);
                    alertElement.classList.add("min-items-alert");
                }
            } else {
                const existingAlert = wrapper.querySelector(".min-items-alert");
                if (existingAlert) {
                    existingAlert.remove();
                }
            }
        }

        function updateHidden() {
            originalInput.value = items.join(',');
            checkMinItems();
        }

        function renderTags() {
            wrapper.querySelectorAll(".tag-item").forEach(tag => tag.remove());
            items.forEach((item, index) => {
                const tag = document.createElement("span");
                tag.className = "tag-item badge bg-primary me-2 mb-1 d-flex align-items-center";
                tag.textContent = item;

                if (selectedIndex === index) {
                    tag.classList.add("selected");
                }

                // N'ajoute pas le bouton de suppression si le champ est désactivé
                if (!isDisabled) {
                    const removeBtn = document.createElement("button");
                    removeBtn.type = "button";
                    removeBtn.className = "btn-close btn-close-white ms-2";
                    removeBtn.onclick = (e) => {
                        e.stopPropagation();
                        items.splice(index, 1);
                        selectedIndex = null;
                        updateHidden();
                        renderTags();
                    };
                    tag.appendChild(removeBtn);
                }

                tag.onclick = (e) => {
                    if (!isDisabled) {
                        e.stopPropagation();
                        selectedIndex = index;
                        renderTags();
                    }
                };

                wrapper.insertBefore(tag, editor);
            });

            editor.disabled = items.length >= maxItems || isDisabled;
            editor.placeholder = isDisabled
                ? " "
                : items.length >= maxItems
                    ? interpolate(gettext(`Maximum %s éléments atteint!`), [maxItems])
                    : gettext("Ajouter un item");
        }

        // Désactive les événements si le champ est désactivé
        if (!isDisabled) {
            editor.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const val = editor.value.trim();
                    if (val && !items.includes(val) && items.length < maxItems) {
                        items.push(val);
                        editor.value = "";
                        selectedIndex = null;
                        updateHidden();
                        renderTags();
                    }
                } else if ((e.key === "Backspace" || e.key === "Delete") && editor.value === "") {
                    if (selectedIndex !== null) {
                        items.splice(selectedIndex, 1);
                        selectedIndex = null;
                        updateHidden();
                        renderTags();
                    } else {
                        items.pop();
                        updateHidden();
                        renderTags();
                    }
                } else {
                    selectedIndex = null;
                    renderTags();
                }
            });
        }

        document.addEventListener("click", function (e) {
            if (!wrapper.contains(e.target)) {
                selectedIndex = null;
                renderTags();
            }
        });

        checkMinItems();
        renderTags();
    });
});

