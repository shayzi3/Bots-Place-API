(function () {
    "use strict";

    const UNAUTHORIZED = 401;
    const COOLDOWN_KEY = "cooldown:resend";

    function setMessage(form, text) {
        const box = form.querySelector("[data-message]");
        if (!box) return;
        box.textContent = text || "";
        box.hidden = !text;
    }

    function saveCooldown(seconds) {
        try {
            localStorage.setItem(COOLDOWN_KEY, String(Date.now() + seconds * 1000));
        } catch (error) {
            return;
        }
    }

    function savedCooldown() {
        try {
            const expiresAt = localStorage.getItem(COOLDOWN_KEY);
            if (expiresAt === null) return null;
            return Math.max(0, Math.ceil((Number(expiresAt) - Date.now()) / 1000));
        } catch (error) {
            return null;
        }
    }

    function clearCooldown() {
        try {
            localStorage.removeItem(COOLDOWN_KEY);
        } catch (error) {
            return;
        }
    }

    function rememberCooldown(payload) {
        if (payload.data && payload.data.retry_after) {
            saveCooldown(payload.data.retry_after);
        }
    }

    function countdown(button, seconds) {
        const label = button.dataset.label || button.textContent.trim();
        let left = seconds;
        button.disabled = true;
        button.textContent = `${label} (${left} с)`;

        const timer = setInterval(function () {
            left -= 1;
            if (left <= 0) {
                clearInterval(timer);
                clearCooldown();
                button.disabled = false;
                button.textContent = label;
                return;
            }
            button.textContent = `${label} (${left} с)`;
        }, 1000);
    }

    function startCooldown(button, payload) {
        if (button && payload.data && payload.data.retry_after) {
            countdown(button, payload.data.retry_after);
        }
    }

    async function submit(form, event) {
        event.preventDefault();
        const button = form.querySelector("button[type=submit]");
        setMessage(form, "");

        let response;
        let payload;
        try {
            response = await fetch(form.getAttribute("action"), {
                method: "POST",
                body: new URLSearchParams(new FormData(form)),
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            });
            payload = await response.json();
        } catch (error) {
            setMessage(form, "Нет связи с сервером. Попробуйте позже.");
            return;
        }

        if (response.status === UNAUTHORIZED) {
            window.location.assign("/auth/login");
            return;
        }

        if (!response.ok) {
            setMessage(form, payload.msg);
            rememberCooldown(payload);
            startCooldown(button, payload);
            return;
        }

        rememberCooldown(payload);

        if (form.dataset.successUrl) {
            window.location.assign(form.dataset.successUrl);
            return;
        }

        setMessage(form, form.dataset.successMessage || "");
        startCooldown(button, payload);
    }

    function init() {
        document.querySelectorAll("form[data-api]").forEach(function (form) {
            form.addEventListener("submit", function (event) {
                submit(form, event);
            });
        });

        const resend = document.getElementById("resend-btn");
        if (resend) {
            const left = savedCooldown() ?? 0;
            if (left > 0) {
                countdown(resend, left);
            } else {
                clearCooldown();
                resend.disabled = false;
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
