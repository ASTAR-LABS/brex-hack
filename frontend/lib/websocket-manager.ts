import { QueryClient } from '@tanstack/react-query';

export type WebSocketStatus = 'idle' | 'connecting' | 'connected' | 'error' | 'disconnected';

export interface TranscriptionData {
  type: 'transcription';
  text: string;
  is_final: boolean;
  session_id: string;
  timestamp: string;
  full_transcript: string;
}

export interface SessionData {
  type: 'session_started';
  session_id: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

class WebSocketManager {
  private static instance: WebSocketManager;
  private websocket: WebSocket | null = null;
  private status: WebSocketStatus = 'idle';
  private sessionId: string | null = null;
  private listeners: Set<(message: WebSocketMessage) => void> = new Set();
  private statusListeners: Set<(status: WebSocketStatus) => void> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private queryClient: QueryClient | null = null;

  private constructor() {}

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  setQueryClient(client: QueryClient) {
    this.queryClient = client;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.updateStatus('connecting');
      this.websocket = new WebSocket('ws://localhost:8000/api/v1/ws/audio');

      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        this.updateStatus('connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        // Handle session start
        if (data.type === 'session_started') {
          this.sessionId = data.session_id;
          // Update query cache with session info
          this.queryClient?.setQueryData(['session'], {
            id: data.session_id,
            startedAt: data.timestamp,
            status: 'active'
          });
        }
        
        // Handle transcription
        if (data.type === 'transcription' && data.is_final) {
          // Update transcription in query cache
          this.queryClient?.setQueryData(['transcription'], (old: string[] = []) => {
            const words = data.text.trim().split(' ').filter((word: string) => word.length > 0);
            return [...old, ...words];
          });
        }

        // Notify all listeners
        this.listeners.forEach(listener => listener(data));
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.updateStatus('error');
        reject(error);
      };

      this.websocket.onclose = () => {
        console.log('WebSocket disconnected');
        this.sessionId = null;
        this.updateStatus('disconnected');
        
        // Attempt reconnection
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectTimeout = setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            this.connect();
          }, Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000));
        }
      };
    });
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.updateStatus('idle');
  }

  send(data: ArrayBuffer | string) {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(data);
    } else {
      console.warn('WebSocket not connected, cannot send data');
    }
  }

  sendCommand(command: string, payload?: any) {
    this.send(JSON.stringify({ command, ...payload }));
  }

  addMessageListener(listener: (message: WebSocketMessage) => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  addStatusListener(listener: (status: WebSocketStatus) => void) {
    this.statusListeners.add(listener);
    listener(this.status); // Send current status immediately
    return () => this.statusListeners.delete(listener);
  }

  private updateStatus(status: WebSocketStatus) {
    this.status = status;
    this.statusListeners.forEach(listener => listener(status));
    
    // Update status in query cache
    this.queryClient?.setQueryData(['websocket-status'], status);
  }

  getStatus(): WebSocketStatus {
    return this.status;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }
}

export const websocketManager = WebSocketManager.getInstance();