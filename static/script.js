const summonHermesBtn = document.getElementById("summonHermesBtn");
const chatbotContainer = document.querySelector('.chatbot');
const firstChatMessage = document.querySelector('.chatbox li:first-child');
const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");
const userIconPath = '/static/assets/user-icon.svg';
const botIconPath = '/static/assets/bot-icon.png';
const threadListContainer = document.getElementById('thread-list-container');
const threadDropdownIcon = document.getElementById('thread-dropdown-icon');
const promptsContainer = document.getElementById('prompt-suggestions');



let selectedThread = null;
let threads = [];
let messages = []; 
let resultsLimit = 10;
let userMessage = null; // Variable to store user's message
let currentThreadId = null; // Variable to store the current thread ID
const inputInitHeight = chatInput.scrollHeight;

// Array of prompt suggestions
const prompts = ["Please help me understand a Bill of Lading", "How do I set up a shipping relationship with factories in China?", "Are there any trade events near Baltimore?", "Can you find me an ITA office in Germany?"];

// Function to add prompts to the UI
function populatePrompts() {
    const promptsContainer = document.getElementById('prompt-suggestions');
    promptsContainer.innerHTML = ''; // Clear existing prompts to avoid duplication
    prompts.forEach(prompt => {
        const promptElement = document.createElement('button');
        promptElement.innerText = prompt;
        promptElement.classList.add('prompt-button');
        promptElement.addEventListener('click', () => {
            chatInput.value = prompt;
            handleChat();
            promptsContainer.style.opacity = '0'; // Set the opacity to 0
            promptsContainer.style.pointerEvents = 'none'; // Disable pointer events
        });
        promptsContainer.appendChild(promptElement);
    });
}

// Call this function when the chatbot is initialized
document.addEventListener('DOMContentLoaded', populatePrompts);

// Initially hide the first chat message
firstChatMessage.style.display = 'none';

summonHermesBtn.addEventListener("click", () => {
    // Show the first chat message and start the conversation
    firstChatMessage.style.display = 'flex';

    // Hide the Summon button and remove blur from the chat container
    summonHermesBtn.style.display = 'none';
    landingPageContent.style.display = 'none';
    landingPage.style.display = 'none';
    document.body.classList.add("show-chatbot"); // Additional class to manage visibility

    // Populate prompt suggestions here
    populatePrompts();

    startConversation();
});

const createChatLi = (message, className, isMarkdown = false) => {
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);

    let iconHTML;
    if (className === "outgoing") {
        iconHTML = `<img src="${userIconPath}" alt="User Icon" class="user-icon">`;
    } else {
        iconHTML = `<div class="botIcon"><img src="${botIconPath}" alt="Bot Icon"></div>`;
    }

    let chatContent = `${iconHTML}<div class="botMessage"><p>${message}</p></div>`;
    chatLi.innerHTML = chatContent;

    // Parse Markdown if required
    if (isMarkdown && className === "incoming") {
        const pElement = chatLi.querySelector("p");
        pElement.innerHTML = marked.parse(message);

        // Ensure all links open in a new tab
        const anchors = pElement.querySelectorAll('a');
        anchors.forEach(anchor => {
            anchor.setAttribute('target', '_blank');
            anchor.setAttribute('rel', 'noopener noreferrer'); // For security
        });
    }

    return chatLi;
};
    
    
    let statusMessages = {};  // Object to store status messages for each thread
    
    const startConversation = () => {
        console.log("Starting conversation...");
        fetchThreads(resultsLimit);
        return fetch("https://projecthermes.replit.app/start", {
            method: "GET"
        })
        .then(res => res.json())
        .then(data => {
            currentThreadId = data.thread_id;
            statusMessages[currentThreadId] = "Initializing...";  // Initialize status message for new thread
            console.log("Conversation started with Thread ID:", currentThreadId);
        })
        .catch(error => {
            console.error("Error starting conversation:", error);
        });
    };
    
