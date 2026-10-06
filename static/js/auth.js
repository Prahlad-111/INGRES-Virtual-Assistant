
console.log("INGRES Auth JS loaded.");

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM loaded.");

    setupLogin();
    setupRegister();
});


// =====================================================
// SHARED HELPERS
// =====================================================

function showMessage(element, text, color = "red") {
    if (!element) return;

    element.textContent = text;
    element.style.color = color;
}

async function postJSON(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    let data;

    try {
        data = await response.json();
    } catch {
        data = {
            success: false,
            message: "The server returned an invalid response."
        };
    }

    return { response, data };
}


// =====================================================
// LOGIN
// =====================================================

function setupLogin() {
    const form = document.getElementById("login-form");

    if (!form) return;

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const button = document.getElementById("login-button");
        const message = document.getElementById("login-message");

        if (!email || !password) {
            showMessage(message, "Please enter your email and password.");
            return;
        }

        button.disabled = true;
        button.textContent = "Logging in...";
        showMessage(message, "");

        try {
            const { response, data } = await postJSON(
                "/api/auth/login",
                { email, password }
            );

            if (response.ok && data.success && data.token) {
                localStorage.setItem("ingres_token", data.token);

                if (data.user) {
                    localStorage.setItem(
                        "ingres_user",
                        JSON.stringify(data.user)
                    );
                }

                showMessage(message, "Login successful!", "green");
                window.location.href = "/";
            } else {
                showMessage(
                    message,
                    data.message || "Login failed. Please check your details."
                );
            }
        } catch (error) {
            console.error("LOGIN ERROR:", error);

            showMessage(
                message,
                "Unable to connect to the server. Please try again."
            );
        } finally {
            button.disabled = false;
            button.textContent = "Login";
        }
    });
}


// =====================================================
// REGISTRATION AND EMAIL OTP
// =====================================================

