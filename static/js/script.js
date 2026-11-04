"use strict";

let currentConversationId = null;
let isSending = false;

// Authentication elements
let loginScreen;
let appContainer;
let createTab;
let loginTab;
let createAccountForm;
let loginAccountForm;
let verifyRegistrationForm;
let verifyLoginForm;
let forgotPasswordForm;
let resetPasswordForm;
let authName;
let authEmail;
let authPassword;
let authConfirmPassword;
let loginEmail;
let loginPassword;
let registrationOtp;
let loginOtp;
let resetOtp;
let resetEmail;
let resetNewPassword;
let authMessage;

// Chat elements
let chatBox;
let userInput;
let sendButton;
let typingIndicator;
let recentChatList;

// Account menu elements
let accountName;
let accountDisplayName;
let accountDisplayEmail;
let accountButton;
let accountMenu;

// New chat menu elements
let newChatButton;
let newChatMenu;

// ============================================================
// AUTHENTICATION
// ============================================================

function getAuthToken() {
    return localStorage.getItem("ingres_token");
}

function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem("ingres_user"));
    } catch (error) {
        console.error("Unable to read saved user:", error);
        return null;
    }
}

function saveAuthData(token, user) {
    localStorage.setItem("ingres_token", token);
    localStorage.setItem("ingres_user", JSON.stringify(user));
    localStorage.removeItem("ingres_visitor_token");
    localStorage.removeItem("ingres_login_only");
}

function clearAuthData() {
    localStorage.removeItem("ingres_token");
    localStorage.removeItem("ingres_user");
    localStorage.removeItem("ingresToken");
    localStorage.removeItem("ingresUser");
    localStorage.removeItem("ingres_visitor_token");
    localStorage.removeItem("ingres_login_only");
}

async function authRequest(endpoint, payload) {
    const response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    let data = {};

    try {
        data = await response.json();
    } catch (error) {
        if (response.ok) {
            throw new Error("The server returned an invalid response.");
        }
    }

    if (!response.ok || data.success === false) {
        throw new Error(data.message || "Request failed. Please try again.");
    }

    return data;
}

