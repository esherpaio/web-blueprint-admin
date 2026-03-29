async function initButtons() {
    const buttons = document.getElementsByClassName("btn-load");
    for (const button of buttons) {
        button.dataset.loading = "0";
        let spinner = document.createElement("span");
        spinner.classList.add("d-none", "spinner-grow", "spinner-grow-sm", "ms-2");
        spinner.setAttribute("role", "status");
        button.appendChild(spinner);
    }
}

function resetButtons() {
    const buttons = document.getElementsByClassName("btn-load");
    for (const button of buttons) {
        if (button.id) {
            updateButton(button.id, 0, true);
        }
    }
}

function updateButton(buttonId, value, override) {
    let button = document.getElementById(buttonId);
    if (!button.classList.contains("btn-load")) return;
    let spinner = button.getElementsByClassName("spinner-grow")[0];

    const oldCount = parseInt(button.dataset.loading);
    const newCount = override ? value : oldCount + value;
    button.dataset.loading = String(newCount);

    if (newCount > 0) {
        button.classList.add("disabled");
        if (spinner.classList.contains("d-none")) spinner.classList.remove("d-none");
    } else {
        button.classList.remove("disabled");
        if (!spinner.classList.contains("d-none")) spinner.classList.add("d-none");
    }
}

window.addEventListener("load", initButtons);
