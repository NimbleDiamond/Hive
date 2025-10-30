// Submind Web Interface - Main JavaScript
// Handles Server-Sent Events and UI updates

let eventSource = null;
let currentHistory = [];
let currentSummary = null;
let abortController = null;

// Submind toggle state
let enabledSubminds = new Set();
let allSubminds = [];
let presets = {};
let autoTerminate = true; // Auto-end conversation detection

// DOM Elements
const chatForm = document.getElementById('chatForm');
const promptInput = document.getElementById('promptInput');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const chatContainer = document.getElementById('chatContainer');
const statusBar = document.getElementById('statusBar');
const statusText = document.getElementById('statusText');
const exportBtn = document.getElementById('exportBtn');
const newChatBtn = document.getElementById('newChatBtn');
const presetSelect = document.getElementById('presetSelect');
const activeCount = document.getElementById('activeCount');
const totalCount = document.getElementById('totalCount');
const autoTerminateToggle = document.getElementById('autoTerminateToggle');

// Color mapping for subminds
const colorMap = {
    'blue': 'bg-blue-500',
    'cyan': 'bg-cyan-500',
    'green': 'bg-green-500',
    'magenta': 'bg-purple-500',
    'purple': 'bg-purple-500',
    'red': 'bg-red-500',
    'yellow': 'bg-yellow-500',
    'white': 'bg-gray-500',
};

const textColorMap = {
    'blue': 'text-blue-400',
    'cyan': 'text-cyan-400',
    'green': 'text-green-400',
    'magenta': 'text-purple-400',
    'purple': 'text-purple-400',
    'red': 'text-red-400',
    'yellow': 'text-yellow-400',
    'white': 'text-gray-400',
};

// Submind info (loaded from template)
let submindInfo = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Load submind info and presets
    fetch('/config')
        .then(res => res.json())
        .then(data => {
            data.subminds.forEach(s => {
                submindInfo[s.name] = s;
                allSubminds.push(s.name);
                enabledSubminds.add(s.name); // Start with all enabled
            });

            // Load presets
            presets = data.presets || {};
            loadPresets();

            // Update counter
            updateActiveCounter();

            // Initialize chip states
            updateChipStates();
        });

    // Form submission
    chatForm.addEventListener('submit', handleSubmit);

    // New chat button
    newChatBtn.addEventListener('click', () => {
        location.reload();
    });

    // Export button
    exportBtn.addEventListener('click', handleExport);

    // Stop button
    stopBtn.addEventListener('click', handleStop);

    // Preset selector
    presetSelect.addEventListener('change', handlePresetChange);

    // Submind chip toggles
    document.querySelectorAll('.submind-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const submindName = chip.dataset.submind;
            toggleSubmind(submindName);
        });
    });

    // Auto-terminate toggle
    autoTerminateToggle.addEventListener('change', () => {
        autoTerminate = autoTerminateToggle.checked;
        console.log('Auto-terminate:', autoTerminate ? 'ON' : 'OFF');
    });
});

// Preset and toggle functions
function loadPresets() {
    // Populate preset selector
    presetSelect.innerHTML = '';
    Object.keys(presets).forEach(presetKey => {
        const preset = presets[presetKey];
        const option = document.createElement('option');
        option.value = presetKey;
        option.textContent = preset.name;
        presetSelect.appendChild(option);
    });
}

function handlePresetChange() {
    const presetKey = presetSelect.value;
    if (!presets[presetKey]) return;

    const preset = presets[presetKey];

    // Clear and set enabled subminds based on preset
    enabledSubminds.clear();
    preset.subminds.forEach(name => enabledSubminds.add(name));

    // Update UI
    updateChipStates();
    updateActiveCounter();
}

function toggleSubmind(submindName) {
    // Check if we can toggle (minimum 2 required)
    if (enabledSubminds.has(submindName) && enabledSubminds.size <= 2) {
        showStatus('Minimum 2 subminds required', true);
        setTimeout(hideStatus, 2000);
        return;
    }

    // Toggle the submind
    if (enabledSubminds.has(submindName)) {
        enabledSubminds.delete(submindName);
    } else {
        enabledSubminds.add(submindName);
    }

    // Update UI
    updateChipStates();
    updateActiveCounter();

    // Reset preset selector to "custom" if it exists, otherwise keep current
    // (since manual toggle means not using preset anymore)
}

