// Extracted and cleaned JS from index.html
// All DOMContentLoaded and event listeners are wrapped for safety

document.addEventListener('DOMContentLoaded', function() {
    // Chat History Management
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
    let currentChatId = null;
    let currentMessages = [];
    let adobeDCView = null;
    let currentPDFUrl = null;


    function initializeChatHistory() {
        const chatHistoryContainer = document.getElementById('chatHistory');
        chatHistoryContainer.innerHTML = '';

        if (chatHistory.length === 0) {
            chatHistoryContainer.innerHTML = '<p style="opacity: 0.6; text-align: center; padding: 1rem;">No chat history yet</p>';
            return;
        }

        chatHistory.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-history-item';
            chatItem.innerHTML = `
                <div>
                    <div class="chat-history-title">${chat.title}</div>
                    <div class="chat-history-date">${formatDate(chat.timestamp)}</div>
                </div>
            `;
            chatItem.addEventListener('click', () => loadChat(chat.id));
            chatHistoryContainer.appendChild(chatItem);
        });
    }

    function formatDate(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    function saveChat() {
        if (currentMessages.length === 0) return;
        const chatTitle = generateChatTitle(currentMessages);
        const newChat = {
            id: Date.now(),
            title: chatTitle,
            messages: [...currentMessages],
            timestamp: new Date().toISOString()
        };
        chatHistory.unshift(newChat);
        if (chatHistory.length > 10) {
            chatHistory = chatHistory.slice(0, 10);
        }
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        initializeChatHistory();
    }

    function generateChatTitle(messages) {
        const firstUserMessage = messages.find(msg => msg.isUser);
        if (firstUserMessage) {
            const text = firstUserMessage.text.substring(0, 30);
            return text.length === 30 ? text + '...' : text;
        }
        return 'New Chat';
    }

    function loadChat(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (!chat) return;
        currentChatId = chatId;
        currentMessages = [...chat.messages];
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        currentMessages.forEach(msg => {
            addMessageToUI(msg.text, msg.isUser, false);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
        showToast(`Loaded: ${chat.title}`);
    }

    function addMessageToUI(text, isUser, animate = true) {
        const chatMessages = document.getElementById('chatMessages');
        const message = document.createElement('div');
        message.className = 'message' + (isUser ? ' user' : '');
        if (!animate) {
            message.style.animation = 'none';
        }
        message.innerHTML = `
            <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
            <div class="message-content">${text}</div>
        `;
        chatMessages.appendChild(message);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function startNewChat() {
        if (currentMessages.length > 0) {
            saveChat();
        }
        currentChatId = null;
        currentMessages = [];
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        addMessageToUI("Hello! I'm your AI Assistant. I can help you with PDF conversions, document management, and answer any questions you have. How can I assist you today?", false, false);
        showToast('New chat started');
    }

    document.getElementById('newChatBtn').addEventListener('click', startNewChat);

    // PDF Converter Functionality
    const dropZonePanel = document.getElementById('dropZonePanel');
    const fileInputPanel = document.getElementById('fileInputPanel');
    const analyzeBtnPanel = document.getElementById('analyzeBtnPanel');
    const personaInput = document.getElementById('personaInput');
    const jobInput = document.getElementById('jobInput');
    const progressContainerPanel = document.getElementById('progressContainerPanel');
    const progressFillPanel = document.getElementById('progressFillPanel');
    const progressTextPanel = document.getElementById('progressTextPanel');
    const fileListPanel = document.getElementById('fileListPanel');
    const fileItemsPanel = document.getElementById('fileItemsPanel');
    const status = document.getElementById('status');
    const pdfSelector = document.getElementById('pdfSelector');
    const pdfPanel = document.getElementById('pdfPanel');
    const closePanel = document.getElementById('closePanel');
    let panelSelectedFiles = [];

    function showToast(message) {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        toastMessage.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 2500);
    }

    function updatePanelAnalyzeButton() {
        if (panelSelectedFiles.length === 0) {
            analyzeBtnPanel.disabled = true;
        } else {
            analyzeBtnPanel.disabled = false;
        }
    }

    pdfSelector.addEventListener('click', () => {
        pdfPanel.classList.toggle('show');
        pdfSelector.classList.toggle('active');
    });
    closePanel.addEventListener('click', () => {
        pdfPanel.classList.remove('show');
        pdfSelector.classList.remove('active');
    });
    dropZonePanel.addEventListener('click', () => fileInputPanel.click());
    dropZonePanel.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZonePanel.classList.add('drag-over');
    });
    dropZonePanel.addEventListener('dragleave', () => {
        dropZonePanel.classList.remove('drag-over');
    });
    dropZonePanel.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZonePanel.classList.remove('drag-over');
        handlePanelFiles(e.dataTransfer.files);
    });
    fileInputPanel.addEventListener('change', (e) => {
        handlePanelFiles(e.target.files);
    });

    function handlePanelFiles(files) {
        panelSelectedFiles = Array.from(files);
        updatePanelFileList();
        updatePanelAnalyzeButton();
        showToast(`${files.length} file(s) selected`);
    }

    function updatePanelFileList() {
        if (panelSelectedFiles.length === 0) {
            fileListPanel.style.display = 'none';
            return;
        }
        fileListPanel.style.display = 'block';
        fileItemsPanel.innerHTML = '';
        panelSelectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-info">
                    <span class="file-icon">📄</span>
                    <span class="file-name">${file.name}</span>
                </div>
                <button class="remove-file-btn" data-index="${index}">×</button>
            `;
            fileItem.querySelector('.remove-file-btn').addEventListener('click', () => {
                removePanelFile(index);
            });
            fileItemsPanel.appendChild(fileItem);
        });
    }

    function removePanelFile(index) {
        panelSelectedFiles.splice(index, 1);
        updatePanelFileList();
        updatePanelAnalyzeButton();
    }

    analyzeBtnPanel.addEventListener('click', async () => {

        if (panelSelectedFiles.length === 0) {
            showToast('Please select at least one PDF.');
            return;
        }
        const persona = personaInput.value.trim();
        const job = jobInput.value.trim();
        if (!persona || !job) {
            showToast('Please enter both persona and job to be done.');
            return;
        }
        const documents = panelSelectedFiles.map(file => ({
            filename: file.name,
            title: file.name.replace(/\.[^.]+$/, '')
        }));
        const inputJson = {
            challenge_info: {
                challenge_id: 'round_1b_002',
                test_case_name: 'custom_case',
                description: 'User Provided'
            },
            documents,
            persona: { role: persona },
            job_to_be_done: { task: job }
        };
        const formData = new FormData();
        panelSelectedFiles.forEach((file, idx) => {
            formData.append('pdfs', file, file.name);
        });
        formData.append('input_json', new Blob([JSON.stringify(inputJson)], { type: 'application/json' }), 'challenge1b_input.json');
        progressContainerPanel.style.display = 'block';
        progressFillPanel.style.width = '0%';
        progressTextPanel.textContent = '0%';
        analyzeBtnPanel.disabled = true;
        status.textContent = 'Analyzing...';
        await new Promise(r => setTimeout(r, 0));
        try {
            const response = await fetch('https://pdf-chatbot-lm6d.onrender.com/upload/', {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                const result = await response.json();
                showToast('Analysis complete!');
                displayAnalysisResult(result);
            } else {
                showToast('Backend error: ' + response.statusText);
            }
        } catch (err) {
            showToast('Error connecting to backend.');
        } finally {
            progressContainerPanel.style.display = 'none';
            progressFillPanel.style.width = '0%';
            progressTextPanel.textContent = '0%';
            analyzeBtnPanel.disabled = false;
            status.textContent = 'Online';
        }
    });


    function displayAnalysisResult(result) {
        const container = document.createElement('div');
        container.id = 'analysis-output';
    
        const subsectionAnalysis = result.subsection_analysis || [];
        const extractedSections = result.extracted_sections || [];
    
        // 🧠 Title for Subsection Analysis
        const title = document.createElement('h3');
        title.textContent = `🧠 Subsection Analysis`;
        container.appendChild(title);
    
        // Filter entries that have meaningful refined_text
        const filteredSubsections = subsectionAnalysis.filter(
            entry => entry.refined_text && entry.refined_text.trim().length > 10
        );
    
        if (filteredSubsections.length === 0) {
            const emptyMsg = document.createElement('p');
            emptyMsg.textContent = 'No analysis results available.';
            emptyMsg.style.color = '#ccc';
            container.appendChild(emptyMsg);
        }
    
        // 📘 Display each filtered analysis block
        filteredSubsections.forEach(entry => {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'analysis-card';
            sectionDiv.style.marginBottom = '1em';
            sectionDiv.style.padding = '10px';
            sectionDiv.style.border = '1px solid #ccc';
            sectionDiv.style.borderRadius = '8px';
            sectionDiv.style.backgroundColor = '#0e0c0cff';
    
            const docTitle = document.createElement('strong');
            docTitle.textContent = `📘 ${entry.document} (Page ${entry.page_number})`;
            sectionDiv.appendChild(docTitle);
    
            // Hybrid splitting logic: bullet symbols OR sentence-based
            const points = (entry.refined_text || "")
                .split(/[\u2022•\-–]\s+|(?<=\.)\s+/)  // Split by bullets or after periods
                .map(s => s.trim())
                .filter(p => p.length > 0);
    
            const ul = document.createElement('ul');
            points.forEach(pt => {
                const li = document.createElement('li');
                li.textContent = pt.endsWith('.') ? pt : pt + '.'; // Ensure sentence ends with .
                ul.appendChild(li);
            });
    
            sectionDiv.appendChild(ul);
            // Make the card clickable: just log and show link in chat
            sectionDiv.onclick = () => {
                const pdfUrl = entry.pdf_url || getPDFUrlForDocument(entry.document);
                console.log("📄 Opening PDF:", pdfUrl);
                const linkMessage = `<a href="${pdfUrl}" target="_blank" style="color:#5ad1e6;text-decoration:underline;">📄 Open PDF: ${entry.document}</a>`;
                addMessageToUI(linkMessage, false, false);
            }
            container.appendChild(sectionDiv);
        });
    
        // ➕ Add extracted_sections as reference cards
        if (extractedSections.length > 0) {
            const suggestionHeader = document.createElement('h4');
            suggestionHeader.style.marginTop = '20px';
            suggestionHeader.textContent = '📎 You can also refer to these particular sections for more information:';
            container.appendChild(suggestionHeader);
    
            extractedSections.forEach(section => {
                const sectionRef = document.createElement('div');
                sectionRef.style.margin = '8px 0';
                sectionRef.style.padding = '8px';
                sectionRef.style.backgroundColor = '#0e0c0cff';
                sectionRef.style.borderLeft = '4px solid #3b82f6';
                sectionRef.style.borderRadius = '4px';
    
                const lines = [
                    `📄 PDF: ${section.document}`,
                    `📑 Subsection Title: ${section.section_title}`,
                    `📄 Page No: ${section.page_number}`
                ];
    
                lines.forEach(line => {
                    const p = document.createElement('p');
                    p.style.margin = '2px 0';
                    p.textContent = line;
                    sectionRef.appendChild(p);
                });
    
                container.appendChild(sectionRef);
            });
        }
    
        addMessageToUI(container.outerHTML, false);
    }
});