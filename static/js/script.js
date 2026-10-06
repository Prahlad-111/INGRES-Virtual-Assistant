// ============================================================
// INGRES AI ASSISTANT
// JWT AUTHENTICATION + MONGODB CHAT HISTORY
// ============================================================

"use strict";

// ============================================================
// GLOBAL VARIABLES
// ============================================================

let chatBox = null;
let userInput = null;
let sendButton = null;
let typingIndicator = null;
let recentChatList = null;

let newChatButton = null;
let newChatMenu = null;

let clearChatButton = null;
let clearMemoryButton = null;
let clearMessagesButton = null;
let startFreshButton = null;

let accountButton = null;
let accountMenu = null;
let accountName = null;
let accountDisplayName = null;
let accountDisplayEmail = null;
let switchAccountButton = null;
let logoutButton = null;

let openSidebarButton = null;
let closeSidebarButton = null;
let sidebar = null;

let currentConversationId = null;
let isSending = false;
let isClearing = false;

// ============================================================
// AUTHENTICATION
// ============================================================

function getAuthToken() {
    return (
        localStorage.getItem("ingres_token") ||
        localStorage.getItem("ingresToken")
    );
}

function getCurrentUser() {
    const savedUser =
        localStorage.getItem("ingres_user") ||
        localStorage.getItem("ingresUser");

    if (!savedUser) {
        return null;
    }

    try {
        return JSON.parse(savedUser);
    } catch (error) {
        console.error("Unable to read user information:", error);
        return null;
    }
}

function clearAuthData() {
    localStorage.removeItem("ingres_token");
    localStorage.removeItem("ingres_user");
    localStorage.removeItem("ingresToken");
    localStorage.removeItem("ingresUser");
}

async function authenticatedFetch(url, options = {}) {
    const token = getAuthToken();

    if (!token) {
        window.location.href = "/login";
        throw new Error("Authentication token is missing.");
    }

    const headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401 || response.status === 403) {
        clearAuthData();
        window.location.href = "/login";

        throw new Error("Authentication expired.");
    }

    return response;
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
    if (!value) {
        return "";
    }

    let text = String(value);
    const codeBlocks = [];

    // Preserve fenced code blocks before processing Markdown.
    text = text.replace(
        /```([^\n`]*)\n?([\s\S]*?)```/g,
        function (match, language, code) {
            const lang = language.trim().split(/\s+/)[0];
            const safeCode = escapeHtml(code.replace(/^\n|\n$/g, ""));

            const html = `
                <pre class="code-block"><code class="${
                    lang ? "language-" + escapeHtml(lang) : ""
                }">${safeCode}</code></pre>
            `;

            const placeholder = `@@CODEBLOCK${codeBlocks.length}@@`;
            codeBlocks.push(html);

            return placeholder;
        }
    );

    // Escape ordinary text.
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
        /(^|[^*])\*([^*\n]+)\*(?!\*)/g,
        "$1<em>$2</em>"
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

    // Unordered lists.
    text = text.replace(
        /^(?:- |\* ).+$/gm,
        function (line) {
            return "<li>" + line.substring(2) + "</li>";
        }
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

    text = text.replace(
        /(?:<li>.*?<\/li>\n?)+/gs,
        function (items) {
            if (items.includes("<ul>")) {
                return items;
            }

            return "<ol>" + items + "</ol>";
        }
    );

    // Links: only allow HTTP(S) URLs.
    text = text.replace(
        /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
        function (match, label, url) {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
        }
    );

    // Newlines.
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
    if (!chatBox) {
        console.error("Chat box was not found.");
        return;
    }

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
    if (isSending) {
        return;
    }

    if (!userInput) {
        console.error("Input element #user-input was not found.");
        return;
    }

    const message = userInput.value.trim();

    if (!message) {
        return;
    }

    if (!getAuthToken()) {
        window.location.href = "/login";
        return;
    }

    isSending = true;

    if (sendButton) {
        sendButton.disabled = true;
    }

    addMessage(message, "user");

    userInput.value = "";
    showTyping();

    try {
        const response = await authenticatedFetch("/api/chat", {
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

        if (error.message !== "Authentication expired.") {
            addMessage(
                "Sorry, your message could not be processed. Please try again.",
                "assistant"
            );
        }
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
    if (!recentChatList) {
        return;
    }

    try {
        const response = await authenticatedFetch("/api/chats");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "Unable to load recent chats.");
        }

        recentChatList.innerHTML = "";

        const chats = Array.isArray(data.chats) ? data.chats : [];

        if (chats.length === 0) {
            const empty = document.createElement("div");
            empty.className = "empty-chat-message";
            empty.textContent = "No recent chats";
            recentChatList.appendChild(empty);
            return;
        }

        chats.forEach(function (chat) {
            const chatId = chat.id || chat._id;

            if (!chatId) {
                return;
            }

            const item = document.createElement("div");
            item.className = "recent-chat-item";

            if (String(chatId) === String(currentConversationId)) {
                item.classList.add("active");
            }

            const title = document.createElement("span");
            title.className = "recent-chat-title";
            title.textContent = chat.title || "New Chat";

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "delete-chat-button";
            deleteButton.textContent = "🗑️";
            deleteButton.title = "Delete chat";

            deleteButton.addEventListener("click", async function (event) {
                event.preventDefault();
                event.stopPropagation();

                await deleteChat(chatId, chat.title || "New Chat");
            });

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
// DELETE A SAVED CHAT
// ============================================================

async function deleteChat(conversationId, title) {
    const confirmed = window.confirm(
        `Delete "${title}"?\n\nThis conversation and its saved messages will be permanently deleted.`
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await authenticatedFetch(
            `/api/chats/${encodeURIComponent(conversationId)}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "Unable to delete this chat.");
        }

        if (String(currentConversationId) === String(conversationId)) {
            currentConversationId = null;
            showWelcomeMessage();
        }

        await loadRecentChats();

    } catch (error) {
        console.error("Delete chat error:", error);

        if (error.message !== "Authentication expired.") {
            alert(error.message || "Unable to delete the chat.");
        }
    }
}

