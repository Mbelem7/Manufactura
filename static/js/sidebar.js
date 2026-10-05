document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("appSidebar");
    const toggleButton = document.getElementById("sidebarToggle");

    if (!sidebar || !toggleButton) {
        return;
    }

    toggleButton.addEventListener("click", () => {
        sidebar.classList.toggle("show");
    });
});