async function authFetch(url, options = {}) {
    const token = getAuthToken();

    if (!token) {
        throw new Error("Please log in to continue.");
    }

    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${token}`);

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        clearAuthData();
        currentConversationId = null;
        showLoginScreen();
        showLoginTab();
        throw new Error("Your session expired. Please log in again.");
    }

    return response;
}

function showLoginScreen() {
    if (loginScreen) {
        loginScreen.style.display = "flex";
    }

    if (appContainer) {
        appContainer.classList.add("app-hidden");
    }
}

function showApplication() {
    if (loginScreen) {
        loginScreen.style.display = "none";
    }

    if (appContainer) {
        appContainer.classList.remove("app-hidden");
    }

    updateAccountUI();
}

function updateAccountUI() {
    const user = getCurrentUser();
    if (!user) return;

    const displayName = user.name || user.email || "Account";

    if (accountName) accountName.textContent = displayName;
    if (accountDisplayName) accountDisplayName.textContent = displayName;
    if (accountDisplayEmail) accountDisplayEmail.textContent = user.email || "";
}

function showAuthMessage(message, isSuccess = false) {
    if (!authMessage) return;

    authMessage.textContent = message;
    authMessage.style.color = isSuccess ? "#16a34a" : "#dc2626";
}

function hideAllAuthForms() {
    [
        createAccountForm,
        loginAccountForm,
        verifyRegistrationForm,
        verifyLoginForm,
        forgotPasswordForm,
        resetPasswordForm
    ].forEach(form => {
        if (form) form.classList.add("auth-panel-hidden");
    });
}

function showAuthForm(form) {
    hideAllAuthForms();

    if (form) {
        form.classList.remove("auth-panel-hidden");
    }

    if (authMessage) {
        authMessage.textContent = "";
    }
}

function showCreateTab() {
    if (createTab) createTab.classList.add("active");
    if (loginTab) loginTab.classList.remove("active");
    showAuthForm(createAccountForm);
}

function showLoginTab() {
    if (createTab) createTab.classList.remove("active");
    if (loginTab) loginTab.classList.add("active");
    showAuthForm(loginAccountForm);
}

function setButtonLoading(button, loading, loadingText, normalText) {
    if (!button) return;

    button.disabled = loading;
    button.textContent = loading ? loadingText : normalText;
}

// ============================================================
// ACCOUNT REGISTRATION
// ============================================================

async function handleCreateAccount(event) {
    event.preventDefault();

    if (!authName || !authEmail || !authPassword) {
        showAuthMessage("The account form is missing a required field. Refresh and try again.");
        return;
    }

    const name = authName.value.trim();
    const email = authEmail.value.trim().toLowerCase();
    const password = authPassword.value;
    const confirmPassword = authConfirmPassword
        ? authConfirmPassword.value
        : password;

    if (!name || !email || !password) {
        showAuthMessage("Please fill in all fields.");
        return;
    }

    if (authConfirmPassword && password !== confirmPassword) {
        showAuthMessage("Passwords do not match.");
        return;
    }

    if (password.length < 8) {
        showAuthMessage("Password must contain at least 8 characters.");
        return;
    }

    const button = document.getElementById("create-account-button");
    setButtonLoading(button, true, "Sending OTP...", "Create My Account");

    try {
        const data = await authRequest("/api/auth/register", {
            name,
            email,
            password,
            confirm_password: confirmPassword
        });

        const emailLabel = document.getElementById("registration-otp-email");
        if (emailLabel) emailLabel.textContent = email;

        showAuthForm(verifyRegistrationForm);
        showAuthMessage(data.message || "OTP sent to your email.", true);
    } catch (error) {
        console.error("Registration error:", error);
        showAuthMessage(error.message);
    } finally {
        setButtonLoading(button, false, "Sending OTP...", "Create My Account");
    }
}

async function handleVerifyRegistration(event) {
    event.preventDefault();

    const email = authEmail.value.trim().toLowerCase();
    const otp = registrationOtp.value.trim();

    if (!/^\d{6}$/.test(otp)) {
        showAuthMessage("Enter a valid 6-digit OTP.");
        return;
    }

    const button = document.getElementById("verify-registration-button");
    setButtonLoading(button, true, "Verifying...", "Verify Email");

    try {
        const data = await authRequest("/api/auth/verify-registration", {
            email,
            otp
        });

        if (!data.token || !data.user) {
            throw new Error("The server did not return account login data.");
        }

        saveAuthData(data.token, data.user);
        await enterApplication();
    } catch (error) {
        console.error("Registration verification error:", error);
        showAuthMessage(error.message);
    } finally {
        setButtonLoading(button, false, "Verifying...", "Verify Email");
    }
}

// ============================================================
// LOGIN
// ============================================================

async function handleLogin(event) {
    event.preventDefault();

    const email = loginEmail.value.trim().toLowerCase();
    const password = loginPassword.value;

    if (!email || !password) {
        showAuthMessage("Enter your email and password.");
        return;
    }

    const button = document.getElementById("login-button");
    setButtonLoading(button, true, "Checking...", "Continue");

    try {
        const data = await authRequest("/api/auth/login", {
            email,
            password
        });

        const emailLabel = document.getElementById("login-otp-email");
        if (emailLabel) emailLabel.textContent = email;

        showAuthForm(verifyLoginForm);
        showAuthMessage(data.message || "Login OTP sent to your email.", true);
    } catch (error) {
        console.error("Login error:", error);
        showAuthMessage(error.message);
    } finally {
        setButtonLoading(button, false, "Checking...", "Continue");
    }
}

async function handleVerifyLogin(event) {
    event.preventDefault();

    const email = loginEmail.value.trim().toLowerCase();
    const otp = loginOtp.value.trim();

    if (!/^\d{6}$/.test(otp)) {
        showAuthMessage("Enter a valid 6-digit OTP.");
        return;
    }

    const button = document.getElementById("verify-login-button");
    setButtonLoading(button, true, "Verifying...", "Verify & Login");

    try {
        const data = await authRequest("/api/auth/verify-login", {
            email,
            otp
        });

        if (!data.token || !data.user) {
            throw new Error("The server did not return login data.");
        }

        saveAuthData(data.token, data.user);
        await enterApplication();
    } catch (error) {
        console.error("Login verification error:", error);
        showAuthMessage(error.message);
    } finally {
        setButtonLoading(button, false, "Verifying...", "Verify & Login");
    }
}

// ============================================================
// PASSWORD RESET
// ============================================================

async function handleForgotPassword(event) {
    event.preventDefault();

    const email = resetEmail.value.trim().toLowerCase();

    if (!email) {
        showAuthMessage("Enter your registered email.");
        return;
    }

    const button = document.getElementById("forgot-password-button");
    setButtonLoading(button, true, "Sending OTP...", "Send Reset OTP");

    try {
        const data = await authRequest("/api/auth/forgot-password", { email });

        const emailLabel = document.getElementById("reset-otp-email");
        if (emailLabel) emailLabel.textContent = email;

        showAuthForm(resetPasswordForm);
        showAuthMessage(data.message || "Password reset OTP sent.", true);
    } catch (error) {
        console.error("Forgot password error:", error);
        showAuthMessage(error.message);
    } finally {
        setButtonLoading(button, false, "Sending OTP...", "Send Reset OTP");
    }
}

async function handleResetPassword(event) {
    event.preventDefault();

    const email = resetEmail.value.trim().toLowerCase();
    const otp = resetOtp.value.trim();
    const newPassword = resetNewPassword.value;

    if (!/^\d{6}$/.test(otp)) {
        showAuthMessage("Enter a valid 6-digit OTP.");
        return;
    }

    if (newPassword.length < 8) {
        showAuthMessage("New password must contain at least 8 characters.");
        return;
    }

    const button = document.getElementById("reset-password-button");
    setButtonLoading(button, true, "Resetting...", "Reset Password");

    try {
        const data = await authRequest("/api/auth/reset-password", {
            email,
            otp,
            new_password: newPassword
        });

        resetPasswordForm.reset();
        loginPassword.value = "";
        loginEmail.value = email;

        showLoginTab();
        showAuthMessage(
            data.message || "Password reset successfully. Please log in.",
            true
        );
    } catch (error) {
        console.error("Password reset error:", error);
        showAuthMessage(error.message);
    } finally {
        setButtonLoading(button, false, "Resetting...", "Reset Password");
    }
}

// ============================================================
// CHAT DISPLAY AND MARKDOWN
// ============================================================

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatInlineMarkdown(value) {
    let text = escapeHtml(value);
    const codeSnippets = [];

    text = text.replace(/`([^`]+)`/g, (match, code) => {
        const marker = `\u0000CODE${codeSnippets.length}\u0000`;
        codeSnippets.push(`<code>${code}</code>`);
        return marker;
    });

    text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/\*(.+?)\*/g, "<em>$1</em>");

    codeSnippets.forEach((code, index) => {
        text = text.replace(`\u0000CODE${index}\u0000`, code);
    });

    return text;
}