// ============================================================
// WELCOME MESSAGE
// ============================================================

function showWelcomeMessage() {
    if (!chatBox) {
        return;
    }

    chatBox.innerHTML = "";

    addMessage(
        "## 👋 Hello!\nWelcome to the **INGRES AI Virtual Assistant**.\nHow can I help you today?",
        "assistant"
    );
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
// Permanently deletes the ACTIVE conversation from MongoDB.
// ============================================================

async function clearCurrentMessages() {
    await clearActiveConversation(
        "Clear Chat will permanently delete this conversation and its saved messages. Continue?",
        "Chat cleared. You can start a new conversation."
    );
}

// ============================================================
// CLEAR CONVERSATION MEMORY
// Permanently deletes the ACTIVE conversation from MongoDB.
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

async function clearActiveConversation(confirmText, successText) {
    if (isClearing) {
        return;
    }

    if (!window.confirm(confirmText)) {
        return;
    }

    isClearing = true;

    const conversationId = currentConversationId;

    try {
        // Delete the saved conversation and its messages.
        if (conversationId) {
            const response = await authenticatedFetch(
                `/api/chats/${encodeURIComponent(conversationId)}`,
                {
                    method: "DELETE"
                }
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message || "The conversation could not be deleted."
                );
            }
        }

        // Clear the current view only after the delete succeeds.
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

        if (error.message !== "Authentication expired.") {
            alert(
                error.message ||
                "Unable to clear the conversation. Check the Flask terminal and browser console."
            );
        }
    } finally {
        isClearing = false;
    }
}

// ============================================================
// OPEN A SAVED CONVERSATION
// ============================================================

