(function () {
    "use strict";

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

    function initConfirm() {
        document.querySelectorAll("[data-confirm]").forEach(function (button) {
            button.addEventListener("click", function (event) {
                if (!window.confirm(button.dataset.confirm)) {
                    event.preventDefault();
                }
            });
        });
    }

    function initShowModal() {
        document.querySelectorAll("[data-show-modal]").forEach(function (element) {
            new bootstrap.Modal(element).show();
        });
    }

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

    function initSortable() {
        document.querySelectorAll("tbody[data-sortable]").forEach(function (body) {
            const field = body.dataset.sortField || "order";
            let dragRow = null;

            body.querySelectorAll("tr").forEach(function (row) {
                const handle = row.querySelector("[data-drag-handle]");
                if (!handle) return;

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

    // Redistribute the existing order values over the new row positions.
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

    function initAlertDismiss() {
        document
            .querySelectorAll("[data-alert-wrapper]")
            .forEach(function (wrapper) {
                wrapper.querySelectorAll(".alert").forEach(function (alert) {
                    alert.addEventListener("closed.bs.alert", function () {
                        wrapper.remove();
                    });
                });
            });
    }

    function initCleanUrl() {
        const url = new URL(window.location.href);
        if (url.searchParams.has("saved")) {
            url.searchParams.delete("saved");
            const query = url.searchParams.toString();
            window.history.replaceState(
                {},
                "",
                url.pathname + (query ? "?" + query : "") + url.hash,
            );
        }
    }

    window.addEventListener("load", function () {
        initSelectAll();
        initConfirm();
        initShowModal();
        initAttributes();
        initSortable();
        initAlertDismiss();
        initCleanUrl();
    });
})();