function renderAssistantMarkdown(markdown) {
    const lines = String(markdown || "").replace(/\r/g, "").split("\n");
    const html = [];
    let paragraph = [];
    let listItems = [];
    let listType = null;

    function flushParagraph() {
        if (!paragraph.length) return;

        html.push(
            `<p>${paragraph.map(formatInlineMarkdown).join("<br>")}</p>`
        );
        paragraph = [];
    }

    function flushList() {
        if (!listItems.length) return;

        const tag = listType === "numbered" ? "ol" : "ul";
        const items = listItems
            .map(item => `<li>${formatInlineMarkdown(item)}</li>`)
            .join("");

        html.push(`<${tag}>${items}</${tag}>`);
        listItems = [];
        listType = null;
    }

    for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        const trimmed = line.trim();

        if (!trimmed) {
            flushParagraph();
            flushList();
            continue;
        }

        if (trimmed.startsWith("```")) {
            flushParagraph();
            flushList();

            const codeLines = [];
            index += 1;

            while (index < lines.length && !lines[index].trim().startsWith("```")) {
                codeLines.push(lines[index]);
                index += 1;
            }

            html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
            continue;
        }

        const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
        if (heading) {
            flushParagraph();
            flushList();

            const level = heading[1].length;
            html.push(
                `<h${level}>${formatInlineMarkdown(heading[2])}</h${level}>`
            );
            continue;
        }

        const bullet = trimmed.match(/^[-*]\s+(.+)$/);
        const numbered = trimmed.match(/^\d+[.)]\s+(.+)$/);

        if (bullet || numbered) {
            flushParagraph();

            const nextType = numbered ? "numbered" : "bullet";
            if (listType && listType !== nextType) {
                flushList();
            }

            listType = nextType;
            listItems.push((bullet || numbered)[1]);
            continue;
        }

        flushList();
        paragraph.push(trimmed);
    }

    flushParagraph();
    flushList();

    return html.join("");
}

