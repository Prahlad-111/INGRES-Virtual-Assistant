// ==================================================
// ELEMENTS
// ==================================================

const chatBox =
    document.getElementById("chat-box");

const userInput =
    document.getElementById("user-input");

const sendButton =
    document.getElementById("send-button");

const typingIndicator =
    document.getElementById("typing");

const newChatButton =
    document.getElementById("new-chat-button");

const newChatMenu =
    document.getElementById("new-chat-menu");

const clearMessagesButton =
    document.getElementById("clear-messages-button");

const clearMemoryButton =
    document.getElementById("clear-memory-button");

const startFreshButton =
    document.getElementById("start-fresh-button");

const recentChatList =
    document.getElementById("recent-chat-list");

const sidebar =
    document.getElementById("sidebar");

const openSidebarButton =
    document.getElementById("open-sidebar-button");

const closeSidebarButton =
    document.getElementById("close-sidebar-button");


// ==================================================
// STORAGE
// ==================================================

const STORAGE_KEY =
    "ingres_ai_chat_history";


// ==================================================
// CONVERSATION MEMORY
// ==================================================

let conversationHistory = [];

let currentChatId = null;


// ==================================================
// LOAD SAVED CHATS
// ==================================================

let savedChats = loadChats();


// ==================================================
// LOAD CHATS
// ==================================================

function loadChats() {

    try {

        const stored =
            localStorage.getItem(
                STORAGE_KEY
            );


        if (!stored) {

            return [];

        }


        const chats =
            JSON.parse(stored);


        if (!Array.isArray(chats)) {

            return [];

        }


        return chats;

    }

    catch (error) {

        console.error(
            "Could not load chat history:",
            error
        );

        return [];

    }

}


// ==================================================
// SAVE CHATS
// ==================================================

function saveChats() {

    try {

        localStorage.setItem(

            STORAGE_KEY,

            JSON.stringify(
                savedChats
            )

        );

    }

    catch (error) {

        console.error(
            "Could not save chat history:",
            error
        );

    }

}


// ==================================================
// GENERATE CHAT ID
// ==================================================

function generateChatId() {

    return (

        Date.now().toString() +

        Math.random()
            .toString(36)
            .substring(2, 9)

    );

}


// ==================================================
// FORMAT DATE
// ==================================================

function formatChatTime(
    timestamp
) {

    const date =
        new Date(timestamp);

    const now =
        new Date();


    const today =
        now.toDateString()
        === date.toDateString();


    if (today) {

        return date.toLocaleTimeString(

            [],

            {

                hour: "2-digit",

                minute: "2-digit"

            }

        );

    }


    return date.toLocaleDateString(

        [],

        {

            day: "2-digit",

            month: "short"

        }

    );

}


// ==================================================
// CREATE CHAT TITLE
// ==================================================

function createChatTitle(
    message
) {

    if (!message) {

        return "New Conversation";

    }


    let title =
        message.trim();


    if (title.length > 35) {

        title =
            title.substring(
                0,
                35
            )
            + "...";

    }


    return title;

}


// ==================================================
// CREATE NEW CHAT
// ==================================================

function createChat(
    message
) {

    const chat = {

        id:
            generateChatId(),

        title:
            createChatTitle(
                message
            ),

        createdAt:
            Date.now(),

        updatedAt:
            Date.now(),

        messages:
            []

    };


    savedChats.unshift(
        chat
    );


    currentChatId =
        chat.id;


    saveChats();

    renderRecentChats();


    return chat;

}


// ==================================================
// GET CURRENT CHAT
// ==================================================

function getCurrentChat() {

    return savedChats.find(

        function(chat) {

            return (
                chat.id ===
                currentChatId
            );

        }

    );

}


// ==================================================
// SAVE CURRENT CONVERSATION
// ==================================================

