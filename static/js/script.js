
"use strict";

// ============================================================
// INGRES AI VIRTUAL ASSISTANT
// SECRET ID LOGIN + JWT + MONGODB CHAT HISTORY
// ============================================================


// ============================================================
// GLOBAL VARIABLES
// ============================================================

let chatBox;
let userInput;
let sendButton;
let typingIndicator;
let recentChatList;

let newChatButton;
let newChatMenu;
let clearChatButton;
let clearMemoryButton;
let clearMessagesButton;
let startFreshButton;

let accountButton;
let accountMenu;
let accountName;
let accountDisplayName;
let accountDisplayEmail;
let switchAccountButton;
let logoutButton;

let openSidebarButton;
let closeSidebarButton;
let sidebar;

let currentConversationId = null;
let isSending = false;
let isClearing = false;


// ============================================================
// AUTHENTICATION ELEMENTS
// ============================================================

let loginScreen;
let appContainer;

let createTab;
let loginTab;
let createAccountForm;
let loginAccountForm;

let authName;
let loginName;
let authSecretId;

let authMessage;
let secretIdResult;
let secretIdValue;
let copySecretIdButton;
let continueButton;


// ============================================================
// AUTHENTICATION STORAGE
// ============================================================

function getAuthToken() {
    return localStorage.getItem("ingres_token");
}

function getCurrentUser() {
    try {
        return JSON.parse(
            localStorage.getItem("ingres_user")
        );
    } catch (error) {
        console.error("Unable to read user information:", error);
        return null;
    }
}

function saveAuthData(token, user) {
    localStorage.setItem("ingres_token", token);
    localStorage.setItem("ingres_user", JSON.stringify(user));

    localStorage.removeItem("ingres_visitor_token");
}

function clearAuthData() {
    localStorage.removeItem("ingres_token");
    localStorage.removeItem("ingres_user");
    localStorage.removeItem("ingresToken");
    localStorage.removeItem("ingresUser");
    localStorage.removeItem("ingres_visitor_token");
}


// ============================================================
// LOGIN MODE
// ============================================================

function isLoginOnlyMode() {
    return localStorage.getItem("ingres_login_only") === "true";
}


// ============================================================
// API AUTHENTICATION
// ============================================================

async function registerWithName(name) {
    const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name
        })
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message || "Account creation failed."
        );
    }

    saveAuthData(data.token, data.user);

    return data;
}


async function loginWithSecretId(name, secretId) {
    const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            secret_id: secretId
        })
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message || "Invalid name or Secret ID."
        );
    }

    saveAuthData(data.token, data.user);

    return data;
}


async function authFetch(url, options = {}) {
    const token = getAuthToken();

    if (!token) {
        throw new Error("Please log in to continue.");
    }

    const headers = {
        ...(options.headers || {}),
        "Authorization": `Bearer ${token}`
    };

    const response = await fetch(url, {
        ...options,
        headers: headers
    });

    if (response.status === 401) {
        clearAuthData();

        localStorage.setItem(
            "ingres_login_only",
            "true"
        );

        showLoginOnlyScreen();

        throw new Error(
            "Your session expired. Please log in again."
        );
    }

    return response;
}


// ============================================================
// SHOW / HIDE SCREENS
// ============================================================

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


// ============================================================
// AUTHENTICATION TABS
// ============================================================

function showCreateTab() {
    if (isLoginOnlyMode()) {
        showLoginOnlyScreen();
        return;
    }

    createTab.style.display = "block";
    loginTab.style.display = "block";

    createTab.textContent = "Create Account";
    loginTab.textContent = "Existing Account";

    createTab.classList.add("active");
    loginTab.classList.remove("active");

    createAccountForm.style.display = "block";
    loginAccountForm.style.display = "none";

    secretIdResult.style.display = "none";
    authMessage.textContent = "";
}


