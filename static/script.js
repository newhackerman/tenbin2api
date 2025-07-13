class TurnstileWebApp {
    constructor() {
        this.ws = null;
        this.wsUrl = `ws://${window.location.hostname}:8401/ws`;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.tasks = new Map();
        this.stats = {
            solved: 0,
            failed: 0,
            totalTime: 0
        };
        
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.connectWebSocket();
        this.updateServerTime();
        this.loadStoredData();
        
        // Update server time every second
        setInterval(() => this.updateServerTime(), 1000);
    }

    bindEventListeners() {
        // Form submission
        document.getElementById('solverForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.solveTurnstile();
        });

        // Quick actions
        document.getElementById('clearHistoryBtn').addEventListener('click', () => this.clearHistory());
        document.getElementById('exportResultsBtn').addEventListener('click', () => this.exportResults());
        document.getElementById('reconnectBtn').addEventListener('click', () => this.forceReconnect());
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshTasks());
        
        // Filter
        document.getElementById('filterSelect').addEventListener('change', (e) => {
            this.filterTasks(e.target.value);
        });

        // Auto-save form data
        ['urlInput', 'sitekeyInput', 'actionInput', 'cdataInput'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => this.saveFormData());
        });
    }

    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                this.reconnectAttempts = 0;
                this.sendMessage('ping', {});
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
            
            // Exponential backoff
            this.reconnectDelay *= 1.5;
        } else {
            this.showNotification('Connection failed after multiple attempts', 'error');
        }
    }

    forceReconnect() {
        this.reconnectAttempts = 0;
        this.reconnectDelay = 3000;
        if (this.ws) {
            this.ws.close();
        }
        this.connectWebSocket();
    }

    sendMessage(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    handleWebSocketMessage(message) {
        const { type, data } = message;

        switch (type) {
            case 'pong':
                console.log('Received pong from server');
                break;
                
            case 'task_created':
                this.handleTaskCreated(data);
                break;
                
            case 'task_progress':
                this.handleTaskProgress(data);
                break;
                
            case 'task_completed':
                this.handleTaskCompleted(data);
                break;
                
            case 'task_failed':
                this.handleTaskFailed(data);
                break;
                
            case 'server_stats':
                this.updateServerStats(data);
                break;
                
            default:
                console.log('Unknown message type:', type);
        }
    }

    async solveTurnstile() {
        const url = document.getElementById('urlInput').value;
        const sitekey = document.getElementById('sitekeyInput').value;
        const action = document.getElementById('actionInput').value;
        const cdata = document.getElementById('cdataInput').value;

        if (!url || !sitekey) {
            this.showNotification('URL and Site Key are required', 'error');
            return;
        }

        this.showLoading(true);
        
        try {
            // Create task via API
            const params = new URLSearchParams({
                url: url,
                sitekey: sitekey
            });
            
            if (action) params.append('action', action);
            if (cdata) params.append('cdata', cdata);

            const response = await fetch(`/turnstile?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (response.ok && result.task_id) {
                this.monitorTask(result.task_id, { url, sitekey, action, cdata });
                this.showNotification('Task created successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to create task');
            }
            
        } catch (error) {
            console.error('Error solving turnstile:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
            this.showLoading(false);
        }
    }

    async monitorTask(taskId, taskData) {
        const task = {
            id: taskId,
            status: 'pending',
            startTime: Date.now(),
            ...taskData
        };
        
        this.tasks.set(taskId, task);
        this.updateTaskHistory();
        
        // Poll for result
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/result?id=${taskId}`);
                const result = await response.json();
                
                if (result.value && result.value !== 'CAPTCHA_NOT_READY') {
                    clearInterval(pollInterval);
                    
                    if (result.value === 'CAPTCHA_FAIL') {
                        this.handleTaskFailed({ taskId, error: 'Captcha solving failed' });
                    } else {
                        this.handleTaskCompleted({
                            taskId,
                            result: result.value,
                            elapsed_time: result.elapsed_time
                        });
                    }
                }
            } catch (error) {
                console.error('Error polling task result:', error);
            }
        }, 2000);
        
        // Timeout after 60 seconds
        setTimeout(() => {
            clearInterval(pollInterval);
            const currentTask = this.tasks.get(taskId);
            if (currentTask && currentTask.status === 'pending') {
                this.handleTaskFailed({ taskId, error: 'Task timeout' });
            }
        }, 60000);
    }

    handleTaskCreated(data) {
        const { taskId } = data;
        const task = this.tasks.get(taskId);
        if (task) {
            task.status = 'running';
            this.updateTaskHistory();
        }
    }

    handleTaskProgress(data) {
        const { taskId, status } = data;
        document.getElementById('loadingStatus').textContent = status;
        
        const task = this.tasks.get(taskId);
        if (task) {
            task.progress = status;
            this.updateTaskHistory();
        }
    }

    handleTaskCompleted(data) {
        const { taskId, result, elapsed_time } = data;
        const task = this.tasks.get(taskId);
        
        if (task) {
            task.status = 'success';
            task.result = result;
            task.elapsedTime = elapsed_time;
            task.endTime = Date.now();
            
            this.stats.solved++;
            this.stats.totalTime += elapsed_time;
            
            this.updateTaskHistory();
            this.updateStats();
            this.showLoading(false);
            
            this.showNotification(`Challenge solved in ${elapsed_time}s`, 'success');
            
            // Copy result to clipboard
            navigator.clipboard.writeText(result).then(() => {
                this.showNotification('Result copied to clipboard', 'info');
            });
        }
    }

    handleTaskFailed(data) {
        const { taskId, error } = data;
        const task = this.tasks.get(taskId);
        
        if (task) {
            task.status = 'failed';
            task.error = error;
            task.endTime = Date.now();
            
            this.stats.failed++;
            
            this.updateTaskHistory();
            this.updateStats();
            this.showLoading(false);
            
            this.showNotification(`Task failed: ${error}`, 'error');
        }
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connectionStatus');
        const statusText = document.getElementById('connectionText');
        const wsStatus = document.getElementById('wsStatus');
        
        if (connected) {
            statusDot.className = 'w-3 h-3 bg-green-500 rounded-full pulse-dot mr-2';
            statusText.textContent = 'Connected';
            wsStatus.textContent = 'Connected';
            wsStatus.className = 'text-green-400';
        } else {
            statusDot.className = 'w-3 h-3 bg-red-500 rounded-full pulse-dot mr-2';
            statusText.textContent = 'Disconnected';
            wsStatus.textContent = 'Disconnected';
            wsStatus.className = 'text-red-400';
        }
    }

    updateServerTime() {
        const now = new Date();
        document.getElementById('serverTime').textContent = now.toLocaleTimeString();
    }

    updateTaskHistory() {
        const container = document.getElementById('taskHistory');
        const filter = document.getElementById('filterSelect').value;
        
        const filteredTasks = Array.from(this.tasks.values()).filter(task => {
            if (filter === 'all') return true;
            if (filter === 'success') return task.status === 'success';
            if (filter === 'failed') return task.status === 'failed';
            if (filter === 'pending') return task.status === 'pending' || task.status === 'running';
            return true;
        });
        
        container.innerHTML = '';
        
        if (filteredTasks.length === 0) {
            container.innerHTML = '<p class="text-white/60 text-center py-8">No tasks found</p>';
            return;
        }
        
        filteredTasks.reverse().forEach(task => {
            const taskElement = this.createTaskElement(task);
            container.appendChild(taskElement);
        });
        
        // Update queue status
        const pendingCount = Array.from(this.tasks.values()).filter(t => 
            t.status === 'pending' || t.status === 'running'
        ).length;
        document.getElementById('queueStatus').textContent = `${pendingCount} tasks`;
    }

    createTaskElement(task) {
        const div = document.createElement('div');
        div.className = 'task-card glass-effect rounded-lg p-4 border border-white/20';
        
        const statusColor = {
            'success': 'text-green-400',
            'failed': 'text-red-400',
            'pending': 'text-yellow-400',
            'running': 'text-blue-400'
        }[task.status] || 'text-gray-400';
        
        const statusIcon = {
            'success': 'fas fa-check-circle',
            'failed': 'fas fa-times-circle',
            'pending': 'fas fa-clock',
            'running': 'fas fa-spinner fa-spin'
        }[task.status] || 'fas fa-question-circle';
        
        const elapsed = task.elapsedTime || (task.endTime ? (task.endTime - task.startTime) / 1000 : '--');
        
        div.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <div class="flex-1">
                    <div class="flex items-center mb-1">
                        <i class="${statusIcon} ${statusColor} mr-2"></i>
                        <span class="text-white font-medium">Task ${task.id.substring(0, 8)}</span>
                        <span class="${statusColor} ml-2 text-sm capitalize">${task.status}</span>
                    </div>
                    <p class="text-white/80 text-sm mb-1">${task.url}</p>
                    <p class="text-white/60 text-xs">Sitekey: ${task.sitekey.substring(0, 20)}...</p>
                </div>
                <div class="text-right text-sm">
                    <p class="text-white/80">${elapsed}s</p>
                    <p class="text-white/60 text-xs">${new Date(task.startTime).toLocaleTimeString()}</p>
                </div>
            </div>
            ${task.result ? `
                <div class="mt-2 p-2 bg-green-900/30 rounded border border-green-500/30">
                    <p class="text-green-400 text-xs font-mono break-all">${task.result.substring(0, 50)}...</p>
                    <button onclick="navigator.clipboard.writeText('${task.result}')" class="text-green-300 hover:text-green-200 text-xs mt-1">
                        <i class="fas fa-copy mr-1"></i>Copy Full Result
                    </button>
                </div>
            ` : ''}
            ${task.error ? `
                <div class="mt-2 p-2 bg-red-900/30 rounded border border-red-500/30">
                    <p class="text-red-400 text-xs">${task.error}</p>
                </div>
            ` : ''}
            ${task.progress ? `
                <div class="mt-2 p-2 bg-blue-900/30 rounded border border-blue-500/30">
                    <p class="text-blue-400 text-xs">${task.progress}</p>
                </div>
            ` : ''}
        `;
        
        return div;
    }

    updateStats() {
        document.getElementById('solvedCount').textContent = this.stats.solved;
        document.getElementById('failedCount').textContent = this.stats.failed;
        
        const avgTime = this.stats.solved > 0 ? 
            (this.stats.totalTime / this.stats.solved).toFixed(2) + 's' : '--';
        document.getElementById('avgTime').textContent = avgTime;
    }

    updateServerStats(stats) {
        // Update server-provided statistics if available
        if (stats.queue_size !== undefined) {
            document.getElementById('queueStatus').textContent = `${stats.queue_size} tasks`;
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
            overlay.classList.add('flex');
            document.getElementById('loadingStatus').textContent = 'Initializing...';
        } else {
            overlay.classList.add('hidden');
            overlay.classList.remove('flex');
        }
    }

    showNotification(message, type = 'info') {
        const icon = {
            'success': 'success',
            'error': 'error',
            'warning': 'warning',
            'info': 'info'
        }[type] || 'info';
        
        Swal.fire({
            icon: icon,
            title: message,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            background: 'rgba(255, 255, 255, 0.1)',
            color: '#ffffff',
            backdrop: false
        });
    }

    filterTasks(filter) {
        this.updateTaskHistory();
    }

    clearHistory() {
        Swal.fire({
            title: 'Clear History?',
            text: 'This will remove all task history. This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, clear it!',
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#ffffff'
        }).then((result) => {
            if (result.isConfirmed) {
                this.tasks.clear();
                this.stats = { solved: 0, failed: 0, totalTime: 0 };
                this.updateTaskHistory();
                this.updateStats();
                this.saveStoredData();
                this.showNotification('History cleared', 'success');
            }
        });
    }

    exportResults() {
        const data = {
            tasks: Array.from(this.tasks.values()),
            stats: this.stats,
            exportDate: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `turnstile-results-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('Results exported', 'success');
    }

    refreshTasks() {
        this.updateTaskHistory();
        this.showNotification('Tasks refreshed', 'info');
    }

    saveFormData() {
        const formData = {
            url: document.getElementById('urlInput').value,
            sitekey: document.getElementById('sitekeyInput').value,
            action: document.getElementById('actionInput').value,
            cdata: document.getElementById('cdataInput').value
        };
        localStorage.setItem('turnstile_form_data', JSON.stringify(formData));
    }

    saveStoredData() {
        const data = {
            tasks: Array.from(this.tasks.entries()),
            stats: this.stats
        };
        localStorage.setItem('turnstile_app_data', JSON.stringify(data));
    }

    loadStoredData() {
        // Load form data
        try {
            const formData = JSON.parse(localStorage.getItem('turnstile_form_data') || '{}');
            if (formData.url) document.getElementById('urlInput').value = formData.url;
            if (formData.sitekey) document.getElementById('sitekeyInput').value = formData.sitekey;
            if (formData.action) document.getElementById('actionInput').value = formData.action;
            if (formData.cdata) document.getElementById('cdataInput').value = formData.cdata;
        } catch (error) {
            console.error('Failed to load form data:', error);
        }
        
        // Load app data
        try {
            const appData = JSON.parse(localStorage.getItem('turnstile_app_data') || '{}');
            if (appData.tasks) {
                this.tasks = new Map(appData.tasks);
                this.updateTaskHistory();
            }
            if (appData.stats) {
                this.stats = appData.stats;
                this.updateStats();
            }
        } catch (error) {
            console.error('Failed to load app data:', error);
        }
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.turnstileApp = new TurnstileWebApp();
});

// Save data before page unload
window.addEventListener('beforeunload', () => {
    if (window.turnstileApp) {
        window.turnstileApp.saveStoredData();
    }
});