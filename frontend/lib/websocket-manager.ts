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
  type: 'session_started' | 'session_resumed' | 'session_paused';
  session_id: string;
  timestamp: string;
  is_resumed?: boolean;
  transcript?: string[];
  can_resume?: boolean;
  resume_timeout_minutes?: number;
  final_transcript?: string;
}

export interface WebSocketMessage {
  type: string;
  session_id?: string;
  text?: string;
  is_final?: boolean;
  timestamp?: string;
  full_transcript?: string;
  [key: string]: unknown;
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
  private pausedSessionId: string | null = null;

  private constructor() {
    // Check for paused session in localStorage on initialization
    if (typeof window !== 'undefined') {
      const storedSessionId = localStorage.getItem('pausedSessionId');
      if (storedSessionId) {
        this.pausedSessionId = storedSessionId;
      }
    }
  }

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
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/audio';
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        this.updateStatus('connected');
        this.reconnectAttempts = 0;
        
        // Get session token from localStorage
        const sessionToken = localStorage.getItem('session_token');
        
        // Send init message with session_id and session_token
        if (this.pausedSessionId) {
          this.send(JSON.stringify({
            type: 'init',
            session_id: this.pausedSessionId,
            session_token: sessionToken
          }));
        } else {
          // Send init without session_id for new session
          this.send(JSON.stringify({
            type: 'init',
            session_token: sessionToken
          }));
        }
        
        resolve();
      };

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        // Handle session start
        if (data.type === 'session_started' || data.type === 'session_resumed') {
          this.sessionId = data.session_id;
          this.pausedSessionId = null; // Clear paused session as it's now active
          
          // Update query cache with session info
          this.queryClient?.setQueryData(['session'], {
            id: data.session_id,
            startedAt: data.timestamp,
            status: 'active',
            isResumed: data.is_resumed || false
          });
          
          // If resumed, restore transcript
          if (data.is_resumed && data.transcript) {
            this.queryClient?.setQueryData(['transcription'], data.transcript);
          }
        }
        
        // Handle session pause
        if (data.type === 'session_paused') {
          console.log('Session paused:', data.session_id);
          this.pausedSessionId = data.session_id; // Store for resuming
          this.sessionId = null;
          
          // Update query cache
          this.queryClient?.setQueryData(['session'], {
            id: data.session_id,
            status: 'paused',
            canResume: data.can_resume,
            resumeTimeoutMinutes: data.resume_timeout_minutes
          });
          
          // Store session ID in localStorage for persistence
          if (data.can_resume) {
            localStorage.setItem('pausedSessionId', data.session_id);
          }
        }
        
        // Handle session end (final removal)
        if (data.type === 'session_ended') {
          console.log('Session ended:', data.session_id);
          this.sessionId = null;
          this.pausedSessionId = null;
          localStorage.removeItem('pausedSessionId');
          // Update query cache
          this.queryClient?.setQueryData(['session'], null);
        }
        
        // Handle transcription
        if (data.type === 'transcription' && data.is_final) {
          // Update transcription in query cache
          this.queryClient?.setQueryData(['transcription'], (old: string[] = []) => {
            const words = data.text.trim().split(' ').filter((word: string) => word.length > 0);
            return [...old, ...words];
          });
        }
        
        // Handle action extraction
        if (data.type === 'actions_extracted') {
          console.log('Actions extracted:', data.actions);
        }
        
        // Handle agent response
        if (data.type === 'agent_response') {
          console.log('Agent response:', data.message);
          console.log('Tools used:', data.tools_used);
          // No alert needed - ActionsPanel will show this
        }
        
        // Handle action execution (for backward compatibility)
        if (data.type === 'action_executed') {
          const action = data.action;
          const result = data.result;
          console.log(`✅ Action executed: ${action}`);
          // No alert needed - ActionsPanel will show this
        }
        
        // Handle action errors
        if (data.type === 'action_error') {
          console.error('Action error:', data.message);
          // No alert needed - ActionsPanel will show this
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

  sendCommand(command: string, payload?: Record<string, unknown>) {
    this.send(JSON.stringify({ command, ...payload }));
  }

  addMessageListener(listener: (message: WebSocketMessage) => void) {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  addStatusListener(listener: (status: WebSocketStatus) => void) {
    this.statusListeners.add(listener);
    listener(this.status); // Send current status immediately
    return () => {
      this.statusListeners.delete(listener);
    };
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
  
  getPausedSessionId(): string | null {
    return this.pausedSessionId;
  }
  
  clearPausedSession() {
    this.pausedSessionId = null;
    localStorage.removeItem('pausedSessionId');
  }

  isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }
}

export const websocketManager = WebSocketManager.getInstance();