/**
 * Server-Sent Events (SSE) client for real-time updates
 */

class SSEClient {
    constructor(apiBaseUrl) {
        this.apiBaseUrl = apiBaseUrl;
        this.eventSource = null;
        this.listeners = {};
        this.reconnectDelay = 3000;
        this.maxReconnectDelay = 30000;
        this.reconnectAttempts = 0;
    }

    connect() {
        if (this.eventSource) {
            console.log('SSE already connected');
            return;
        }

        console.log('Connecting to SSE endpoint...');
        this.eventSource = new EventSource(`${this.apiBaseUrl}/events`);

        this.eventSource.onopen = () => {
            console.log('SSE connection established');
            this.reconnectAttempts = 0;
            this.reconnectDelay = 3000;
        };

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleEvent(data);
            } catch (error) {
                console.error('Error parsing SSE message:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.eventSource.close();
            this.eventSource = null;
            this.scheduleReconnect();
        };
    }

    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(
            this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    handleEvent(event) {
        console.log('SSE event received:', event.type, event.data);

        // Trigger event-specific listeners
        if (this.listeners[event.type]) {
            this.listeners[event.type].forEach(callback => {
                callback(event.data);
            });
        }

        // Trigger generic listeners
        if (this.listeners['*']) {
            this.listeners['*'].forEach(callback => {
                callback(event);
            });
        }
    }

    on(eventType, callback) {
        if (!this.listeners[eventType]) {
            this.listeners[eventType] = [];
        }
        this.listeners[eventType].push(callback);
    }

    off(eventType, callback) {
        if (this.listeners[eventType]) {
            this.listeners[eventType] = this.listeners[eventType].filter(
                cb => cb !== callback
            );
        }
    }

    disconnect() {
        if (this.eventSource) {
            console.log('Disconnecting from SSE');
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Create global SSE client instance
const sseClient = new SSEClient('/api');

// Auto-connect when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        sseClient.connect();
    });
} else {
    sseClient.connect();
}

// Disconnect when page is unloaded
window.addEventListener('beforeunload', () => {
    sseClient.disconnect();
});
