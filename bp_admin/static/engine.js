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

    function initBack() {
        document.querySelectorAll("[data-back]").forEach(function (element) {
            element.addEventListener("click", function (event) {
                if (document.referrer.startsWith(window.location.origin)) {
                    event.preventDefault();
                    window.history.back();
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
        document.querySelectorAll("[data-sortable]").forEach(function (body) {
            const field = body.dataset.sortField || "order";
            let dragItem = null;

            Array.prototype.forEach.call(body.children, function (item) {
                const handle = item.querySelector("[data-drag-handle]");
                if (!handle) return;

                handle.addEventListener("mousedown", function () {
                    item.draggable = true;
                });
                item.addEventListener("mouseup", function () {
                    item.draggable = false;
                });

                item.addEventListener("dragstart", function (event) {
                    dragItem = item;
                    item.classList.add("opacity-50");
                    event.dataTransfer.effectAllowed = "move";
                    event.dataTransfer.setData("text/plain", "");
                });
                item.addEventListener("dragend", function () {
                    item.draggable = false;
                    item.classList.remove("opacity-50");
                    dragItem = null;
                    renumber(body, field);
                });
            });

            body.addEventListener("dragover", function (event) {
                if (!dragItem) return;
                event.preventDefault();
                let target = event.target;
                while (target && target.parentNode !== body) {
                    target = target.parentNode;
                }
                if (!target || target === dragItem) return;
                const rect = target.getBoundingClientRect();
                const after = event.clientY > rect.top + rect.height / 2;
                body.insertBefore(dragItem, after ? target.nextSibling : target);
            });
        });
    }

    // Redistribute the existing order values over the new item positions.
    function renumber(body, field) {
        const inputs = [];
        Array.prototype.forEach.call(body.children, function (item) {
            const input = item.querySelector('input[name$="-' + field + '"]');
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

    function initHtmlEditors() {
        const toolbar = [
            [{ header: [2, 3, 4, false] }],
            ["bold", "italic", "underline", "strike"],
            ["link"],
            [{ list: "ordered" }, { list: "bullet" }],
            ["clean"],
        ];
        document.querySelectorAll("[data-html-editor]").forEach(function (el) {
            const input = document.getElementsByName(el.dataset.target)[0];
            const readonly = el.hasAttribute("data-readonly");
            const quill = new Quill(el, {
                theme: "snow",
                readOnly: readonly,
                modules: { toolbar: readonly ? false : toolbar },
            });
            if (!input) return;
            input.value = quill.root.innerHTML;
            quill.on("text-change", function () {
                input.value = quill.root.innerHTML;
            });
        });
    }

    window.addEventListener("load", function () {
        initSelectAll();
        initConfirm();
        initShowModal();
        initAttributes();
        initSortable();
        initAlertDismiss();
        initCleanUrl();
        initHtmlEditors();
        initBack();
    });
})();