function showLoginTab() {
    if (isLoginOnlyMode()) {
        showLoginOnlyScreen();
        return;
    }

    createTab.classList.remove("active");
    loginTab.classList.add("active");

    createAccountForm.style.display = "none";
    loginAccountForm.style.display = "block";

    secretIdResult.style.display = "none";
    authMessage.textContent = "";
}


// ============================================================
// LOGIN-ONLY SCREEN
// This displays only the form's Login button.
// Both tab buttons are hidden.
// ============================================================

function showLoginOnlyScreen() {
    showLoginScreen();

    createTab.style.display = "none";
    loginTab.style.display = "none";

    createAccountForm.style.display = "none";
    loginAccountForm.style.display = "block";

    secretIdResult.style.display = "none";
    authMessage.textContent = "";

    if (loginName) {
        loginName.value = "";
    }

    if (authSecretId) {
        authSecretId.value = "";
    }
}


// ============================================================
// CREATE ACCOUNT
// ============================================================

async function handleCreateAccount(event) {
    event.preventDefault();

    authMessage.textContent = "";
    secretIdResult.style.display = "none";

    const name = authName.value.trim();

    if (!name) {
        authMessage.textContent = "Please enter your name.";
        return;
    }

    const button = document.getElementById(
        "create-account-button"
    );

    if (!button) return;

    button.disabled = true;
    button.textContent = "Creating account...";

    try {
        const data = await registerWithName(name);

        if (!data.secret_id) {
            throw new Error(
                "Secret ID was not returned by the server."
            );
        }

        localStorage.setItem(
            "ingres_login_only",
            "true"
        );

        secretIdValue.textContent = data.secret_id;

        secretIdResult.style.display = "block";

        createAccountForm.style.display = "none";
        loginAccountForm.style.display = "none";

        authMessage.textContent = "";

    } catch (error) {
        console.error("Registration error:", error);

        authMessage.textContent =
            error.message || "Unable to create account.";

    } finally {
        button.disabled = false;
        button.textContent = "Create My Account";
    }
}


// ============================================================
// LOGIN
// ============================================================

async function handleLogin(event) {
    event.preventDefault();

    authMessage.textContent = "";

    const name = loginName.value.trim();
    const secretId = authSecretId.value.trim();

    if (!name || !secretId) {
        authMessage.textContent =
            "Enter your name and Secret ID.";

        return;
    }

    const button = document.getElementById("login-button");

    if (!button) return;

    button.disabled = true;
    button.textContent = "Logging in...";

    try {
        await loginWithSecretId(name, secretId);

        localStorage.setItem(
            "ingres_login_only",
            "true"
        );

        currentConversationId = null;

        showApplication();
        showWelcomeMessage();

        await loadRecentChats();

        loginName.value = "";
        authSecretId.value = "";

    } catch (error) {
        console.error("Login error:", error);

        authMessage.textContent =
            error.message || "Login failed.";

    } finally {
        button.disabled = false;
        button.textContent = "Login";
    }
}


// ============================================================
// COPY SECRET ID
// ============================================================

async function copySecretId() {
    const secretId = secretIdValue.textContent;

    try {
        await navigator.clipboard.writeText(secretId);

        copySecretIdButton.textContent = "Copied!";

    } catch (error) {
        const temporaryInput =
            document.createElement("textarea");

        temporaryInput.value = secretId;

        document.body.appendChild(temporaryInput);

        temporaryInput.select();
        document.execCommand("copy");

        temporaryInput.remove();

        copySecretIdButton.textContent = "Copied!";
    }
}


// ============================================================
// CONTINUE AFTER REGISTRATION
// ============================================================

async function continueAfterRegistration() {
    secretIdResult.style.display = "none";

    showApplication();

    currentConversationId = null;

    showWelcomeMessage();

    await loadRecentChats();
}


// ============================================================
// AUTOMATIC LOGIN
// ============================================================

async function startAuthentication() {
    const token = getAuthToken();
    const user = getCurrentUser();

    if (token && user) {
        showApplication();

        await loadRecentChats();

        return true;
    }

    if (isLoginOnlyMode()) {
        showLoginOnlyScreen();
    } else {
        showLoginScreen();
        showCreateTab();
    }

    return false;
}


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// MARKDOWN RENDERING
// ============================================================

