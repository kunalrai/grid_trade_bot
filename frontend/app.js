// Configuration
const API_BASE_URL = 'http://localhost:5000';
const SOCKET_URL = 'http://localhost:5000';

// State
let socket = null;
let priceChart = null;
let priceHistory = [];
const MAX_PRICE_HISTORY = 50;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    initializePriceChart();
    initializeEventListeners();
    loadConfiguration();
    addLog('Application initialized');
});

// WebSocket Connection
function initializeWebSocket() {
    socket = io(SOCKET_URL);

    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus(true);
        addLog('Connected to server', 'success');
        socket.emit('request_status');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
        addLog('Disconnected from server', 'error');
    });

    socket.on('status_update', (status) => {
        console.log('Status update:', status);
        updateBotStatus(status);
    });
}

// Initialize Price Chart
function initializePriceChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'SOL/USDT Price',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                },
                x: {
                    display: false
                }
            }
        }
    });
}

// Event Listeners
function initializeEventListeners() {
    document.getElementById('startBtn').addEventListener('click', startBot);
    document.getElementById('stopBtn').addEventListener('click', stopBot);
    document.getElementById('pauseBtn').addEventListener('click', pauseBtn);
    document.getElementById('resumeBtn').addEventListener('click', resumeBot);
    document.getElementById('saveConfigBtn').addEventListener('click', saveConfiguration);
    document.getElementById('refreshWalletBtn').addEventListener('click', loadWalletDetails);
    document.getElementById('clearLogBtn').addEventListener('click', clearLog);
    document.getElementById('refreshLogBtn').addEventListener('click', loadDetailedLogs);

    // Load wallet details on startup
    loadWalletDetails();
}

// API Calls
async function startBot() {
    try {
        addLog('Starting bot...');
        const response = await fetch(`${API_BASE_URL}/api/bot/start`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            addLog('Bot started successfully', 'success');
            updateControlButtons('running');
        } else {
            addLog('Failed to start bot: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error starting bot: ' + error.message, 'error');
    }
}

async function stopBot() {
    try {
        addLog('Stopping bot...');
        const response = await fetch(`${API_BASE_URL}/api/bot/stop`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            addLog('Bot stopped successfully', 'success');
            updateControlButtons('stopped');
        } else {
            addLog('Failed to stop bot: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error stopping bot: ' + error.message, 'error');
    }
}

async function pauseBot() {
    try {
        addLog('Pausing bot...');
        const response = await fetch(`${API_BASE_URL}/api/bot/pause`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            addLog('Bot paused', 'success');
            updateControlButtons('paused');
        } else {
            addLog('Failed to pause bot: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error pausing bot: ' + error.message, 'error');
    }
}

async function resumeBot() {
    try {
        addLog('Resuming bot...');
        const response = await fetch(`${API_BASE_URL}/api/bot/resume`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            addLog('Bot resumed', 'success');
            updateControlButtons('running');
        } else {
            addLog('Failed to resume bot: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error resuming bot: ' + error.message, 'error');
    }
}

async function loadConfiguration() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/config`);
        const config = await response.json();

        if (config.trading) {
            document.getElementById('configMarket').value = config.trading.market || 'SOLUSDT';
            document.getElementById('configPositionSize').value = config.trading.position_size || 10;
            document.getElementById('configLeverage').value = config.trading.leverage || 1;
            document.getElementById('configBuyLevel').value = config.trading.buy_level || 138;
            document.getElementById('configSellLevel').value = config.trading.sell_level || 143;

            // Update display
            document.getElementById('buyLevel').textContent = '$' + (config.trading.buy_level || 138).toFixed(2);
            document.getElementById('sellLevel').textContent = '$' + (config.trading.sell_level || 143).toFixed(2);
        }

        if (config.safety) {
            document.getElementById('configMaxLoss').value = config.safety.max_cumulative_loss || -50;
        }

        addLog('Configuration loaded');
    } catch (error) {
        addLog('Error loading configuration: ' + error.message, 'error');
    }
}

async function saveConfiguration() {
    try {
        const config = {
            trading: {
                market: document.getElementById('configMarket').value,
                position_size: parseFloat(document.getElementById('configPositionSize').value),
                leverage: parseInt(document.getElementById('configLeverage').value),
                buy_level: parseFloat(document.getElementById('configBuyLevel').value),
                sell_level: parseFloat(document.getElementById('configSellLevel').value)
            },
            safety: {
                max_cumulative_loss: parseFloat(document.getElementById('configMaxLoss').value)
            }
        };

        const response = await fetch(`${API_BASE_URL}/api/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.success) {
            addLog('Configuration saved successfully', 'success');
            // Update display
            document.getElementById('buyLevel').textContent = '$' + config.trading.buy_level.toFixed(2);
            document.getElementById('sellLevel').textContent = '$' + config.trading.sell_level.toFixed(2);
        } else {
            addLog('Failed to save configuration: ' + data.error, 'error');
        }
    } catch (error) {
        addLog('Error saving configuration: ' + error.message, 'error');
    }
}

// UI Updates
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (connected) {
        statusEl.classList.add('connected');
        statusEl.classList.remove('disconnected');
        statusEl.innerHTML = '<span class="status-dot"></span><span>Connected</span>';
    } else {
        statusEl.classList.remove('connected');
        statusEl.classList.add('disconnected');
        statusEl.innerHTML = '<span class="status-dot"></span><span>Disconnected</span>';
    }
}