function updateChipStates() {
    document.querySelectorAll('.submind-chip').forEach(chip => {
        const submindName = chip.dataset.submind;
        const isEnabled = enabledSubminds.has(submindName);

        chip.dataset.enabled = isEnabled;

        if (isEnabled) {
            // Active state
            chip.classList.remove('opacity-40', 'border', 'border-gray-600');
            chip.classList.add('bg-discord-darker');
        } else {
            // Disabled state
            chip.classList.add('opacity-40', 'border', 'border-gray-600');
            chip.classList.remove('bg-discord-darker');
        }
    });
}

function updateActiveCounter() {
    activeCount.textContent = enabledSubminds.size;
    totalCount.textContent = allSubminds.length;
}

function handleSubmit(e) {
    e.preventDefault();

    const prompt = promptInput.value.trim();
    if (!prompt) return;

    // Check for stop command
    if (prompt.toLowerCase() === 'stop') {
        addMessage('System', 'Discussion stopped. Type a new question to start again.', 'system');
        return;
    }

    // Disable input
    promptInput.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = 'Thinking...';

    // Add user message to chat
    addMessage('User', prompt, 'user');

    // Clear input
    promptInput.value = '';

    // Start SSE connection
    startConversation(prompt);
}

function startConversation(prompt) {
    // Close existing connection
    if (eventSource) {
        eventSource.close();
    }

    // Create new abort controller
    abortController = new AbortController();

    // Show status
    showStatus('Starting discussion...');

    // Show stop button, hide send button
    stopBtn.classList.remove('hidden');
    sendBtn.classList.add('hidden');

    // Create new EventSource
    eventSource = new EventSource('/dev/null'); // We'll use fetch instead

    // Use fetch with streaming
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: prompt,
            enabled_subminds: Array.from(enabledSubminds),
            auto_terminate: autoTerminate
        }),
        signal: abortController.signal,
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function readStream() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    onConversationComplete();
                    return;
                }

                // Decode chunk
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        try {
                            const event = JSON.parse(data);
                            handleEvent(event);
                        } catch (e) {
                            console.error('Error parsing event:', e);
                        }
                    }
                });

                // Continue reading
                readStream();
            });
        }

        readStream();
    })
    .catch(error => {
        // Don't show error if it was intentionally aborted
        if (error.name === 'AbortError') {
            console.log('Request aborted by user');
            return;
        }
        console.error('Error:', error);
        showStatus('Error: ' + error.message, true);
        enableInput();
    });
}

function handleEvent(event) {
    console.log('Event:', event);

    switch (event.type) {
        case 'start':
            showStatus('Discussion started');
            break;

        case 'user_message':
            // Already added by handleSubmit
            break;

        case 'round_start':
            showStatus(`Round ${event.round} starting...`);
            break;

        case 'submind_start':
            showStatus(`${event.submind} is thinking...`);
            // Add thinking indicator
            addThinkingIndicator(event.submind);
            break;

        case 'submind_response':
            // Remove thinking indicator
            removeThinkingIndicator(event.message.speaker);
            // Add message
            addMessage(
                event.message.speaker,
                event.message.content,
                event.message.role,
                event.message
            );
            currentHistory.push(event.message);
            break;

        case 'round_complete':
            showStatus(`Round ${event.round} complete`);
            break;

        case 'termination':
            addMessage('System', event.message.content, 'system');
            showStatus(event.reason);
            break;

        case 'complete':
            currentSummary = event.summary;
            currentHistory = event.history;
            onConversationComplete();
            break;

        case 'export_complete':
            console.log('Exported to:', event.files);
            break;

        case 'error':
            // Remove thinking indicator if there is one
            if (event.submind) {
                removeThinkingIndicator(event.submind);
                // Add error message to chat
                addMessage('System', `${event.submind} encountered an error: ${event.error}`, 'system');
            } else {
                // General error - enable input
                enableInput();
            }
            showStatus('Error: ' + event.error, true);
            break;
    }
}