function renderMarkdown(value) {
    if (!value) return "";

    let text = String(value);

    const codeBlocks = [];

    // Preserve fenced code blocks.
    text = text.replace(
        /```([^\n`]*)\n?([\s\S]*?)```/g,
        function (match, language, code) {
            const lang = language.trim().split(/\s+/)[0];

            const html = `
                <pre class="code-block">
                    <code class="${lang ? "language-" + escapeHtml(lang) : ""}">${escapeHtml(code.trim())}</code>
                </pre>
            `;

            const placeholder =
                `@@CODEBLOCK${codeBlocks.length}@@`;

            codeBlocks.push(html);

            return placeholder;
        }
    );

    text = escapeHtml(text);

    // Inline code.
    text = text.replace(
        /`([^`\n]+)`/g,
        "<code>$1</code>"
    );

    // Bold.
    text = text.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Italic.
    text = text.replace(
        /\*([^*\n]+)\*/g,
        "<em>$1</em>"
    );

    // Headings.
    text = text.replace(
        /^### (.*)$/gm,
        "<h4>$1</h4>"
    );

    text = text.replace(
        /^## (.*)$/gm,
        "<h3>$1</h3>"
    );

    text = text.replace(
        /^# (.*)$/gm,
        "<h2>$1</h2>"
    );

    // Links.
    text = text.replace(
        /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
        function (match, label, url) {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
        }
    );

    // Unordered lists.
    text = text.replace(
        /^(?:- |\* )(.+)$/gm,
        "<li>$1</li>"
    );

    text = text.replace(
        /(?:<li>.*?<\/li>\n?)+/gs,
        function (items) {
            return "<ul>" + items + "</ul>";
        }
    );

    // Numbered lists.
    text = text.replace(
        /^\d+\.\s+(.+)$/gm,
        "<li>$1</li>"
    );

    text = text.replace(/\n/g, "<br>");

    // Restore code blocks.
    codeBlocks.forEach(function (html, index) {
        text = text.replace(
            `@@CODEBLOCK${index}@@`,
            html
        );
    });

    return text;
}


// ============================================================
// ADD MESSAGE TO CHAT
// ============================================================

function addMessage(message, sender) {
    if (!chatBox) return;

    const wrapper = document.createElement("div");

    wrapper.className =
        sender === "user"
            ? "message user-message"
            : "message bot-message";

    const icon = document.createElement("div");
    icon.className = "message-icon";
    icon.textContent = sender === "user" ? "👤" : "🤖";

    const content = document.createElement("div");
    content.className = "message-content";

    const name = document.createElement("div");
    name.className = "message-name";

    name.textContent =
        sender === "user" ? "You" : "INGRES Assistant";

    const messageText = document.createElement("div");
    messageText.className = "message-text";

    if (sender === "assistant") {
        messageText.innerHTML = renderMarkdown(message);
    } else {
        messageText.textContent = String(message);
    }

    content.appendChild(name);
    content.appendChild(messageText);

    wrapper.appendChild(icon);
    wrapper.appendChild(content);

    chatBox.appendChild(wrapper);

    chatBox.scrollTop = chatBox.scrollHeight;
}


// ============================================================
// WELCOME MESSAGE
// ============================================================

function showWelcomeMessage() {
    if (!chatBox) return;

    chatBox.innerHTML = "";

    addMessage(
        "## 👋 Hello!\n" +
        "Welcome to the **INGRES AI Virtual Assistant**.\n" +
        "How can I help you today?",
        "assistant"
    );
}


// ============================================================
// TYPING INDICATOR
// ============================================================

function showTyping() {
    if (typingIndicator) {
        typingIndicator.classList.remove("hidden");
    }
}