async function openConversation(conversationId) {
    try {
        const response = await authenticatedFetch(
            `/api/chats/${encodeURIComponent(conversationId)}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Unable to open this conversation."
            );
        }

        currentConversationId = conversationId;

        if (chatBox) {
            chatBox.innerHTML = "";
        }

        const messages = Array.isArray(data.messages)
            ? data.messages
            : [];

        if (messages.length === 0) {
            addMessage("This conversation is empty.", "assistant");
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

        if (error.message !== "Authentication expired.") {
            alert(error.message || "Unable to open this conversation.");
        }
    }
}

// ============================================================
// ACCOUNT MENU
// ============================================================

function updateAccountUI() {
    const user = getCurrentUser();

    if (!user) {
        if (accountName) {
            accountName.textContent = "Account";
        }

        if (accountDisplayName) {
            accountDisplayName.textContent = "User";
        }

        if (accountDisplayEmail) {
            accountDisplayEmail.textContent = "Not signed in";
        }

        return;
    }

    const name = user.name || user.username || "User";
    const email = user.email || "No email";

    if (accountName) {
        accountName.textContent = name;
    }

    if (accountDisplayName) {
        accountDisplayName.textContent = name;
    }

    if (accountDisplayEmail) {
        accountDisplayEmail.textContent = email;
    }
}

function loginWithAnotherAccount() {
    clearAuthData();
    window.location.href = "/login";
}

function logout() {
    const confirmed = window.confirm(
        "Are you sure you want to log out?"
    );

    if (!confirmed) {
        return;
    }

    clearAuthData();
    window.location.href = "/login";
}

// ============================================================
// INITIALIZE THE APPLICATION
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    console.log("INGRES AI Assistant loaded.");

    // Get DOM elements only after the page is loaded.
    chatBox = document.getElementById("chat-box");
    userInput = document.getElementById("user-input");
    sendButton = document.getElementById("send-button");
    typingIndicator = document.getElementById("typing");
    recentChatList = document.getElementById("recent-chat-list");

    newChatButton = document.getElementById("new-chat-button");
    newChatMenu = document.getElementById("new-chat-menu");

    // IMPORTANT: Match the IDs in your actual HTML.
    clearChatButton = document.getElementById("clear-chat-button");
    clearMemoryButton = document.getElementById("clear-memory-button");

    // Support older HTML if this ID still exists.
    clearMessagesButton = document.getElementById("clear-messages-button");

    startFreshButton = document.getElementById("start-fresh-button");

    accountButton = document.getElementById("account-button");
    accountMenu = document.getElementById("account-menu");
    accountName = document.getElementById("account-name");
    accountDisplayName = document.getElementById("account-display-name");
    accountDisplayEmail = document.getElementById("account-display-email");
    switchAccountButton = document.getElementById("switch-account-button");
    logoutButton = document.getElementById("logout-button");

    openSidebarButton = document.getElementById("open-sidebar-button");
    closeSidebarButton = document.getElementById("close-sidebar-button");
    sidebar = document.getElementById("sidebar");
    
/* ==============================================
   MOBILE SIDEBAR SUPPORT
============================================== */

function closeMobileSidebar() {
    if (sidebar) {
        sidebar.classList.remove("open");
    }

    document.body.classList.remove("mobile-sidebar-open");

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

    document.body.classList.add("mobile-sidebar-open");

    if (openSidebarButton) {
        openSidebarButton.setAttribute(
            "aria-expanded",
            "true"
        );
    }
}

/* Keep overlay state synchronized with sidebar state */
if (openSidebarButton) {
    openSidebarButton.addEventListener("click", function () {
        if (sidebar && sidebar.classList.contains("open")) {
            closeMobileSidebar();
        } else {
            openMobileSidebar();
        }
    });
}

if (closeSidebarButton) {
    closeSidebarButton.addEventListener("click", function () {
        closeMobileSidebar();
    });
}

/* Tap outside the sidebar to close it */
document.addEventListener("click", function (event) {
    if (
        !sidebar ||
        !sidebar.classList.contains("open") ||
        window.innerWidth > 768
    ) {
        return;
    }

    const clickedSidebar = sidebar.contains(event.target);
    const clickedToggle =
        openSidebarButton &&
        openSidebarButton.contains(event.target);

    if (!clickedSidebar && !clickedToggle) {
        closeMobileSidebar();
    }
});

/* Close sidebar with Escape */
document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        closeMobileSidebar();
    }
});

/* Reset drawer state when switching back to desktop */
window.addEventListener("resize", function () {
    if (window.innerWidth > 768) {
        closeMobileSidebar();
    }
});


    // Verify essential HTML elements.
    if (!chatBox) {
        console.error("Missing HTML element: #chat-box");
    }

    if (!userInput) {
        console.error("Missing HTML element: #user-input");
    }

    if (!sendButton) {
        console.error("Missing HTML element: #send-button");
    }

    if (!getAuthToken()) {
        window.location.href = "/login";
        return;
    }

    updateAccountUI();

    // Send button.
    if (sendButton) {
        sendButton.addEventListener("click", function (event) {
            event.preventDefault();
            sendMessage();
        });
    }

    // Enter sends; Shift + Enter inserts a new line.
    if (userInput) {
        userInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    }

    // New Chat menu.
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

    // Clear Chat button: matches id="clear-chat-button".
    if (clearChatButton) {
        clearChatButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            clearCurrentMessages();
        });
    }

    // Compatibility with older HTML.
    if (clearMessagesButton && clearMessagesButton !== clearChatButton) {
        clearMessagesButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            clearCurrentMessages();
        });
    }

    // Clear Conversation Memory button.
    if (clearMemoryButton) {
        clearMemoryButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            clearConversationMemory();
        });
    }

    // Start Fresh.
    if (startFreshButton) {
        startFreshButton.addEventListener("click", function (event) {
            event.preventDefault();
            newChat();
        });
    }

    // Account menu.
    if (accountButton) {
        accountButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            if (accountMenu) {
                accountMenu.classList.toggle("hidden");
            }
        });
    }

    // Switch account.
    if (switchAccountButton) {
        switchAccountButton.addEventListener("click", function (event) {
            event.preventDefault();
            loginWithAnotherAccount();
        });
    }

    // Logout.
    if (logoutButton) {
        logoutButton.addEventListener("click", function (event) {
            event.preventDefault();
            logout();
        });
    }

    // Close menus when clicking outside them.
    document.addEventListener("click", function (event) {
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

    // Mobile sidebar controls.
    if (openSidebarButton) {
        openSidebarButton.addEventListener("click", function (event) {
            event.preventDefault();

            if (sidebar) {
                sidebar.classList.add("open");
            }
        });
    }

    if (closeSidebarButton) {
        closeSidebarButton.addEventListener("click", function (event) {
            event.preventDefault();

            if (sidebar) {
                sidebar.classList.remove("open");
            }
        });
    }

    // Load saved conversations.
    loadRecentChats();

    if (userInput) {
        userInput.focus();
    }

    console.log("INGRES AI Assistant initialization complete.");
});