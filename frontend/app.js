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
    document.getElementById('refreshPositionBtn').addEventListener('click', refreshPosition);
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
            document.getElementById('configTradeDirection').value = config.trading.trade_direction || 'long';

            // Update display
            document.getElementById('buyLevel').textContent = '$' + (config.trading.buy_level || 138).toFixed(2);
            document.getElementById('sellLevel').textContent = '$' + (config.trading.sell_level || 143).toFixed(2);
        }

        if (config.safety) {
            document.getElementById('configMaxLoss').value = config.safety.max_cumulative_loss || -50;
            document.getElementById('configStopLoss').value = config.safety.stop_loss_percentage || 5;
            document.getElementById('configSupportLevel').value = config.safety.support_level || 120;
            document.getElementById('configResistanceLevel').value = config.safety.resistance_level || 160;
            document.getElementById('configTradingRangeMin').value = config.safety.trading_range_min || 100;
            document.getElementById('configTradingRangeMax').value = config.safety.trading_range_max || 180;
        }

        addLog('Configuration loaded');
    } catch (error) {
        addLog('Error loading configuration: ' + error.message, 'error');
    }
}

function validateConfiguration(config) {
    const errors = [];

    // Validate trading configuration
    if (config.trading.position_size <= 0) {
        errors.push('Position size must be greater than 0');
    }
    if (config.trading.leverage < 1 || config.trading.leverage > 100) {
        errors.push('Leverage must be between 1 and 100');
    }
    if (config.trading.buy_level <= 0) {
        errors.push('Buy level must be greater than 0');
    }
    if (config.trading.sell_level <= 0) {
        errors.push('Sell level must be greater than 0');
    }
    if (config.trading.buy_level >= config.trading.sell_level) {
        errors.push('Buy level must be less than sell level');
    }

    // Validate safety configuration
    if (config.safety.max_cumulative_loss >= 0) {
        errors.push('Max cumulative loss must be negative (e.g., -50 for $50 max loss)');
    }
    if (config.safety.stop_loss_percentage <= 0 || config.safety.stop_loss_percentage > 100) {
        errors.push('Stop loss percentage must be between 0 and 100');
    }
    if (config.safety.trading_range_min >= config.safety.trading_range_max) {
        errors.push('Trading range min must be less than trading range max');
    }
    if (config.safety.support_level >= config.safety.resistance_level) {
        errors.push('Support level must be less than resistance level');
    }

    return {
        valid: errors.length === 0,
        errors: errors
    };
}

async function saveConfiguration() {
    try {
        const config = {
            trading: {
                market: document.getElementById('configMarket').value,
                position_size: parseFloat(document.getElementById('configPositionSize').value),
                leverage: parseInt(document.getElementById('configLeverage').value),
                buy_level: parseFloat(document.getElementById('configBuyLevel').value),
                sell_level: parseFloat(document.getElementById('configSellLevel').value),
                order_type: "market",
                trade_direction: document.getElementById('configTradeDirection').value
            },
            safety: {
                max_cumulative_loss: parseFloat(document.getElementById('configMaxLoss').value),
                stop_loss_percentage: parseFloat(document.getElementById('configStopLoss').value),
                support_level: parseFloat(document.getElementById('configSupportLevel').value),
                resistance_level: parseFloat(document.getElementById('configResistanceLevel').value),
                trading_range_min: parseFloat(document.getElementById('configTradingRangeMin').value),
                trading_range_max: parseFloat(document.getElementById('configTradingRangeMax').value)
            }
        };

        // Validate configuration
        const validation = validateConfiguration(config);
        if (!validation.valid) {
            addLog('Configuration validation failed: ' + validation.errors.join(', '), 'error');
            return;
        }

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
        statusEl.innerHTML = '<span class="status-dot w-3 h-3 rounded-full bg-green-500"></span><span class="text-sm">Connected</span>';
    } else {
        statusEl.innerHTML = '<span class="status-dot w-3 h-3 rounded-full bg-red-500 animate-pulse-dot"></span><span class="text-sm">Disconnected</span>';
    }
}