function saveCurrentConversation() {

    if (!currentChatId) {

        return;

    }


    const chat =
        getCurrentChat();


    if (!chat) {

        return;

    }


    chat.messages =
        conversationHistory.map(

            function(item) {

                return {

                    role:
                        item.role,

                    message:
                        item.message

                };

            }

        );


    chat.updatedAt =
        Date.now();


    savedChats.sort(

        function(a, b) {

            return (
                b.updatedAt -
                a.updatedAt
            );

        }

    );


    saveChats();

    renderRecentChats();

}


// ==================================================
// MARKDOWN FORMATTER
// ==================================================

function formatBotMessage(
    message
) {

    let html =
        String(message);


    html = html
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        );


    // Code blocks

    html = html.replace(

        /```(?:[a-zA-Z0-9_+-]+)?\s*([\s\S]*?)```/g,

        function(
            match,
            code
        ) {

            return `
                <pre class="code-block"><code>${code.trim()}</code></pre>
            `;

        }

    );


    // Inline code

    html = html.replace(

        /`([^`]+)`/g,

        "<code>$1</code>"

    );


    // Bold

    html = html.replace(

        /\*\*(.*?)\*\*/g,

        "<strong>$1</strong>"

    );


    // Italic

    html = html.replace(

        /(?<!\*)\*([^*\n]+)\*(?!\*)/g,

        "<em>$1</em>"

    );


    // Headings

    html = html.replace(

        /^### (.*)$/gm,

        "<h4>$1</h4>"

    );


    html = html.replace(

        /^## (.*)$/gm,

        "<h3>$1</h3>"

    );


    html = html.replace(

        /^# (.*)$/gm,

        "<h2>$1</h2>"

    );


    // Bullets

    html = html.replace(

        /^\s*[-•]\s+(.*)$/gm,

        "<li>$1</li>"

    );


    // Numbered lists

    html = html.replace(

        /^\s*\d+\.\s+(.*)$/gm,

        "<li>$1</li>"

    );


    // Horizontal line

    html = html.replace(

        /^\s*---+\s*$/gm,

        "<hr>"

    );


    // New lines

    html = html.replace(

        /\n/g,

        "<br>"

    );


    return html;

}


// ==================================================
// ADD MESSAGE
// ==================================================

function addMessage(
    message,
    sender
) {

    const messageDiv =
        document.createElement(
            "div"
        );


    messageDiv.classList.add(
        "message"
    );


    if (
        sender === "user"
    ) {

        messageDiv.classList.add(
            "user-message"
        );

    }

    else {

        messageDiv.classList.add(
            "bot-message"
        );

    }


    const icon =
        document.createElement(
            "div"
        );


    icon.classList.add(
        "message-icon"
    );


    icon.textContent =
        sender === "user"
            ? "👤"
            : "🤖";


    const content =
        document.createElement(
            "div"
        );


    content.classList.add(
        "message-content"
    );


    const name =
        document.createElement(
            "div"
        );


    name.classList.add(
        "message-name"
    );


    name.textContent =
        sender === "user"
            ? "You"
            : "INGRES Assistant";


    const text =
        document.createElement(
            "div"
        );


    text.classList.add(
        "message-text"
    );


    if (
        sender === "bot"
    ) {

        text.innerHTML =
            formatBotMessage(
                message
            );

    }

    else {

        text.textContent =
            message;

    }


    content.appendChild(
        name
    );

    content.appendChild(
        text
    );


    messageDiv.appendChild(
        icon
    );

    messageDiv.appendChild(
        content
    );


    chatBox.appendChild(
        messageDiv
    );


    setTimeout(

        function() {

            chatBox.scrollTop =
                chatBox.scrollHeight;

        },

        30

    );

}


// ==================================================
// TYPING
// ==================================================

function showTyping() {

    typingIndicator.classList.remove(
        "hidden"
    );


    chatBox.scrollTop =
        chatBox.scrollHeight;

}


function hideTyping() {

    typingIndicator.classList.add(
        "hidden"
    );

}


// ==================================================
// RENDER RECENT CHATS
// ==================================================

function renderRecentChats() {

    recentChatList.innerHTML =
        "";


    if (
        savedChats.length === 0
    ) {

        const empty =
            document.createElement(
                "div"
            );


        empty.className =
            "empty-history";


        empty.textContent =
            "No recent chats yet.";


        recentChatList.appendChild(
            empty
        );


        return;

    }


    savedChats.forEach(

        function(chat) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "recent-chat-item";


            if (
                chat.id ===
                currentChatId
            ) {

                item.classList.add(
                    "active"
                );

            }


            const icon =
                document.createElement(
                    "span"
                );


            icon.className =
                "recent-chat-icon";


            icon.textContent =
                "💬";


            const content =
                document.createElement(
                    "div"
                );


            content.className =
                "recent-chat-content";


            const title =
                document.createElement(
                    "div"
                );


            title.className =
                "recent-chat-title";


            title.textContent =
                chat.title;


            const time =
                document.createElement(
                    "div"
                );


            time.className =
                "recent-chat-time";


            time.textContent =
                formatChatTime(
                    chat.updatedAt
                );


            content.appendChild(
                title
            );

            content.appendChild(
                time
            );


            const deleteButton =
                document.createElement(
                    "button"
                );


            deleteButton.className =
                "delete-chat-button";


            deleteButton.type =
                "button";


            deleteButton.textContent =
                "🗑";


            deleteButton.title =
                "Delete chat";


            deleteButton.addEventListener(

                "click",

                function(event) {

                    event.stopPropagation();

                    deleteChat(
                        chat.id
                    );

                }

            );


            item.addEventListener(

                "click",

                function() {

                    loadChat(
                        chat.id
                    );

                }

            );


            item.appendChild(
                icon
            );

            item.appendChild(
                content
            );

            item.appendChild(
                deleteButton
            );


            recentChatList.appendChild(
                item
            );

        }

    );

}


// ==================================================
// LOAD CHAT
// ==================================================

function loadChat(
    chatId
) {

    const chat =
        savedChats.find(

            function(item) {

                return (
                    item.id ===
                    chatId
                );

            }

        );


    if (!chat) {

        return;

    }


    currentChatId =
        chat.id;


    conversationHistory =
        Array.isArray(
            chat.messages
        )

            ? chat.messages.map(

                function(item) {

                    return {

                        role:
                            item.role,

                        message:
                            item.message

                    };

                }

            )

            : [];


    chatBox.innerHTML =
        "";


    conversationHistory.forEach(

        function(item) {

            addMessage(

                item.message,

                item.role === "user"
                    ? "user"
                    : "bot"

            );

        }

    );


    if (
        conversationHistory.length === 0
    ) {

        showWelcomeMessage();

    }


    renderRecentChats();

    closeSidebar();

    userInput.focus();

}


// ==================================================
// DELETE CHAT
// ==================================================

function deleteChat(
    chatId
) {

    const confirmed =
        confirm(
            "Delete this conversation?"
        );


    if (!confirmed) {

        return;

    }


    savedChats =
        savedChats.filter(

            function(chat) {

                return (
                    chat.id !==
                    chatId
                );

            }

        );


    saveChats();


    if (
        currentChatId ===
        chatId
    ) {

        currentChatId =
            null;

        conversationHistory =
            [];

        chatBox.innerHTML =
            "";

        showWelcomeMessage();

    }


    renderRecentChats();

}


// ==================================================
// WELCOME
// ==================================================

function showWelcomeMessage() {

    addMessage(

        "Hello! 👋\n\n" +

        "Welcome to the INGRES AI Virtual Assistant.\n\n" +

        "I can help you with INGRES, groundwater, " +

        "programming, education, calculations, " +

        "technical problems, and general questions.\n\n" +

        "How can I help you today?",

        "bot"

    );

}


// ==================================================
// ENSURE CURRENT CHAT
// ==================================================

function ensureCurrentChat(
    message
) {

    if (
        currentChatId
    ) {

        return;

    }


    createChat(
        message
    );

}


// ==================================================
// SEND MESSAGE
// ==================================================

async function sendMessage() {

    const message =
        userInput.value.trim();


    if (!message) {

        return;

    }


    ensureCurrentChat(
        message
    );


    addMessage(
        message,
        "user"
    );


    conversationHistory.push({

        role:
            "user",

        message:
            message

    });


    saveCurrentConversation();


    userInput.value =
        "";


    sendButton.disabled =
        true;


    showTyping();


    try {

        const response =
            await fetch(

                "/api/chat",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            message:
                                message,

                            conversation_history:
                                conversationHistory.slice(
                                    -10
                                )

                        })

                }

            );


        const data =
            await response.json();


        hideTyping();


        if (
            data.success
        ) {

            addMessage(

                data.response,

                "bot"

            );


            conversationHistory.push({

                role:
                    "assistant",

                message:
                    data.response

            });


            conversationHistory =
                conversationHistory.slice(
                    -10
                );


            saveCurrentConversation();

        }

        else {

            addMessage(

                data.message ||
                "Something went wrong.",

                "bot"

            );

        }


    }

    catch (error) {

        console.error(
            "Chat error:",
            error
        );


        hideTyping();


        addMessage(

            "Unable to connect to the chatbot server.",

            "bot"

        );

    }


    sendButton.disabled =
        false;


    userInput.focus();

}


// ==================================================
// CLEAR MESSAGES
// ==================================================

function clearMessages() {

    chatBox.innerHTML =
        "";


    showWelcomeMessage();


    newChatMenu.classList.add(
        "hidden"
    );


    userInput.focus();

}


// ==================================================
// CLEAR CONVERSATION MEMORY
// ==================================================

function clearConversationMemory() {

    conversationHistory =
        [];


    newChatMenu.classList.add(
        "hidden"
    );


    userInput.focus();

}


// ==================================================
// START FRESH
// ==================================================

function startFresh() {

    const confirmed =
        confirm(

            "Start a new conversation?\n\n" +

            "Your current conversation will be saved " +

            "in Recent Chats."

        );


    if (!confirmed) {

        return;

    }


    if (
        conversationHistory.length > 0
    ) {

        saveCurrentConversation();

    }


    currentChatId =
        null;


    conversationHistory =
        [];


    chatBox.innerHTML =
        "";


    showWelcomeMessage();


    newChatMenu.classList.add(
        "hidden"
    );


    renderRecentChats();


    userInput.value =
        "";


    userInput.focus();

}


// ==================================================
// NEW CHAT MENU
// ==================================================

newChatButton.addEventListener(

    "click",

    function(event) {

        event.stopPropagation();

        newChatMenu.classList.toggle(
            "hidden"
        );

    }

);


// ==================================================
// CLEAR MESSAGES
// ==================================================

clearMessagesButton.addEventListener(

    "click",

    function() {

        clearMessages();

    }

);


// ==================================================
// CLEAR MEMORY
// ==================================================

clearMemoryButton.addEventListener(

    "click",

    function() {

        clearConversationMemory();

    }

);


// ==================================================
// START FRESH
// ==================================================

startFreshButton.addEventListener(

    "click",

    function() {

        startFresh();

    }

);


// ==================================================
// CLOSE MENU OUTSIDE
// ==================================================

document.addEventListener(

    "click",

    function(event) {

        if (
            !event.target.closest(
                ".new-chat-wrapper"
            )
        ) {

            newChatMenu.classList.add(
                "hidden"
            );

        }

    }

);


// ==================================================
// OPEN SIDEBAR - MOBILE
// ==================================================

openSidebarButton.addEventListener(

    "click",

    function() {

        sidebar.classList.add(
            "open"
        );

    }

);


// ==================================================
// CLOSE SIDEBAR - MOBILE
// ==================================================

closeSidebarButton.addEventListener(

    "click",

    function() {

        closeSidebar();

    }

);


function closeSidebar() {

    sidebar.classList.remove(
        "open"
    );

}


// ==================================================
// ENTER KEY
// ==================================================

userInput.addEventListener(

    "keydown",

    function(event) {

        if (
            event.key === "Enter"
        ) {

            event.preventDefault();

            sendMessage();

        }

    }

);


// ==================================================
// INITIALIZE
// ==================================================

renderRecentChats();

userInput.focus();