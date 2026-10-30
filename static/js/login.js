"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    if (!form) return;

    const submit = document.getElementById("loginButton");
    const buttonText = document.getElementById("loginButtonText");
    const buttonIcon = document.getElementById("loginButtonIcon");
    const error = document.getElementById("loginError");
    const password = document.getElementById("password");
    const toggle = document.getElementById("togglePassword");
    const toggleIcon = document.getElementById("togglePasswordIcon");

    function showError(message) {
        error.textContent = message;
        error.classList.remove("d-none");
    }

    toggle.addEventListener("click", () => {
        const visible = password.type === "text";
        password.type = visible ? "password" : "text";
        toggle.setAttribute("aria-pressed", String(!visible));
        toggle.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
        toggleIcon.classList.toggle("bi-eye", visible);
        toggleIcon.classList.toggle("bi-eye-slash", !visible);
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        error.classList.add("d-none");
        error.textContent = "";

        const email = document.getElementById("email").value.trim();
        const clave = password.value;
        if (!email || !clave) {
            showError("Ingresá el correo y la contraseña.");
            return;
        }
        if (!document.getElementById("email").checkValidity()) {
            showError("Ingresá un correo electrónico válido.");
            return;
        }

        submit.disabled = true;
        buttonText.textContent = "Verificando acceso…";
        buttonIcon.className = "bi bi-arrow-repeat ms-2";

        try {
            const response = await fetch(form.dataset.loginUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                body: JSON.stringify({email, password: clave})
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                showError(data.error || "No fue posible iniciar sesión. Intentá de nuevo.");
                return;
            }
            window.location.assign(form.dataset.dashboardUrl);
        } catch (_) {
            showError("No se pudo conectar al servidor. Verificá tu conexión e intentá otra vez.");
        } finally {
            submit.disabled = false;
            buttonText.textContent = "Entrar al sistema";
            buttonIcon.className = "bi bi-arrow-right ms-2";
        }
    });
});