function updateBotStatus(status) {
    // Update state indicator
    const statusEl = document.getElementById('botStatus');
    const state = status.state || 'stopped';

    let statusText = state.charAt(0).toUpperCase() + state.slice(1);
    let statusClass = state;

    // Add error message if present
    let errorHTML = '';
    if (state === 'error' && status.error) {
        errorHTML = `<div class="error-message">${status.error}</div>`;
        addLog('Bot Error: ' + status.error, 'error');
    }

    statusEl.innerHTML = `
        <div class="status-indicator ${statusClass}">
            <span class="status-dot"></span>
            <span class="status-text">${statusText}</span>
        </div>
        ${errorHTML}
    `;

    // Update control buttons
    updateControlButtons(state);

    // Update price
    if (status.current_price) {
        document.getElementById('currentPrice').textContent = '$' + status.current_price.toFixed(2);
        updatePriceChart(status.current_price);
    }

    // Update statistics
    document.getElementById('totalTrades').textContent = status.total_trades || 0;
    document.getElementById('winningTrades').textContent = status.winning_trades || 0;
    document.getElementById('winRate').textContent = (status.win_rate || 0).toFixed(1) + '%';
    document.getElementById('cycles').textContent = status.cycles_completed || 0;

    // Update P&L
    const pnl = status.cumulative_pnl || 0;
    const pnlEl = document.getElementById('totalPnl');
    pnlEl.textContent = '$' + pnl.toFixed(2);
    pnlEl.className = 'stat-value ' + (pnl >= 0 ? 'success' : 'danger');

    // Update position
    updatePosition(status.position);

    // Update recent trades
    if (status.recent_trades) {
        updateRecentTrades(status.recent_trades);
    }
}

function updateControlButtons(state) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');

    if (state === 'running') {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        pauseBtn.disabled = false;
        resumeBtn.disabled = true;
    } else if (state === 'paused') {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        pauseBtn.disabled = true;
        resumeBtn.disabled = false;
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        pauseBtn.disabled = true;
        resumeBtn.disabled = true;
    }
}

function updatePriceChart(price) {
    const now = new Date();
    const timeLabel = now.toLocaleTimeString();

    priceHistory.push({ time: timeLabel, price: price });

    if (priceHistory.length > MAX_PRICE_HISTORY) {
        priceHistory.shift();
    }

    priceChart.data.labels = priceHistory.map(p => p.time);
    priceChart.data.datasets[0].data = priceHistory.map(p => p.price);
    priceChart.update('none');
}

function updatePosition(position) {
    const positionContent = document.getElementById('positionContent');

    if (!position || position.size === 0) {
        positionContent.innerHTML = '<div class="no-position">No active position</div>';
        return;
    }

    const pnlClass = position.unrealized_pnl >= 0 ? 'positive' : 'negative';

    positionContent.innerHTML = `
        <div class="position-details">
            <div class="position-item">
                <span>Side</span>
                <strong>${position.side.toUpperCase()}</strong>
            </div>
            <div class="position-item">
                <span>Size</span>
                <strong>${position.size} SOL</strong>
            </div>
            <div class="position-item">
                <span>Entry Price</span>
                <strong>$${position.entry_price.toFixed(2)}</strong>
            </div>
            <div class="position-item ${pnlClass}">
                <span>Unrealized P&L</span>
                <strong>$${position.unrealized_pnl.toFixed(2)}</strong>
            </div>
        </div>
    `;
}

function updateRecentTrades(trades) {
    const tradesListEl = document.getElementById('tradesList');

    if (!trades || trades.length === 0) {
        tradesListEl.innerHTML = '<div class="no-trades">No trades yet</div>';
        return;
    }

    const tradesHTML = trades.reverse().map(trade => {
        const time = new Date(trade.timestamp).toLocaleTimeString();
        const type = trade.type.toLowerCase();
        const profitHTML = trade.profit !== undefined
            ? `<span class="trade-profit ${trade.profit >= 0 ? 'positive' : 'negative'}">
                   ${trade.profit >= 0 ? '+' : ''}$${trade.profit.toFixed(2)}
               </span>`
            : '';

        return `
            <div class="trade-item ${type}">
                <div class="trade-header">
                    <span class="trade-type ${type}">${trade.type}</span>
                    <span class="trade-time">${time}</span>
                </div>
                <div class="trade-details">
                    <span>${trade.quantity} SOL @ $${trade.price.toFixed(2)}</span>
                    ${profitHTML}
                </div>
            </div>
        `;
    }).join('');

    tradesListEl.innerHTML = tradesHTML;
}

