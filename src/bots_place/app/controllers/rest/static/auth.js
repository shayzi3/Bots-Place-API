(function () {
    "use strict";

    const UNAUTHORIZED = 401;

    function setMessage(form, text) {
        const box = form.querySelector("[data-message]");
        if (!box) return;
        box.textContent = text || "";
        box.hidden = !text;
    }

    function cooldownKey(form) {
        return "cooldown:" + form.getAttribute("action");
    }

    function saveCooldown(form, seconds) {
        try {
            localStorage.setItem(cooldownKey(form), String(Date.now() + seconds * 1000));
        } catch (error) {
            return;
        }
    }

    function savedCooldown(form) {
        try {
            const expiresAt = localStorage.getItem(cooldownKey(form));
            if (expiresAt === null) return null;
            return Math.max(0, Math.ceil((Number(expiresAt) - Date.now()) / 1000));
        } catch (error) {
            return null;
        }
    }

    function clearCooldown(form) {
        try {
            localStorage.removeItem(cooldownKey(form));
        } catch (error) {
            return;
        }
    }

    function countdown(form, button, seconds) {
        const label = button.dataset.label || button.textContent.trim();
        let left = seconds;
        button.disabled = true;
        button.textContent = `${label} (${left} с)`;

        const timer = setInterval(function () {
            left -= 1;
            if (left <= 0) {
                clearInterval(timer);
                clearCooldown(form);
                button.disabled = false;
                button.textContent = label;
                return;
            }
            button.textContent = `${label} (${left} с)`;
        }, 1000);
    }

    function startCooldown(form, button, payload) {
        if (button && payload.data && payload.data.retry_after) {
            saveCooldown(form, payload.data.retry_after);
            countdown(form, button, payload.data.retry_after);
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
            startCooldown(form, button, payload);
            return;
        }

        if (form.dataset.successUrl) {
            window.location.assign(form.dataset.successUrl);
            return;
        }

        setMessage(form, form.dataset.successMessage || "");
        startCooldown(form, button, payload);
    }

    function init() {
        document.querySelectorAll("form[data-api]").forEach(function (form) {
            form.addEventListener("submit", function (event) {
                submit(form, event);
            });
        });

        const resend = document.getElementById("resend-btn");
        if (resend) {
            const saved = savedCooldown(resend.form);
            const left = saved === null ? parseInt(resend.dataset.seconds || "0", 10) : saved;
            if (left > 0) {
                countdown(resend.form, resend, left);
            } else {
                clearCooldown(resend.form);
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