function hideTyping() {
    if (typingIndicator) {
        typingIndicator.classList.add("hidden");
    }
}


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {
    if (isSending || !userInput) return;

    const message = userInput.value.trim();

    if (!message) return;

    isSending = true;

    if (sendButton) {
        sendButton.disabled = true;
    }

    addMessage(message, "user");

    userInput.value = "";

    showTyping();

    try {
        const response = await authFetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to send your message."
            );
        }

        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
        }

        addMessage(
            data.response || "I couldn't generate a response.",
            "assistant"
        );

        await loadRecentChats();

    } catch (error) {
        console.error("Send message error:", error);

        addMessage(
            "Sorry, your message could not be processed. Please try again.",
            "assistant"
        );

    } finally {
        isSending = false;

        hideTyping();

        if (sendButton) {
            sendButton.disabled = false;
        }

        if (userInput) {
            userInput.focus();
        }
    }
}


// ============================================================
// LOAD RECENT CHATS
// ============================================================

async function loadRecentChats() {
    if (!recentChatList || !getAuthToken()) return;

    try {
        const response = await authFetch("/api/chats");

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to load recent chats."
            );
        }

        recentChatList.innerHTML = "";

        const chats = Array.isArray(data.chats)
            ? data.chats
            : [];

        if (chats.length === 0) {
            const empty = document.createElement("div");

            empty.className = "empty-chat-message";
            empty.textContent = "No recent chats";

            recentChatList.appendChild(empty);

            return;
        }

        chats.forEach(function (chat) {
            const chatId = chat.id || chat._id;

            if (!chatId) return;

            const item = document.createElement("div");
            item.className = "recent-chat-item";

            if (
                String(chatId) ===
                String(currentConversationId)
            ) {
                item.classList.add("active");
            }

            const title = document.createElement("span");
            title.className = "recent-chat-title";
            title.textContent = chat.title || "New Chat";

            const deleteButton =
                document.createElement("button");

            deleteButton.type = "button";
            deleteButton.className = "delete-chat-button";
            deleteButton.textContent = "🗑️";
            deleteButton.title = "Delete chat";

            deleteButton.addEventListener(
                "click",
                async function (event) {
                    event.preventDefault();
                    event.stopPropagation();

                    await deleteChat(
                        chatId,
                        chat.title || "New Chat"
                    );
                }
            );

            item.appendChild(title);
            item.appendChild(deleteButton);

            item.addEventListener("click", function () {
                openConversation(chatId);
            });

            recentChatList.appendChild(item);
        });

    } catch (error) {
        console.error("Load recent chats error:", error);
    }
}


// ============================================================
// DELETE SAVED CHAT
// ============================================================

async function deleteChat(conversationId, title) {
    const confirmed = window.confirm(
        `Delete "${title}"?\n\n` +
        "This conversation and its saved messages will be permanently deleted."
    );

    if (!confirmed) return;

    try {
        const response = await authFetch(
            `/api/chats/${encodeURIComponent(conversationId)}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to delete this chat."
            );
        }

        if (
            String(currentConversationId) ===
            String(conversationId)
        ) {
            currentConversationId = null;
            showWelcomeMessage();
        }

        await loadRecentChats();

    } catch (error) {
        console.error("Delete chat error:", error);

        alert(error.message || "Unable to delete the chat.");
    }
}


// ============================================================
// OPEN SAVED CONVERSATION
// ============================================================

async function openConversation(conversationId) {
    try {
        const response = await authFetch(
            `/api/chats/${encodeURIComponent(conversationId)}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to open this conversation."
            );
        }

        currentConversationId = conversationId;

        chatBox.innerHTML = "";

        const messages = Array.isArray(data.messages)
            ? data.messages
            : [];

        if (messages.length === 0) {
            addMessage(
                "This conversation is empty.",
                "assistant"
            );
        } else {
            messages.forEach(function (message) {
                addMessage(
                    message.message || "",
                    message.role === "user" ? "user" : "assistant"
                );
            });
        }

        await loadRecentChats();

        if (sidebar) {
            sidebar.classList.remove("open");
        }

        if (userInput) {
            userInput.focus();
        }

    } catch (error) {
        console.error("Open conversation error:", error);

        alert(
            error.message || "Unable to open this conversation."
        );
    }
}


