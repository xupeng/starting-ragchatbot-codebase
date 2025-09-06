// API base URL - use relative path to work from any host
const API_URL = '/api';

// Global state
let currentSessionId = null;

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, newChatButton;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements after page loads
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    newChatButton = document.getElementById('newChatButton');
    
    setupEventListeners();
    createNewSession();
    loadCourseStats();
});

// Event Listeners
function setupEventListeners() {
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // New chat button
    newChatButton.addEventListener('click', createNewSession);
    
    
    // Suggested questions
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // Disable input
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage(query, 'user');

    // Add loading message - create a unique container for it
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) {
            // 尝试获取详细的错误信息
            let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
            
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    if (typeof errorData.detail === 'object') {
                        // 详细错误对象
                        errorDetail = `❌ ${errorData.detail.error || 'Unknown error'}`;
                        
                        if (errorData.detail.type) {
                            errorDetail += `\n\n🔍 **错误类型**: ${errorData.detail.type}`;
                        }
                        
                        if (errorData.detail.help) {
                            errorDetail += `\n\n💡 **建议**: ${errorData.detail.help}`;
                        }
                        
                        // 添加调试信息
                        errorDetail += '\n\n🔧 **调试信息**:';
                        errorDetail += '\n- 请检查服务器控制台日志';
                        errorDetail += '\n- 确认 API 服务正在运行';
                        errorDetail += '\n- 验证网络连接';
                        
                    } else {
                        // 简单错误字符串
                        errorDetail = `❌ ${errorData.detail}`;
                    }
                }
            } catch (parseError) {
                // JSON 解析失败，使用原始响应
                const text = await response.text();
                errorDetail += `\n\n服务器响应: ${text.substring(0, 200)}${text.length > 200 ? '...' : ''}`;
            }
            
            throw new Error(errorDetail);
        }

        const data = await response.json();
        
        // Update session ID if new
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // Replace loading message with response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        // Replace loading message with detailed error
        loadingMessage.remove();
        
        let errorMessage = '抱歉，处理您的查询时遇到了问题。\n\n';
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage += '❌ **网络连接失败**\n\n';
            errorMessage += '💡 **可能的原因**:\n';
            errorMessage += '- 服务器未运行\n';
            errorMessage += '- 网络连接问题\n';
            errorMessage += '- 防火墙阻止连接\n\n';
            errorMessage += '🔧 **建议**:\n';
            errorMessage += '- 确认服务器正在运行 (uvicorn app:app --reload)\n';
            errorMessage += '- 检查服务器地址是否正确';
        } else {
            errorMessage += error.message;
        }
        
        addMessage(errorMessage, 'assistant');
        
        // 在控制台记录详细错误用于调试
        console.error('Query error details:', error);
        
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    let html = `<div class="message-content">${displayContent}</div>`;
    
    if (sources && sources.length > 0) {
        // Debug: Log sources structure
        console.log('Sources received:', sources);
        
        // Format sources - handle both string and object formats
        const formattedSources = sources.map((source, index) => {
            console.log(`Processing source ${index}:`, source, 'Type:', typeof source);
            
            if (typeof source === 'string') {
                // Legacy string format - just return as text
                console.log('  -> Using as string:', source);
                return source;
            } else if (source && typeof source === 'object' && source.text) {
                // New object format with potential link
                console.log('  -> Object format, text:', source.text, 'link:', source.link);
                if (source.link) {
                    return `<a href="${source.link}" target="_blank" rel="noopener noreferrer">${source.text}</a>`;
                } else {
                    return source.text;
                }
            } else {
                // Fallback for unexpected formats
                console.log('  -> Fallback, converting to string:', String(source));
                return String(source);
            }
        });
        
        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">Sources</summary>
                <div class="sources-content">
                    ${formattedSources.map(source => `<div class="source-item">${source}</div>`).join('')}
                </div>
            </details>
        `;
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// Helper function to escape HTML for user messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Removed removeMessage function - no longer needed since we handle loading differently

async function createNewSession() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        // Update stats in UI
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // Update course titles
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        // Set default values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}