function addChatMessage(role, text) {
    if (!chatBox) return;

    const isUser = role === "user";

    const message = document.createElement("div");
    message.className = isUser
        ? "message user-message"
        : "message bot-message";

    const icon = document.createElement("div");
    icon.className = "message-icon";
    icon.textContent = isUser ? "👤" : "🤖";

    const content = document.createElement("div");
    content.className = "message-content";

    const name = document.createElement("div");
    name.className = "message-name";
    name.textContent = isUser ? "You" : "INGRES Assistant";

    const body = document.createElement("div");
    body.className = "message-text";

    if (isUser) {
        body.textContent = String(text || "");
        body.style.whiteSpace = "pre-wrap";
    } else {
        body.innerHTML = renderAssistantMarkdown(text);
    }

    content.append(name, body);
    message.append(icon, content);
    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showWelcomeMessage() {
    if (!chatBox) return;

    chatBox.innerHTML = "";

    const message = document.createElement("div");
    message.className = "message bot-message";
    message.innerHTML = `
        <div class="message-icon">🤖</div>
        <div class="message-content">
            <div class="message-name">INGRES Assistant</div>
            <div class="message-text">
                <p>Hello! 👋</p>
                <p>Welcome to <strong>INGRES AI Virtual Assistant</strong>.</p>
                <p>How can I help you today?</p>
            </div>
        </div>
    `;

    chatBox.appendChild(message);
}

function setTyping(visible) {
    if (!typingIndicator) return;
    typingIndicator.classList.toggle("hidden", !visible);
}

// ============================================================
// CHAT API AND HISTORY
// ============================================================

async function readApiResponse(response) {
    let data = {};

    try {
        data = await response.json();
    } catch (error) {
        console.error("Server response was not JSON:", error);
    }

    if (!response.ok || data.success === false) {
        throw new Error(
            data.message || `Request failed (HTTP ${response.status}).`
        );
    }

    return data;
}

async function handleSendMessage() {
    if (!userInput || !sendButton || isSending) return;

    const message = userInput.value.trim();
    if (!message) return;

    if (!getAuthToken()) {
        showLoginScreen();
        showLoginTab();
        return;
    }

    isSending = true;
    sendButton.disabled = true;
    userInput.disabled = true;
    userInput.value = "";

    addChatMessage("user", message);
    setTyping(true);

    try {
        const response = await authFetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message,
                conversation_id: currentConversationId
            })
        });

        const data = await readApiResponse(response);

        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
        }

        addChatMessage("assistant", data.response || "I couldn't generate a response.");
        await loadRecentChats();
    } catch (error) {
        console.error("Chat request error:", error);
        addChatMessage("assistant", `Sorry, ${error.message}`);
    } finally {
        isSending = false;
        sendButton.disabled = false;
        userInput.disabled = false;
        setTyping(false);
        userInput.focus();
    }
}

async function loadRecentChats() {
    if (!recentChatList || !getAuthToken()) return;

    const response = await authFetch("/api/chats", {
        method: "GET"
    });
    const data = await readApiResponse(response);

    recentChatList.innerHTML = "";

    const chats = (Array.isArray(data.chats) ? data.chats : [])
        .filter(chat =>
            chat.title &&
            chat.title.trim() &&
            chat.title.trim().toLowerCase() !== "new chat"
        );

    if (chats.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-chat-message";
        empty.textContent = "Your recent chats will appear here.";
        recentChatList.appendChild(empty);
        return;
    }

    chats.forEach(chat => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "recent-chat-item";

        if (chat.id === currentConversationId) {
            button.classList.add("active");
        }

        const title = document.createElement("span");
        title.className = "recent-chat-title";
        title.textContent = chat.title.trim();

        button.appendChild(title);
        button.addEventListener("click", () => openConversation(chat.id));
        recentChatList.appendChild(button);
    });
}

async function openConversation(conversationId) {
    if (!conversationId) return;

    try {
        const response = await authFetch(
            `/api/chats/${encodeURIComponent(conversationId)}`,
            { method: "GET" }
        );
        const data = await readApiResponse(response);

        currentConversationId = data.conversation_id || conversationId;

        if (chatBox) chatBox.innerHTML = "";

        const messages = Array.isArray(data.messages) ? data.messages : [];

        if (!messages.length) {
            showWelcomeMessage();
        } else {
            messages.forEach(item => {
                if (item.role === "user" || item.role === "assistant") {
                    addChatMessage(item.role, item.message || "");
                }
            });
        }

        await loadRecentChats();
        closeNewChatMenu();
    } catch (error) {
        console.error("Unable to open conversation:", error);
        window.alert(error.message);
    }
}

