async function logoutUser() {
    await deleteSessions();
    window.location.href = "/";
}