// ============================================================
// NEW CHAT
// ============================================================

function newChat() {
    currentConversationId = null;

    showWelcomeMessage();

    if (userInput) {
        userInput.value = "";
        userInput.focus();
    }

    if (newChatMenu) {
        newChatMenu.classList.add("hidden");
    }

    if (sidebar) {
        sidebar.classList.remove("open");
    }

    loadRecentChats();
}


// ============================================================
// CLEAR CHAT
// ============================================================

async function clearCurrentMessages() {
    await clearActiveConversation(
        "Clear Chat will permanently delete this conversation and its saved messages. Continue?",
        "Chat cleared. You can start a new conversation."
    );
}


// ============================================================
// CLEAR CONVERSATION MEMORY
// ============================================================

async function clearConversationMemory() {
    await clearActiveConversation(
        "Clear Conversation Memory will permanently delete this conversation and its saved messages. Continue?",
        "Conversation memory cleared. Start a new conversation."
    );
}


// ============================================================
// SHARED CLEAR FUNCTION
// ============================================================

async function clearActiveConversation(
    confirmText,
    successText
) {
    if (isClearing) return;

    if (!window.confirm(confirmText)) return;

    isClearing = true;

    const conversationId = currentConversationId;

    try {
        if (conversationId) {
            const response = await authFetch(
                `/api/chats/${encodeURIComponent(conversationId)}`,
                {
                    method: "DELETE"
                }
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message ||
                    "The conversation could not be deleted."
                );
            }
        }

        currentConversationId = null;

        if (chatBox) {
            chatBox.innerHTML = "";
        }

        addMessage(successText, "assistant");

        if (newChatMenu) {
            newChatMenu.classList.add("hidden");
        }

        await loadRecentChats();

        if (userInput) {
            userInput.value = "";
            userInput.focus();
        }

    } catch (error) {
        console.error("Clear conversation error:", error);

        alert(
            error.message ||
            "Unable to clear the conversation."
        );

    } finally {
        isClearing = false;
    }
}


// ============================================================
// ACCOUNT MENU
// ============================================================

function updateAccountUI() {
    const user = getCurrentUser();

    const displayName =
        user && user.name ? user.name : "INGRES User";

    if (accountName) {
        accountName.textContent = displayName;
    }

    if (accountDisplayName) {
        accountDisplayName.textContent = displayName;
    }

    if (accountDisplayEmail) {
        accountDisplayEmail.textContent =
            "INGRES Secret ID account";
    }
}


// ============================================================
// LOGOUT
// ============================================================

function logout() {
    const confirmed = window.confirm(
        "Log out of your INGRES account?\n\n" +
        "Your saved conversations will remain safe."
    );

    if (!confirmed) return;

    localStorage.setItem(
        "ingres_login_only",
        "true"
    );

    clearAuthData();

    currentConversationId = null;

    if (accountMenu) {
        accountMenu.classList.add("hidden");
    }

    showLoginOnlyScreen();
}


// ============================================================
// LOGIN WITH ANOTHER ACCOUNT
// ============================================================

function loginWithAnotherAccount() {
    const confirmed = window.confirm(
        "Login with another INGRES account?\n\n" +
        "Enter the other account's name and Secret ID."
    );

    if (!confirmed) return;

    localStorage.setItem(
        "ingres_login_only",
        "true"
    );

    clearAuthData();

    currentConversationId = null;

    if (accountMenu) {
        accountMenu.classList.add("hidden");
    }

    showLoginOnlyScreen();
}