function resetChatDisplay() {
    currentConversationId = null;
    showWelcomeMessage();
    loadRecentChats().catch(error => {
        console.error("Unable to refresh chat list:", error);
    });
}

// ============================================================
// NEW CHAT MENU ACTIONS
// ============================================================

function closeNewChatMenu() {
    if (newChatMenu) {
        newChatMenu.classList.add("hidden");
    }

    if (newChatButton) {
        newChatButton.setAttribute("aria-expanded", "false");
    }
}

async function handleClearChat() {
    closeNewChatMenu();

    if (!currentConversationId) {
        showWelcomeMessage();
        return;
    }

    if (!window.confirm("Delete this chat and all its messages?")) return;

    try {
        const response = await authFetch(
            `/api/chats/${encodeURIComponent(currentConversationId)}`,
            { method: "DELETE" }
        );
        await readApiResponse(response);

        currentConversationId = null;
        showWelcomeMessage();
        await loadRecentChats();
    } catch (error) {
        console.error("Unable to delete chat:", error);
        window.alert(error.message);
    }
}

async function handleClearConversationMemory() {
    closeNewChatMenu();

    if (!currentConversationId) {
        showWelcomeMessage();
        return;
    }

    if (!window.confirm("Delete the messages and memory from this conversation?")) return;

    try {
        const response = await authFetch(
            `/api/chats/${encodeURIComponent(currentConversationId)}/messages`,
            { method: "DELETE" }
        );
        await readApiResponse(response);

        showWelcomeMessage();
        await loadRecentChats();
    } catch (error) {
        console.error("Unable to clear conversation memory:", error);
        window.alert(error.message);
    }
}

function handleStartFresh() {
    closeNewChatMenu();
    currentConversationId = null;
    showWelcomeMessage();
}

// ============================================================
// ACCOUNT MENU
// ============================================================

function closeAccountMenu() {
    if (accountMenu) {
        accountMenu.classList.add("hidden");
    }

    if (accountButton) {
        accountButton.setAttribute("aria-expanded", "false");
    }
}

function toggleAccountMenu(event) {
    event.stopPropagation();

    if (!accountMenu) return;

    const willOpen = accountMenu.classList.contains("hidden");
    accountMenu.classList.toggle("hidden", !willOpen);

    if (accountButton) {
        accountButton.setAttribute("aria-expanded", String(willOpen));
    }
}

function returnToLogin() {
    clearAuthData();
    currentConversationId = null;
    closeAccountMenu();

    if (recentChatList) recentChatList.innerHTML = "";
    showLoginScreen();
    showLoginTab();
}

// ============================================================
// INITIALIZATION
// ============================================================

function bind(id, eventName, handler) {
    const element = document.getElementById(id);
    if (element) element.addEventListener(eventName, handler);
}

