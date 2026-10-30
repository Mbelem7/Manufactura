"use strict";


document.addEventListener("DOMContentLoaded", async () => {
    const name = document.getElementById("currentUserName");
    const role = document.getElementById("currentUserRole");
    const email = document.getElementById("accountEmail");
    const adminNav = document.getElementById("adminNavigation");
    const logout = document.getElementById("logoutButton");
    const logoutError = document.getElementById("logoutError");

    try {
        const response = await fetch("/auth/me", {
            credentials: "same-origin",
            headers: {"Accept": "application/json"},
            cache: "no-store"
        });
        if (response.status === 401 || response.status === 403) {
            window.location.replace("/auth/login");
            return;
        }
        if (response.ok) {
            const user = await response.json();
            if (name) {
                name.textContent = `${user.nombre || "Usuario"} ${user.apellido || ""}`.trim();
                name.style.visibility = "visible";
            }
            if (email) email.textContent = user.correo || "Cuenta activa";
            if (role) role.textContent = user.rol === "administrador" ? "Administrador" : "Operador";
            if (adminNav && user.rol === "administrador") adminNav.classList.remove("d-none");
        }
    } catch (_) {
        
        if (role) role.textContent = "No se pudo verificar la sesión";
    }

    if (!logout) return;
    logout.addEventListener("click", async () => {
        logout.disabled = true;
        if (logoutError) logoutError.classList.add("d-none");
        try {
            const response = await fetch("/auth/logout", {
                method: "POST",
                credentials: "same-origin",
                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                body: "{}"
            });
            if (!response.ok) throw new Error("No se pudo cerrar la sesión.");
            window.location.replace("/auth/login");
        } catch (_) {
            if (logoutError) {
                logoutError.textContent = "No se pudo cerrar sesión. Intentá de nuevo.";
                logoutError.classList.remove("d-none");
            }
            logout.disabled = false;
        }
    });
});
