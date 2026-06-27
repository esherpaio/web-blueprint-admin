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

    // Native drag-and-drop reordering for tables that have an "order" column.
    // Dragging only permutes the existing order values among the visible rows,
    // so it is safe across paginated pages; the user persists via normal Save.
    function initSortable() {
        document.querySelectorAll("tbody[data-sortable]").forEach(function (body) {
            const field = body.dataset.sortField || "order";
            let dragRow = null;

            body.querySelectorAll("tr").forEach(function (row) {
                const handle = row.querySelector("[data-drag-handle]");
                if (!handle) return;

                // Only start a drag when the handle is grabbed, so the row's
                // inputs and checkboxes stay usable.
                handle.addEventListener("mousedown", function () {
                    row.draggable = true;
                });
                row.addEventListener("mouseup", function () {
                    row.draggable = false;
                });

                row.addEventListener("dragstart", function (event) {
                    dragRow = row;
                    row.classList.add("table-active");
                    event.dataTransfer.effectAllowed = "move";
                    event.dataTransfer.setData("text/plain", "");
                });
                row.addEventListener("dragend", function () {
                    row.draggable = false;
                    row.classList.remove("table-active");
                    dragRow = null;
                    renumber(body, field);
                });
            });

            body.addEventListener("dragover", function (event) {
                if (!dragRow) return;
                event.preventDefault();
                const target = event.target.closest("tr");
                if (!target || target === dragRow || target.parentNode !== body) {
                    return;
                }
                const rect = target.getBoundingClientRect();
                const after = event.clientY > rect.top + rect.height / 2;
                body.insertBefore(dragRow, after ? target.nextSibling : target);
            });
        });
    }

    // Reassign the existing order values to rows by their new position, leaving
    // the set of numbers unchanged.
    function renumber(body, field) {
        const inputs = [];
        body.querySelectorAll("tr").forEach(function (row) {
            const input = row.querySelector('input[name$="-' + field + '"]');
            if (input) inputs.push(input);
        });
        const values = inputs.map(function (input, index) {
            const parsed = parseInt(input.value, 10);
            return isNaN(parsed) ? index + 1 : parsed;
        });
        values.sort(function (a, b) {
            return a - b;
        });
        inputs.forEach(function (input, index) {
            input.value = values[index];
        });
    }

    window.addEventListener("load", function () {
        initSelectAll();
        initConfirm();
        initShowModal();
        initAttributes();
        initSortable();
    });
})();