function initializeApp() {
    loginScreen = document.getElementById("login-screen");
    appContainer = document.getElementById("app-container");

    createTab = document.getElementById("create-tab");
    loginTab = document.getElementById("login-tab");

    createAccountForm = document.getElementById("create-account-form");
    loginAccountForm = document.getElementById("login-account-form");
    verifyRegistrationForm = document.getElementById("verify-registration-form");
    verifyLoginForm = document.getElementById("verify-login-form");
    forgotPasswordForm = document.getElementById("forgot-password-form");
    resetPasswordForm = document.getElementById("reset-password-form");

    authName = document.getElementById("auth-name");
    authEmail = document.getElementById("auth-email");
    authPassword = document.getElementById("auth-password");
    authConfirmPassword = document.getElementById("auth-confirm-password");
    loginEmail = document.getElementById("login-email");
    loginPassword = document.getElementById("login-password");
    registrationOtp = document.getElementById("registration-otp");
    loginOtp = document.getElementById("login-otp");
    resetOtp = document.getElementById("reset-otp");
    resetEmail = document.getElementById("reset-email");
    resetNewPassword = document.getElementById("reset-new-password");
    authMessage = document.getElementById("auth-message");

    chatBox = document.getElementById("chat-box");
    userInput = document.getElementById("user-input");
    sendButton = document.getElementById("send-button");
    typingIndicator = document.getElementById("typing");
    recentChatList = document.getElementById("recent-chat-list");

    accountName = document.getElementById("account-name");
    accountDisplayName = document.getElementById("account-display-name");
    accountDisplayEmail = document.getElementById("account-display-email");
    accountButton = document.getElementById("account-button");
    accountMenu = document.getElementById("account-menu");

    newChatButton = document.getElementById("new-chat-button");
    newChatMenu = document.getElementById("new-chat-menu");

    if (createTab) createTab.addEventListener("click", showCreateTab);
    if (loginTab) loginTab.addEventListener("click", showLoginTab);

    if (createAccountForm) {
        createAccountForm.addEventListener("submit", handleCreateAccount);
    }
    if (verifyRegistrationForm) {
        verifyRegistrationForm.addEventListener("submit", handleVerifyRegistration);
    }
    if (loginAccountForm) {
        loginAccountForm.addEventListener("submit", handleLogin);
    }
    if (verifyLoginForm) {
        verifyLoginForm.addEventListener("submit", handleVerifyLogin);
    }
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener("submit", handleForgotPassword);
    }
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener("submit", handleResetPassword);
    }

    bind("registration-back-button", "click", showCreateTab);
    bind("login-back-button", "click", showLoginTab);
    bind("forgot-back-button", "click", showLoginTab);
    bind("reset-back-button", "click", showLoginTab);

    bind("forgot-password-link", "click", () => {
        if (resetEmail && loginEmail) {
            resetEmail.value = loginEmail.value.trim().toLowerCase();
        }
        showAuthForm(forgotPasswordForm);
    });

    document.querySelectorAll("[data-toggle-password]").forEach(button => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.togglePassword);
            if (!input) return;

            const showPassword = input.type === "password";
            input.type = showPassword ? "text" : "password";
            button.textContent = showPassword ? "Hide" : "Show";
            button.setAttribute(
                "aria-label",
                showPassword ? "Hide password" : "Show password"
            );
        });
    });

    if (sendButton) {
        sendButton.addEventListener("click", handleSendMessage);
    }

    if (userInput) {
        userInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                handleSendMessage();
            }
        });
    }

    if (accountButton && accountMenu) {
        accountButton.addEventListener("click", toggleAccountMenu);
    }

    bind("logout-button", "click", returnToLogin);
    bind("switch-account-button", "click", returnToLogin);

    if (newChatButton && newChatMenu) {
        newChatButton.addEventListener("click", event => {
            event.stopPropagation();
            const willOpen = newChatMenu.classList.contains("hidden");
            newChatMenu.classList.toggle("hidden", !willOpen);
            newChatButton.setAttribute("aria-expanded", String(willOpen));
        });
    }

    bind("clear-chat-button", "click", handleClearChat);
    bind("clear-memory-button", "click", handleClearConversationMemory);
    bind("start-fresh-button", "click", handleStartFresh);

    document.addEventListener("click", event => {
        if (
            accountMenu &&
            accountButton &&
            !accountMenu.contains(event.target) &&
            !accountButton.contains(event.target)
        ) {
            closeAccountMenu();
        }

        if (
            newChatMenu &&
            newChatButton &&
            !newChatMenu.contains(event.target) &&
            !newChatButton.contains(event.target)
        ) {
            closeNewChatMenu();
        }
    });

    bind("open-sidebar-button", "click", () => {
        const sidebar = document.getElementById("sidebar");
        if (sidebar) sidebar.classList.toggle("open");
    });

    bind("close-sidebar-button", "click", () => {
        const sidebar = document.getElementById("sidebar");
        if (sidebar) sidebar.classList.remove("open");
    });

    const token = getAuthToken();
    const user = getCurrentUser();

    if (token && user) {
        showApplication();
        loadRecentChats().catch(error => {
            console.error("Unable to load recent chats:", error);
        });
    } else {
        showLoginScreen();
        showCreateTab();
    }
}

async function enterApplication() {
    currentConversationId = null;
    showApplication();
    showWelcomeMessage();

    try {
        await loadRecentChats();
    } catch (error) {
        console.error("Unable to load recent chats:", error);
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeApp);
} else {
    initializeApp();
}