function updateBotStatus(status) {
    // Update state indicator
    const statusEl = document.getElementById('botStatus');
    const state = status.state || 'stopped';

    let statusText = state.charAt(0).toUpperCase() + state.slice(1);
    let dotColor = state === 'running' ? 'bg-green-500' : state === 'paused' ? 'bg-yellow-500' : 'bg-red-500';

    // Add error message if present
    let errorHTML = '';
    if (state === 'error' && status.error) {
        errorHTML = `<div class="mt-2 p-2 bg-red-900/50 border border-red-700 rounded text-sm text-red-200">${status.error}</div>`;
        addLog('Bot Error: ' + status.error, 'error');
    }

    statusEl.innerHTML = `
        <div class="flex items-center gap-3 p-4 bg-gray-700 rounded-lg">
            <span class="status-dot w-4 h-4 rounded-full ${dotColor}"></span>
            <span class="status-text text-lg font-medium">${statusText}</span>
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
    pnlEl.className = 'text-2xl font-bold ' + (pnl >= 0 ? 'text-green-400' : 'text-red-400');

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
        positionContent.innerHTML = '<div class="text-gray-400 text-center py-4">No active position</div>';
        return;
    }

    const pnlColor = position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400';
    const sideColor = position.side === 'buy' ? 'text-green-400' : 'text-red-400';

    positionContent.innerHTML = `
        <div class="grid grid-cols-2 gap-4">
            <div class="p-3 bg-gray-700 rounded-lg">
                <div class="text-xs text-gray-400 mb-1">Side</div>
                <div class="font-semibold ${sideColor}">${position.side.toUpperCase()}</div>
            </div>
            <div class="p-3 bg-gray-700 rounded-lg">
                <div class="text-xs text-gray-400 mb-1">Size</div>
                <div class="font-semibold">${position.size} SOL</div>
            </div>
            <div class="p-3 bg-gray-700 rounded-lg">
                <div class="text-xs text-gray-400 mb-1">Entry Price</div>
                <div class="font-semibold">$${position.entry_price.toFixed(2)}</div>
            </div>
            <div class="p-3 bg-gray-700 rounded-lg">
                <div class="text-xs text-gray-400 mb-1">Unrealized P&L</div>
                <div class="font-semibold ${pnlColor}">$${position.unrealized_pnl.toFixed(2)}</div>
            </div>
        </div>
    `;
}

function updateRecentTrades(trades) {
    const tradesListEl = document.getElementById('tradesList');

    if (!trades || trades.length === 0) {
        tradesListEl.innerHTML = '<div class="text-gray-400 text-center py-4">No trades yet</div>';
        return;
    }

    const tradesHTML = trades.reverse().map(trade => {
        const time = new Date(trade.timestamp).toLocaleTimeString();
        const isEntry = trade.type.includes('ENTRY');
        const profitHTML = trade.profit !== undefined
            ? `<span class="font-semibold ${trade.profit >= 0 ? 'text-green-400' : 'text-red-400'}">
                   ${trade.profit >= 0 ? '+' : ''}$${trade.profit.toFixed(2)}
               </span>`
            : '';

        return `
            <div class="p-3 bg-gray-700 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-medium ${isEntry ? 'text-blue-400' : 'text-yellow-400'}">${trade.type}</span>
                    <span class="text-xs text-gray-400">${time}</span>
                </div>
                <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-300">${trade.quantity} SOL @ $${trade.price.toFixed(2)}</span>
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

    const colorClass = type === 'error' ? 'text-red-400' : type === 'success' ? 'text-green-400' : 'text-gray-300';
    logEntry.className = colorClass;
    logEntry.textContent = `[${timestamp}] ${message}`;

    logContainer.insertBefore(logEntry, logContainer.firstChild);

    // Keep only last 50 entries
    while (logContainer.children.length > 50) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Position Refresh Function
async function refreshPosition() {
    try {
        addLog('Refreshing position data...');

        // Request fresh status from backend which will fetch latest position
        const response = await fetch(`${API_BASE_URL}/api/bot/status`);
        const data = await response.json();

        if (data && !data.error) {
            // Update the position display
            updatePosition(data.position);
            addLog('Position data refreshed', 'success');
        } else {
            addLog('Failed to refresh position: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        addLog('Error refreshing position: ' + error.message, 'error');
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
            let walletHTML = '<div class="space-y-2">';

            // Check if wallet data is an array (new format)
            if (Array.isArray(walletData) && walletData.length > 0) {
                walletData.forEach(item => {
                    const currency = item.currency_short_name || item.currency || item.asset;
                    const balance = parseFloat(item.balance || 0);
                    const locked = parseFloat(item.locked_balance || item.locked || 0);
                    const crossMargin = parseFloat(item.cross_user_margin || 0);

                    if (balance > 0 || locked > 0 || crossMargin > 0) {
                        walletHTML += `
                            <div class="p-3 bg-gray-700 rounded-lg">
                                <div class="font-semibold text-blue-400 mb-1">${currency}</div>
                                <div class="text-sm space-y-1">
                                    <div class="text-gray-300">Balance: <span class="font-medium">${balance}</span></div>
                                    ${locked > 0 ? `<div class="text-yellow-400">Locked: ${locked}</div>` : ''}
                                    ${crossMargin > 0 ? `<div class="text-purple-400">Margin: ${crossMargin}</div>` : ''}
                                </div>
                            </div>
                        `;
                    }
                });
            } else {
                walletHTML += '<div class="text-gray-400 text-center py-4">No balance information available</div>';
            }

            walletHTML += '</div>';
            walletContent.innerHTML = walletHTML;
            addLog('Wallet details loaded', 'success');
        } else {
            walletContent.innerHTML = '<div class="text-red-400 text-center py-4">Failed to load wallet details</div>';
            addLog('Failed to load wallet: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        document.getElementById('walletContent').innerHTML = '<div class="text-red-400 text-center py-4">Error loading wallet</div>';
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

// Periodic updates - Update price every second
setInterval(() => {
    if (socket && socket.connected) {
        socket.emit('request_status');
    }
}, 1000);

// Periodic wallet refresh (every 30 seconds)
setInterval(() => {
    if (socket && socket.connected) {
        loadWalletDetails();
    }
}, 30000);
