// Progressive enhancement for the declarative admin engine. All persistence
// happens through native form submits; this only adds small conveniences.

(function () {
    "use strict";

    // Select-all checkbox toggles every row checkbox within the same table.
    function initSelectAll() {
        document.querySelectorAll("[data-select-all]").forEach(function (master) {
            const table = master.closest("table");
            if (!table) return;
            master.addEventListener("change", function () {
                table
                    .querySelectorAll("[data-select-row]")
                    .forEach(function (checkbox) {
                        checkbox.checked = master.checked;
                    });
            });
        });
    }

    // Confirmation prompts for destructive submit buttons.
    function initConfirm() {
        document.querySelectorAll("[data-confirm]").forEach(function (button) {
            button.addEventListener("click", function (event) {
                if (!window.confirm(button.dataset.confirm)) {
                    event.preventDefault();
                }
            });
        });
    }

    // Re-open a modal that contains validation errors after a reload.
    function initShowModal() {
        document.querySelectorAll("[data-show-modal]").forEach(function (element) {
            new bootstrap.Modal(element).show();
        });
    }

    // Add/remove rows in a JSONB attributes editor.
    function initAttributes() {
        document.querySelectorAll("[data-attributes]").forEach(function (editor) {
            const rows = editor.querySelector("[data-attributes-rows]");
            const template = editor.querySelector("[data-attributes-template]");
            const addButton = editor.querySelector("[data-attributes-add]");

            if (addButton && rows && template) {
                addButton.addEventListener("click", function () {
                    rows.appendChild(template.content.cloneNode(true));
                });
            }
            editor.addEventListener("click", function (event) {
                const remove = event.target.closest("[data-attributes-remove]");
                if (!remove) return;
                const row = remove.closest(".admin-attribute-row");
                if (row) row.remove();
            });
        });
    }

    window.addEventListener("load", function () {
        initSelectAll();
        initConfirm();
        initShowModal();
        initAttributes();
    });
})();