let retryCount = 0; // Variable to track the number of retries

    const generateResponse = (chatElement) => {
        if (!currentThreadId) {
            console.error("No active thread. Cannot send message.");
            return;
        }
    
        console.log("Generating response for message:", userMessage);
        const API_URL = "https://projecthermes.replit.app/chat";
        const STATUS_URL = `https://projecthermes.replit.app/status/${currentThreadId}`;
    
        let statusPolling = setInterval(() => {
            fetch(STATUS_URL)
            .then(res => res.json())
            .then(data => {
                if (data && data.statusMessage) {
                    updateStatusMessage(chatElement, data.statusMessage);
                }
            })
            .catch(error => {
                console.error("Error fetching status:", error);
            });
        }, 500); // Poll every 2 seconds
    
        fetch(API_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ thread_id: currentThreadId, message: userMessage })
        })
        .then(res => res.json())
        .then(data => {
            clearInterval(statusPolling);
            if (chatElement && chatElement.parentNode) {
                chatbox.removeChild(chatElement);
            }
            const incomingMessage = createChatLi(data.response.trim(), "incoming", true);
            chatbox.appendChild(incomingMessage);
            retryCount = 0; // Reset retry count after a successful response
        })
        .catch(error => {
            clearInterval(statusPolling);
            if (retryCount < 1) { // Retry once if an error occurs
                retryCount++;
                console.log("An error occurred, trying again...");
                const retryMessage = createChatLi("Let me try that again...", "incoming");
                chatbox.appendChild(retryMessage);
                setTimeout(() => {
                    generateResponse(retryMessage);
                }, 1000);
            } else {
                // Show error message if retries are exhausted
                if (chatElement && chatElement.parentNode) {
                    updateElementWithError(chatElement, `Oops! Something went wrong: ${error.message}`);
                }
                console.error("Chat error:", error);
                retryCount = 0; // Reset retry count after handling error
            }
        })
        .finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
    };
        
    
    const createErrorDropdown = (errorMessage) => {
        const errorLi = document.createElement("li");
        errorLi.classList.add("chat", "incoming", "error-dropdown");
        errorLi.innerHTML = `
            <span class="material-symbols-outlined">H</span>
            <div class="error-message">
                <p>An error occurred <span class="dropdown-arrow">▼</span></p>
                <div class="error-details">${errorMessage}</div>
            </div>
        `;
        return errorLi;
    };
    
    function displayNextStatus(chatElement) {
        if (statusQueue.length > 0) {
            const nextStatus = statusQueue.shift();
            updateStatusMessage(chatElement, nextStatus);
            isDisplayingStatus = true;
    
            setTimeout(() => {
                isDisplayingStatus = false;
                if (statusQueue.length > 0) {
                    displayNextStatus(chatElement); // Display the next message if queue is not empty
                }
            }, MIN_STATUS_DISPLAY_TIME);
        }
    }
    
    function updateStatusMessage(chatElement, message) {
        const paragraph = chatElement.querySelector("p");
        if (paragraph) {
            paragraph.textContent = message;
        }
    }

    function updateElementWithError(element, errorMessage) {
        element.innerHTML = `
            <div class="error-message">
                <p>An error occurred <span class="dropdown-arrow">▼</span></p>
                <div class="error-details">${errorMessage}</div>
            </div>
        `;
        element.classList.add("error-dropdown");
    }
    
    
    const handleChat = () => {
        userMessage = chatInput.value.trim();
        if (!userMessage) {
            console.log("Empty message, not sending.");
            return;
        }
    
        // Directly hide prompt suggestions when a message is sent
        const promptsContainer = document.getElementById('prompt-suggestions');
        promptsContainer.style.opacity = '0'; // Set the opacity to 0
        promptsContainer.style.pointerEvents = 'none'; // Disable pointer events
    
        chatInput.value = "";
        chatInput.style.height = `${inputInitHeight}px`;
        const outgoingChatLi = createChatLi(userMessage, "outgoing");
        chatbox.appendChild(outgoingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);
    
        if (!currentThreadId) {
            startConversation().then(() => {
                const incomingChatLi = createChatLi("Working...", "incoming");
                chatbox.appendChild(incomingChatLi);
                chatbox.scrollTo(0, chatbox.scrollHeight);
                generateResponse(incomingChatLi);
            });
        } else {
            const incomingChatLi = createChatLi("Working...", "incoming");
            chatbox.appendChild(incomingChatLi);
            chatbox.scrollTo(0, chatbox.scrollHeight);
            generateResponse(incomingChatLi);
        }
    };
    const API_BASE_URL = 'https://projecthermes.replit.app';

    const renderThreads = (threads) => {
        threadListContainer.innerHTML = ''; // Clear existing threads
    
        // Helper function to format the date
        const formatDate = (dateString) => {
            // Parse the date in UTC and then convert it to the local time zone
            const date = new Date(dateString);
            const localDate = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds());

            return localDate.toLocaleDateString();
        };
    
        // Helper function to determine the date category
        const getDateCategory = (dateString) => {
            // Parse the date as UTC
            const date = new Date(dateString);

            // Get the current date and time in the user's local time zone
            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const yesterday = new Date(today);
            yesterday.setDate(today.getDate() - 1);

            // Convert the UTC date to the user's local time zone
            const localDate = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());

            // Determine the date category
            if (localDate >= today) {
                return 'Today';
            } else if (localDate >= yesterday && localDate < today) {
                return 'Yesterday';
            } else {
                // Additional date categorizations as needed
                return 'Older';
            }
        };
    
        let lastCategory = '';
    
        threads.forEach(thread => {
            const threadCategory = getDateCategory(thread.updated_at);
    
            if (threadCategory !== lastCategory) {
                const categoryDiv = document.createElement('div');
                categoryDiv.classList.add('thread-category');
                categoryDiv.textContent = threadCategory;
                threadListContainer.appendChild(categoryDiv);
                lastCategory = threadCategory;
            }
    
            const threadDiv = document.createElement('div');
            threadDiv.classList.add('thread-item');
    
            const titleDiv = document.createElement('div');
            titleDiv.classList.add('thread-title');
            titleDiv.textContent = thread.title || 'Untitled Thread';
    
            threadDiv.appendChild(titleDiv);
            
    
            threadDiv.onclick = () => handleThreadClick(thread.thread_id);
            threadListContainer.appendChild(threadDiv);
        });
    };

    const handleThreadClick = async (threadId) => {
        // Update the currentThreadId
        currentThreadId = threadId;
        console.log(`Thread selected: ${currentThreadId}`);
    
        // Fetch and render messages from the selected thread
        messages = await fetchMessagesFromAPI(threadId);
        const container = document.getElementById('thread-list-container');
        container.classList.remove('active');
        
            promptsContainer.style.opacity = '0'; // Set the opacity to 0
            promptsContainer.style.pointerEvents = 'none';
        // This will hide the dropd
        renderMessages(messages);
    };
    

    const renderMessages = (messages) => {
        chatbox.innerHTML = ''; // Clear existing messages
    
        messages.forEach(message => {
            const messageClass = (message.role === 'user') ? 'outgoing' : 'incoming';
            const messageLi = createChatLi(message.content, messageClass, true); // Assuming createChatLi handles the Markdown parsing
            chatbox.appendChild(messageLi);
        });
    
        chatbox.scrollTo(0, chatbox.scrollHeight);
    };
    


    const fetchThreadsFromAPI = async (startDate, endDate, limit = 10) => {
        try {
            const params = new URLSearchParams();
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            params.append('limit', limit);
    
            const response = await fetch(`${API_BASE_URL}/threads?${params.toString()}`);
            const data = await response.json();
            return data; // Array of thread objects
        } catch (error) {
            console.error('Error fetching threads', error);
            return ["Ive encountered and error with threads"]; // Return an empty array in case of error
        }
    };
    
    const fetchMessagesFromAPI = async (threadId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/messages/${threadId}`);
            const data = await response.json();
            return data; // Array of message objects
        } catch (error) {
            console.error('Error fetching messages', error);
            return ["Ive encountered an error with messages"]; // Return an empty array in case of error
        }
    };

    const fetchThreads = async (limit) => {
        // Fetch threads for the last 7 days including today
        const today = new Date();
        const startDate = new Date();
        startDate.setDate(today.getDate() - 7);

        // Adjust endDate to the end of the current day in local time zone
        const endDate = new Date(today);
        endDate.setHours(23, 59, 59, 999); // Set to last millisecond of the day

        threads = await fetchThreadsFromAPI(startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0], limit);
        renderThreads(threads);
    };
    // Function to populate the threads dropdown
    const populateThreadsDropdown = (threads) => {
        const container = document.getElementById('thread-list-container');
        container.innerHTML = ''; // Clear previous threads
        threads.forEach(thread => {
            const threadDiv = document.createElement('div');
            threadDiv.classList.add('thread-item');
            threadDiv.textContent = `Thread from ${thread.updated_at}`; // Adjust based on your thread data
            threadDiv.onclick = () => handleThreadSelection(thread.thread_id);
            container.appendChild(threadDiv);
        });
    };
    
    // Function to handle thread selection
  
        
    // ... [rest of your JavaScript code, such as event listeners and other functions] ...
    
    
    chatInput.addEventListener("input", () => {
        chatInput.style.height = `${inputInitHeight}px`;
        chatInput.style.height = `${chatInput.scrollHeight}px`;
    });
    
    
    document.addEventListener("click", (e) => {
        if (e.target && e.target.classList.contains("dropdown-arrow")) {
            const errorDetails = e.target.parentElement.nextElementSibling;
            errorDetails.style.display = errorDetails.style.display === 'block' ? 'none' : 'block';
            e.target.textContent = errorDetails.style.display === 'block' ? '▲' : '▼';
        }
    });
    
    
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
            e.preventDefault();
            handleChat();
        }
    });
    
    sendChatBtn.addEventListener("click", handleChat);
    
    chatbotToggler.addEventListener("click", () => {
        document.body.classList.toggle("show-chatbot");
        chatbotContainer.classList.toggle("is-blurred");
        if (!currentThreadId) {
            console.log("No current thread ID, starting a new conversation.");
            startConversation();
        }
    });
    
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            document.body.classList.remove("show-chatbot");
            chatbotContainer.classList.add("is-blurred");
            summonHermesBtn.style.display = 'block';
        });
    }
    

    document.getElementById('thread-dropdown-icon').addEventListener('click', () => {
        const container = document.getElementById('thread-list-container');
        container.classList.toggle('active');
        if (container.classList.contains('active')) {
            fetchThreads(); // Fetch and populate threads if the container is active
        }
    });