function addMessage(speaker, content, role, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex items-start gap-3 animate-fade-in';

    // Get submind info
    const info = submindInfo[speaker] || {};
    const color = info.color || 'white';

    // Avatar
    let avatarContent = '🤖';
    let avatarClass = 'bg-gray-700';

    if (speaker === 'User') {
        avatarContent = '👤';
        avatarClass = 'bg-blue-600';
    } else if (speaker === 'System') {
        avatarContent = '⚙️';
        avatarClass = 'bg-gray-600';
    } else {
        // Submind avatar
        const emoji = {
            'Doctrinal': '📚',
            'Analytical': '🔬',
            'Strategic': '🎯',
            'Creative': '💡',
            'Skeptic': '🤔'
        }[speaker] || '🧠';
        avatarContent = emoji;
        avatarClass = colorMap[color] || 'bg-gray-700';
    }

    const avatar = `
        <div class="w-10 h-10 rounded-full ${avatarClass} flex items-center justify-center text-xl flex-shrink-0">
            ${avatarContent}
        </div>
    `;

    // Message content
    const textColor = speaker !== 'User' && speaker !== 'System'
        ? (textColorMap[color] || 'text-gray-300')
        : 'text-gray-300';

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Get model name if available (extract short name from full path)
    let modelBadge = '';
    if (metadata.model) {
        const modelShortName = metadata.model.split('/').pop().split(':')[0]; // Extract "llama-3.2" from "meta-llama/llama-3.2-3b-instruct:free"
        modelBadge = `<span class="text-xs text-gray-600 bg-gray-800 px-2 py-0.5 rounded">${modelShortName}</span>`;
    }

    const messageContent = `
        <div class="flex-1 max-w-4xl">
            <div class="flex items-baseline gap-2">
                <span class="font-semibold ${textColor}">${speaker}</span>
                ${modelBadge}
                <span class="text-xs text-gray-500">${timestamp}</span>
            </div>
            <div class="mt-1 text-gray-200 whitespace-pre-wrap message-content">
                ${formatContent(content)}
            </div>
        </div>
    `;

    messageDiv.innerHTML = avatar + messageContent;
    chatContainer.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

function addThinkingIndicator(submind) {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = `thinking-${submind}`;
    thinkingDiv.className = 'flex items-start gap-3 opacity-60';

    const info = submindInfo[submind] || {};
    const color = info.color || 'white';
    const avatarClass = colorMap[color] || 'bg-gray-700';
    const textColor = textColorMap[color] || 'text-gray-400';

    const emoji = {
        'Doctrinal': '📚',
        'Analytical': '🔬',
        'Strategic': '🎯',
        'Creative': '💡',
        'Skeptic': '🤔'
    }[submind] || '🧠';

    thinkingDiv.innerHTML = `
        <div class="w-10 h-10 rounded-full ${avatarClass} flex items-center justify-center text-xl flex-shrink-0">
            ${emoji}
        </div>
        <div class="flex-1">
            <span class="font-semibold ${textColor}">${submind}</span>
            <div class="mt-1 text-gray-400">
                <span class="thinking-dots">thinking</span>
            </div>
        </div>
    `;

    chatContainer.appendChild(thinkingDiv);
    scrollToBottom();
}

function removeThinkingIndicator(submind) {
    const thinkingDiv = document.getElementById(`thinking-${submind}`);
    if (thinkingDiv) {
        thinkingDiv.remove();
    }
}

function formatContent(content) {
    // Basic formatting: preserve line breaks
    return content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');
}

function showStatus(text, isError = false) {
    statusText.textContent = text;
    statusBar.classList.remove('hidden');
    if (isError) {
        statusText.classList.add('text-red-400');
    } else {
        statusText.classList.remove('text-red-400');
    }
}

function hideStatus() {
    statusBar.classList.add('hidden');
}

function enableInput() {
    promptInput.disabled = false;
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
    promptInput.focus();

    // Show send button, hide stop button
    sendBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
}

function onConversationComplete() {
    showStatus('Discussion complete');
    enableInput();
    exportBtn.classList.remove('hidden');

    // Hide status after a delay
    setTimeout(hideStatus, 3000);
}

function handleExport() {
    if (!currentHistory.length) return;

    // Create JSON export
    const exportData = {
        messages: currentHistory,
        metadata: currentSummary,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `submind_conversation_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    showStatus('Conversation exported');
    setTimeout(hideStatus, 2000);
}

function handleStop() {
    // Abort the ongoing request
    if (abortController) {
        abortController.abort();
        abortController = null;
    }

    // Remove all thinking indicators
    const thinkingDivs = document.querySelectorAll('[id^="thinking-"]');
    thinkingDivs.forEach(div => div.remove());

    // Add stop message to chat
    addMessage('System', 'Discussion stopped by user.', 'system');

    // Enable input
    enableInput();

    // Show status
    showStatus('Discussion stopped');
    setTimeout(hideStatus, 2000);
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
