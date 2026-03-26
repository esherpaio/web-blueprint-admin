function hideModals() {
    const elements = document.getElementsByClassName("modal");
    for (const element of elements) {
        const modal = bootstrap.Modal.getInstance(element);
        if (modal) {
            modal.hide();
        }
    }
}

function showModal(id_) {
    hideModals();
    const modal = new bootstrap.Modal(document.getElementById(id_));
    modal.show();
}

function showMessage(message) {
    hideModals();
    let modalBody = document.querySelector("#modal-message .modal-body p");
    modalBody.innerHTML = message;
    let modal = new bootstrap.Modal(document.getElementById("modal-message"));
    modal.show();
}