function setupRegister() {
    const form = document.getElementById("register-form");

    if (!form) return;

    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput =
        document.getElementById("confirm-password");

    const registrationFields =
        document.getElementById("registration-fields");
    const otpSection = document.getElementById("otp-section");

    const title = document.getElementById("form-title");
    const subtitle = document.getElementById("form-subtitle");

    const registerButton = document.getElementById("register-button");
    const verifyButton = document.getElementById("verify-otp-button");
    const resendButton = document.getElementById("resend-otp-button");
    const backButton =
        document.getElementById("back-to-register-button");

    const otpInput = document.getElementById("otp");
    const verificationEmail =
        document.getElementById("verification-email");
    const message = document.getElementById("register-message");

    let pendingEmail = "";
    let verificationStage = false;
    let resendAvailable = true;

    function setRegistrationStage() {
        verificationStage = false;

        registrationFields.hidden = false;
        otpSection.hidden = true;

        // Disable hidden controls so browser validation works correctly.
        registrationFields.querySelectorAll("input").forEach(function (input) {
            input.disabled = false;
        });

        otpInput.disabled = true;
        otpInput.required = false;

        registerButton.hidden = false;
        registerButton.disabled = false;
        registerButton.textContent = "Create Account";

        title.textContent = "Create Account";
        subtitle.textContent = "Create your account to get started";
    }

    function setVerificationStage(email) {
        verificationStage = true;
        pendingEmail = email;

        registrationFields.hidden = true;
        otpSection.hidden = false;

        registrationFields.querySelectorAll("input").forEach(function (input) {
            input.disabled = true;
        });

        otpInput.disabled = false;
        otpInput.required = true;
        otpInput.value = "";

        verificationEmail.textContent = email;

        registerButton.hidden = true;
        title.textContent = "Verify Your Email";
        subtitle.textContent = "Enter the verification code sent to your inbox";

        otpInput.focus();
    }

    // ---------------------------------------------
    // CREATE ACCOUNT: SEND OTP
    // ---------------------------------------------

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (verificationStage) return;

        const name = nameInput.value.trim();
        const email = emailInput.value.trim().toLowerCase();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (!name || !email || !password || !confirmPassword) {
            showMessage(message, "Please complete all fields.");
            return;
        }

        if (password !== confirmPassword) {
            showMessage(message, "Passwords do not match.");
            return;
        }

        if (password.length < 6) {
            showMessage(
                message,
                "Password must be at least 6 characters long."
            );
            return;
        }

        registerButton.disabled = true;
        registerButton.textContent = "Sending verification code...";
        showMessage(message, "");

        try {
            const { response, data } = await postJSON(
                "/api/auth/register",
                { name, email, password }
            );

            if (response.ok && data.success) {
                setVerificationStage(email);

                showMessage(
                    message,
                    data.message ||
                        "Verification code sent. Please check your email.",
                    "green"
                );
            } else {
                showMessage(
                    message,
                    data.message || "Unable to start registration."
                );
            }
        } catch (error) {
            console.error("REGISTER ERROR:", error);

            showMessage(
                message,
                "Unable to connect to the server. Please try again."
            );
        } finally {
            if (!verificationStage) {
                registerButton.disabled = false;
                registerButton.textContent = "Create Account";
            }
        }
    });

    // ---------------------------------------------
    // VERIFY OTP
    // ---------------------------------------------

    verifyButton.addEventListener("click", async function () {
        const otp = otpInput.value.trim();

        if (!pendingEmail) {
            showMessage(
                message,
                "Please start registration again."
            );
            return;
        }

        if (!/^\d{6}$/.test(otp)) {
            showMessage(message, "Enter the six-digit verification code.");
            return;
        }

        verifyButton.disabled = true;
        verifyButton.textContent = "Verifying...";
        showMessage(message, "");

        try {
            const { response, data } = await postJSON(
                "/api/auth/verify-otp",
                {
                    email: pendingEmail,
                    otp: otp
                }
            );

            if (response.ok && data.success) {
                showMessage(
                    message,
                    data.message ||
                        "Email verified! Redirecting to login...",
                    "green"
                );

                verifyButton.disabled = true;
                resendButton.disabled = true;
                backButton.disabled = true;

                setTimeout(function () {
                    window.location.href = "/login";
                }, 1500);
            } else {
                showMessage(
                    message,
                    data.message || "Invalid or expired verification code."
                );
            }
        } catch (error) {
            console.error("OTP VERIFICATION ERROR:", error);

            showMessage(
                message,
                "Unable to verify your email. Please try again."
            );
        } finally {
            if (!backButton.disabled) {
                verifyButton.disabled = false;
                verifyButton.textContent = "Verify Email";
            }
        }
    });

    // ---------------------------------------------
    // RESEND OTP
    // ---------------------------------------------

    resendButton.addEventListener("click", async function () {
        if (!pendingEmail || !resendAvailable) return;

        resendAvailable = false;
        resendButton.disabled = true;
        resendButton.textContent = "Sending...";
        showMessage(message, "");

        try {
            const { response, data } = await postJSON(
                "/api/auth/resend-otp",
                { email: pendingEmail }
            );

            if (response.ok && data.success) {
                otpInput.value = "";

                showMessage(
                    message,
                    data.message || "A new verification code was sent.",
                    "green"
                );
            } else {
                showMessage(
                    message,
                    data.message || "Unable to resend the code."
                );
            }
        } catch (error) {
            console.error("RESEND OTP ERROR:", error);

            showMessage(
                message,
                "Unable to connect to the server."
            );
        } finally {
            // Local cooldown; the server must enforce its own cooldown too.
            let remaining = 60;

            resendButton.textContent = `Resend in ${remaining}s`;

            const timer = setInterval(function () {
                remaining -= 1;

                if (remaining <= 0) {
                    clearInterval(timer);
                    resendAvailable = true;
                    resendButton.disabled = false;
                    resendButton.textContent = "Resend Code";
                } else {
                    resendButton.textContent = `Resend in ${remaining}s`;
                }
            }, 1000);
        }
    });

    // ---------------------------------------------
    // BACK TO REGISTRATION
    // ---------------------------------------------

    backButton.addEventListener("click", function () {
        pendingEmail = "";
        otpInput.value = "";

        setRegistrationStage();
        showMessage(message, "");
    });

    // Initial page state
    setRegistrationStage();
}