// ============================================================
// INITIALIZE APPLICATION
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("INGRES AI Assistant loaded.");

    // ========================================================
    // MAIN APPLICATION ELEMENTS
    // ========================================================

    chatBox = document.getElementById("chat-box");
    userInput = document.getElementById("user-input");
    sendButton = document.getElementById("send-button");
    typingIndicator = document.getElementById("typing");

    recentChatList =
        document.getElementById("recent-chat-list");

    newChatButton =
        document.getElementById("new-chat-button");

    newChatMenu =
        document.getElementById("new-chat-menu");

    clearChatButton =
        document.getElementById("clear-chat-button");

    clearMemoryButton =
        document.getElementById("clear-memory-button");

    clearMessagesButton =
        document.getElementById("clear-messages-button");

    startFreshButton =
        document.getElementById("start-fresh-button");

    accountButton =
        document.getElementById("account-button");

    accountMenu =
        document.getElementById("account-menu");

    accountName =
        document.getElementById("account-name");

    accountDisplayName =
        document.getElementById("account-display-name");

    accountDisplayEmail =
        document.getElementById("account-display-email");

    switchAccountButton =
        document.getElementById("switch-account-button");

    logoutButton =
        document.getElementById("logout-button");

    openSidebarButton =
        document.getElementById("open-sidebar-button");

    closeSidebarButton =
        document.getElementById("close-sidebar-button");

    sidebar =
        document.getElementById("sidebar");


    // ========================================================
    // AUTHENTICATION ELEMENTS
    // ========================================================

    loginScreen =
        document.getElementById("login-screen");

    appContainer =
        document.getElementById("app-container");

    createTab =
        document.getElementById("create-tab");

    loginTab =
        document.getElementById("login-tab");

    createAccountForm =
        document.getElementById("create-account-form");

    loginAccountForm =
        document.getElementById("login-account-form");

    authName =
        document.getElementById("auth-name");

    loginName =
        document.getElementById("login-name");

    authSecretId =
        document.getElementById("auth-secret-id");

    authMessage =
        document.getElementById("auth-message");

    secretIdResult =
        document.getElementById("secret-id-result");

    secretIdValue =
        document.getElementById("secret-id-value");

    copySecretIdButton =
        document.getElementById("copy-secret-id-button");

    continueButton =
        document.getElementById("continue-button");


    // ========================================================
    // CHECK REQUIRED AUTHENTICATION ELEMENTS
    // ========================================================

    const requiredAuthElements = [
        loginScreen,
        appContainer,
        createTab,
        loginTab,
        createAccountForm,
        loginAccountForm,
        authName,
        loginName,
        authSecretId,
        authMessage,
        secretIdResult,
        secretIdValue,
        copySecretIdButton,
        continueButton
    ];

    if (requiredAuthElements.some(element => !element)) {
        console.error(
            "Some authentication HTML elements are missing. Check templates/index.html."
        );

        return;
    }


    // ========================================================
    // AUTHENTICATION EVENTS
    // ========================================================

    createTab.addEventListener("click", showCreateTab);
    loginTab.addEventListener("click", showLoginTab);

    createAccountForm.addEventListener(
        "submit",
        handleCreateAccount
    );

    loginAccountForm.addEventListener(
        "submit",
        handleLogin
    );

    copySecretIdButton.addEventListener(
        "click",
        copySecretId
    );

    continueButton.addEventListener(
        "click",
        continueAfterRegistration
    );


    // ========================================================
    // SEND BUTTON
    // ========================================================

    if (sendButton) {
        sendButton.addEventListener("click", function (event) {
            event.preventDefault();
            sendMessage();
        });
    }


    // ========================================================
    // ENTER SENDS MESSAGE
    // ========================================================

    if (userInput) {
        userInput.addEventListener("keydown", function (event) {
            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {
                event.preventDefault();
                sendMessage();
            }
        });
    }


    // ========================================================
    // NEW CHAT MENU
    // ========================================================

    if (newChatButton) {
        newChatButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            if (newChatMenu) {
                newChatMenu.classList.toggle("hidden");
            } else {
                newChat();
            }
        });
    }


    // ========================================================
    // CLEAR CHAT BUTTON
    // ========================================================

    if (clearChatButton) {
        clearChatButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            clearCurrentMessages();
        });
    }

    if (
        clearMessagesButton &&
        clearMessagesButton !== clearChatButton
    ) {
        clearMessagesButton.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopPropagation();

                clearCurrentMessages();
            }
        );
    }


    // ========================================================
    // CLEAR CONVERSATION MEMORY
    // ========================================================

    if (clearMemoryButton) {
        clearMemoryButton.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopPropagation();

                clearConversationMemory();
            }
        );
    }


    // ========================================================
    // START FRESH
    // ========================================================

    if (startFreshButton) {
        startFreshButton.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                newChat();
            }
        );
    }


    // ========================================================
    // ACCOUNT MENU
    // ========================================================

    if (accountButton) {
        accountButton.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopPropagation();

                if (accountMenu) {
                    accountMenu.classList.toggle("hidden");
                }
            }
        );
    }


    // Login with another account.
    if (switchAccountButton) {
        switchAccountButton.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                loginWithAnotherAccount();
            }
        );
    }


    // Logout.
    if (logoutButton) {
        logoutButton.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                logout();
            }
        );
    }


    // ========================================================
    // MOBILE SIDEBAR
    // ========================================================

    function closeMobileSidebar() {
        if (sidebar) {
            sidebar.classList.remove("open");
        }

        document.body.classList.remove(
            "mobile-sidebar-open"
        );

        if (openSidebarButton) {
            openSidebarButton.setAttribute(
                "aria-expanded",
                "false"
            );
        }
    }


    function openMobileSidebar() {
        if (sidebar) {
            sidebar.classList.add("open");
        }

        document.body.classList.add(
            "mobile-sidebar-open"
        );

        if (openSidebarButton) {
            openSidebarButton.setAttribute(
                "aria-expanded",
                "true"
            );
        }
    }


    if (openSidebarButton) {
        openSidebarButton.addEventListener(
            "click",
            function () {
                if (
                    sidebar &&
                    sidebar.classList.contains("open")
                ) {
                    closeMobileSidebar();
                } else {
                    openMobileSidebar();
                }
            }
        );
    }


    if (closeSidebarButton) {
        closeSidebarButton.addEventListener(
            "click",
            closeMobileSidebar
        );
    }


    // ========================================================
    // CLOSE MENUS WHEN CLICKING OUTSIDE
    // ========================================================

    document.addEventListener("click", function (event) {

        if (
            sidebar &&
            sidebar.classList.contains("open") &&
            window.innerWidth <= 768
        ) {
            const clickedSidebar =
                sidebar.contains(event.target);

            const clickedToggle =
                openSidebarButton &&
                openSidebarButton.contains(event.target);

            if (!clickedSidebar && !clickedToggle) {
                closeMobileSidebar();
            }
        }

        if (
            newChatMenu &&
            newChatButton &&
            !newChatMenu.contains(event.target) &&
            !newChatButton.contains(event.target)
        ) {
            newChatMenu.classList.add("hidden");
        }

        if (
            accountMenu &&
            accountButton &&
            !accountMenu.contains(event.target) &&
            !accountButton.contains(event.target)
        ) {
            accountMenu.classList.add("hidden");
        }

    });


    // ========================================================
    // CLOSE SIDEBAR WITH ESCAPE
    // ========================================================

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeMobileSidebar();
        }
    });


    // ========================================================
    // RESET SIDEBAR WHEN SWITCHING TO DESKTOP
    // ========================================================

    window.addEventListener("resize", function () {
        if (window.innerWidth > 768) {
            closeMobileSidebar();
        }
    });


    // ========================================================
    // INITIALIZE AUTHENTICATION
    // ========================================================

    startAuthentication()
        .then(function (authenticated) {

            if (authenticated) {
                updateAccountUI();
            }

        })
        .catch(function (error) {

            console.error(
                "Authentication initialization error:",
                error
            );

            clearAuthData();

            localStorage.setItem(
                "ingres_login_only",
                "true"
            );

            showLoginOnlyScreen();

        });


    console.log(
        "INGRES AI Assistant initialization complete."
    );

});
