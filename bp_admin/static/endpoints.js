function deleteSessions(silent = false) {
    const url = `/api/v1/sessions`;
    return callApi("DELETE", url, null, "application/json", silent);
}