function addLog(message, type = '') {
    const logContainer = document.getElementById('activityLog');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry ' + type;
    logEntry.textContent = `[${timestamp}] ${message}`;

    logContainer.insertBefore(logEntry, logContainer.firstChild);

    // Keep only last 50 entries
    while (logContainer.children.length > 50) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Wallet Details Functions
async function loadWalletDetails() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/wallet/details`);
        const data = await response.json();

        const walletContent = document.getElementById('walletContent');

        if (data.success && data.wallet) {
            const walletData = data.wallet;

            // Display wallet balances
            let walletHTML = '<div class="wallet-info">';

            // Check if wallet data is an array (new format)
            if (Array.isArray(walletData) && walletData.length > 0) {
                walletHTML += '<div class="balance-list">';
                walletData.forEach(item => {
                    const currency = item.currency_short_name || item.currency || item.asset;
                    const balance = parseFloat(item.balance || 0);
                    const locked = parseFloat(item.locked_balance || item.locked || 0);
                    const crossMargin = parseFloat(item.cross_user_margin || 0);

                    if (balance > 0 || locked > 0 || crossMargin > 0) {
                        walletHTML += `
                            <div class="balance-item">
                                <span class="currency">${currency}</span>
                                <div class="amounts">
                                    <span class="available">Balance: ${balance}</span>
                                    ${locked > 0 ? `<span class="locked">Locked: ${locked}</span>` : ''}
                                    ${crossMargin > 0 ? `<span class="margin">Margin: ${crossMargin}</span>` : ''}
                                </div>
                            </div>
                        `;
                    }
                });
                walletHTML += '</div>';
            } else {
                walletHTML += '<div class="no-balance">No balance information available</div>';
            }

            walletHTML += '</div>';
            walletContent.innerHTML = walletHTML;
            addLog('Wallet details loaded', 'success');
        } else {
            walletContent.innerHTML = '<div class="wallet-error">Failed to load wallet details</div>';
            addLog('Failed to load wallet: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        document.getElementById('walletContent').innerHTML = '<div class="wallet-error">Error loading wallet</div>';
        addLog('Error loading wallet: ' + error.message, 'error');
    }
}

// Detailed Logging Functions
let logEntries = [];
let errorCount = 0;

async function loadDetailedLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/logs?limit=100`);
        const data = await response.json();

        if (data.success && data.logs) {
            logEntries = data.logs;
            displayLogs();
            addLog('Logs refreshed', 'success');
        }
    } catch (error) {
        addLog('Error loading logs: ' + error.message, 'error');
    }
}

function displayLogs() {
    const logContainer = document.getElementById('activityLog');
    logContainer.innerHTML = '';

    logEntries.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry ' + (log.level || '');

        const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '';
        logEntry.textContent = `[${timestamp}] ${log.message}`;

        logContainer.appendChild(logEntry);
    });

    updateLogStats();
}

function clearLog() {
    const logContainer = document.getElementById('activityLog');
    logContainer.innerHTML = '<div class="log-entry">Log cleared</div>';
    logEntries = [];
    errorCount = 0;
    updateLogStats();
}

function updateLogStats() {
    // Count errors
    errorCount = logEntries.filter(log =>
        log.level === 'error' || log.level === 'ERROR' || log.message.toLowerCase().includes('error')
    ).length;

    document.getElementById('logCount').textContent = `${logEntries.length} entries`;
    document.getElementById('errorCount').textContent = `${errorCount} errors`;
}

// Enhanced addLog function with better categorization
function addLog(message, type = '') {
    const logContainer = document.getElementById('activityLog');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');

    // Determine log type
    let logClass = type;
    if (!logClass) {
        if (message.toLowerCase().includes('error') || message.toLowerCase().includes('failed')) {
            logClass = 'error';
        } else if (message.toLowerCase().includes('success') || message.toLowerCase().includes('started')) {
            logClass = 'success';
        } else if (message.toLowerCase().includes('warning')) {
            logClass = 'warning';
        }
    }

    logEntry.className = 'log-entry ' + logClass;
    logEntry.innerHTML = `
        <span class="log-time">[${timestamp}]</span>
        <span class="log-message">${message}</span>
    `;

    logContainer.insertBefore(logEntry, logContainer.firstChild);

    // Update entries array
    logEntries.unshift({
        timestamp: new Date().toISOString(),
        message: message,
        level: logClass
    });

    // Keep only last 100 entries
    while (logContainer.children.length > 100) {
        logContainer.removeChild(logContainer.lastChild);
    }

    if (logEntries.length > 100) {
        logEntries = logEntries.slice(0, 100);
    }

    updateLogStats();
}

// Periodic updates
setInterval(() => {
    if (socket && socket.connected) {
        socket.emit('request_status');
    }
}, 5000);

// Periodic wallet refresh (every 30 seconds)
setInterval(() => {
    if (socket && socket.connected) {
        loadWalletDetails();
    }
}, 30000);
