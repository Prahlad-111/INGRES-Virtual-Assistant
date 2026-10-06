
document.addEventListener("DOMContentLoaded", () => {
    const requestForm = document.getElementById("forgot-password-form");
    const resetForm = document.getElementById("reset-password-form");
    const emailInput = document.getElementById("reset-email");
    const message = document.getElementById("reset-message");
    const sendButton = document.getElementById("send-reset-code");
    const resetButton = document.getElementById("reset-password-button");

    function showMessage(text, isError = false) {
        message.textContent = text;
        message.style.color = isError ? "#dc2626" : "#15803d";
    }

    async function postJSON(url, data) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                result.message ||
                result.error ||
                "Request failed. Please try again."
            );
        }

        return result;
    }

    // Step 1: Request a password-reset OTP
    requestForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = emailInput.value.trim().toLowerCase();

        if (!email) {
            showMessage("Please enter your email address.", true);
            return;
        }

        sendButton.disabled = true;
        sendButton.textContent = "Sending...";
        showMessage("");

        try {
            const result = await postJSON(
                "/api/auth/forgot-password",
                { email }
            );

            showMessage(
                result.message ||
                "If a verified account exists for this email, a reset code will be sent."
            );

            resetForm.hidden = false;
            emailInput.readOnly = true;
        } catch (error) {
            showMessage(error.message, true);
        } finally {
            sendButton.disabled = false;
            sendButton.textContent = "Send Reset Code";
        }
    });

    // Step 2: Verify OTP and reset the password
    resetForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = emailInput.value.trim().toLowerCase();
        const otp = document.getElementById("reset-otp").value.trim();
        const password = document.getElementById("new-password").value;
        const confirmPassword =
            document.getElementById("confirm-password").value;

        if (!/^[0-9]{6}$/.test(otp)) {
            showMessage(
                "Enter the 6-digit code sent to your email.",
                true
            );
            return;
        }

        if (password.length < 6 || password.length > 72) {
            showMessage(
                "Password must contain 6 to 72 characters.",
                true
            );
            return;
        }

        if (password !== confirmPassword) {
            showMessage("Passwords do not match.", true);
            return;
        }

        resetButton.disabled = true;
        resetButton.textContent = "Resetting...";
        showMessage("");

        try {
            const result = await postJSON(
                "/api/auth/reset-password",
                {
                    email,
                    otp,
                    new_password: password
                }
            );

            showMessage(
                result.message ||
                "Password reset successful. Redirecting to login..."
            );

            resetForm.reset();

            setTimeout(() => {
                window.location.href = "/login";
            }, 1500);

        } catch (error) {
            showMessage(error.message, true);
        } finally {
            resetButton.disabled = false;
            resetButton.textContent = "Reset Password";
        }
    });
});
