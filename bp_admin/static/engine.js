(function () {
    "use strict";

    function setButtonLoading(button, loading) {
        if (!button) return;
        button.disabled = loading;
        button.classList.toggle("disabled", loading);
    }

    function showFlash(message, level) {
        level = level || "danger";
        const container = document.querySelector("[data-flash]");
        if (!container) {
            window.alert(message);
            return;
        }
        const alert = document.createElement("div");
        alert.className = "alert alert-" + level + " alert-dismissible fade show";
        alert.setAttribute("role", "alert");
        alert.textContent = message;
        const close = document.createElement("button");
        close.type = "button";
        close.className = "btn-close";
        close.setAttribute("data-bs-dismiss", "alert");
        alert.appendChild(close);
        container.appendChild(alert);
    }

    window.adminFlash = showFlash;

    function initSelection() {
        const forms = new Set();
        document
            .querySelectorAll("[data-select-row], [data-requires-selection]")
            .forEach(function (element) {
                if (element.form) forms.add(element.form);
            });
        forms.forEach(function (form) {
            const elements = Array.from(form.elements);
            const checkboxes = elements.filter(function (element) {
                return element.hasAttribute("data-select-row");
            });
            const buttons = elements.filter(function (element) {
                return element.hasAttribute("data-requires-selection");
            });
            const master = elements.find(function (element) {
                return element.hasAttribute("data-select-all");
            });

            function updateSelection() {
                const selectedCount = checkboxes.filter(function (checkbox) {
                    return checkbox.checked;
                }).length;
                if (master) {
                    master.checked = selectedCount > 0 && selectedCount === checkboxes.length;
                    master.indeterminate = selectedCount > 0 && selectedCount < checkboxes.length;
                }
                buttons.forEach(function (button) {
                    button.disabled = selectedCount === 0;
                });
            }

            if (master) {
                master.addEventListener("change", function () {
                    checkboxes.forEach(function (checkbox) {
                        checkbox.checked = master.checked;
                    });
                    updateSelection();
                });
            }
            checkboxes.forEach(function (checkbox) {
                checkbox.addEventListener("change", updateSelection);
            });
            window.addEventListener("pageshow", updateSelection);
            updateSelection();
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

    function getApiData(form) {
        const data = {};
        form.querySelectorAll("[name]").forEach(function (input) {
            if (input.disabled) return;
            let value = input.value;
            if (input.type === "checkbox") value = input.checked;
            else if (value === "") value = null;
            data[input.name] = value;
        });
        return Object.keys(data).length ? data : null;
    }

    function initApiActions() {
        document.querySelectorAll("form[data-api-url]").forEach(function (form) {
            form.addEventListener("submit", async function (event) {
                event.preventDefault();
                const method = form.dataset.apiMethod;
                const url = form.dataset.apiUrl;
                const redirect = form.dataset.apiRedirect;
                const button = form.querySelector('[type="submit"]');
                const data = getApiData(form);
                const contentType = data ? "application/json" : null;
                setButtonLoading(button, true);
                try {
                    await callApi(method, url, data, contentType);
                    if (redirect) window.location.href = redirect;
                    else window.location.reload();
                } catch (error) {
                    setButtonLoading(button, false);
                    showFlash(error.message);
                }
            });
        });
    }

    function initBack() {
        document.querySelectorAll("[data-back]").forEach(function (element) {
            element.addEventListener("click", function (event) {
                event.preventDefault();
                const path = window.location.pathname.replace(/\/+$/, "");
                const parent = path.slice(0, path.lastIndexOf("/")) || "/";
                window.location.assign(parent);
            });
        });
    }

    function initShowModal() {
        document.querySelectorAll("[data-show-modal]").forEach(function (element) {
            new bootstrap.Modal(element).show();
        });
    }

    function initSearchFocus() {
        const search = document.getElementById("search");
        if (!search) return;
        search.addEventListener("shown.bs.collapse", function () {
            const input = search.querySelector('input[name="s"]');
            if (input) input.focus();
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

            Array.from(body.children).forEach(function (item) {
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

    function renumber(body, field) {
        let position = 0;
        Array.from(body.children).forEach(function (item) {
            const input = item.querySelector('input[name$="-' + field + '"]');
            if (!input) return;
            position += 1;
            input.value = position;
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
        const query = new URLSearchParams(
            Array.from(url.searchParams).filter(function ([name, value]) {
                return name !== "saved" && value !== "";
            }),
        ).toString();
        if (query !== url.searchParams.toString()) {
            window.history.replaceState(
                {},
                "",
                url.pathname + (query ? "?" + query : "") + url.hash,
            );
        }
    }

    function initCheckGroups() {
        document.querySelectorAll("[data-check-group]").forEach(function (group) {
            const master = group.querySelector("[data-check-group-all]");
            const count = group.querySelector("[data-check-group-count]");
            const checkboxes = Array.from(group.querySelectorAll("[data-check-group-option]"));

            function update() {
                const checkedCount = checkboxes.filter(function (checkbox) {
                    return checkbox.checked;
                }).length;
                master.checked = checkedCount > 0 && checkedCount === checkboxes.length;
                master.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
                count.textContent = checkedCount + " / " + checkboxes.length;
            }

            master.addEventListener("change", function () {
                checkboxes.forEach(function (checkbox) {
                    checkbox.checked = master.checked;
                });
                update();
            });
            checkboxes.forEach(function (checkbox) {
                checkbox.addEventListener("change", update);
            });
            window.addEventListener("pageshow", update);
            update();
        });
    }

    window.addEventListener("load", function () {
        initSelection();
        initCheckGroups();
        initConfirm();
        initShowModal();
        initSearchFocus();
        initAttributes();
        initSortable();
        initAlertDismiss();
        initCleanUrl();
        initBack();
        initApiActions();
    });
})();
