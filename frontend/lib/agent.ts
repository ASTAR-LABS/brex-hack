// Agent API client for the new LangGraph agent system

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Tool {
  name: string;
  description: string;
}

export interface ToolCategory {
  name: string;
  description: string;
  tools: Tool[];
}

export interface ToolsResponse {
  categories: Record<string, ToolCategory>;
  total_categories: number;
}

export interface ChatRequest {
  message: string;
  categories?: string[];
  model?: string;
  system_prompt?: string;
  session_token?: string;
  user_role?: string;
}

export interface ChatResponse {
  response: string;
  tools_used: string[];
  session_token?: string;
  success: boolean;
  error?: string;
}

export interface GoogleAuthStatus {
  authenticated: boolean;
  email?: string;
  name?: string;
  picture?: string;
  auth_url?: string;
  error?: string;
}

// Get available tools organized by category
export async function getAgentTools(): Promise<ToolsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/tools`);
  if (!response.ok) {
    throw new Error('Failed to fetch agent tools');
  }
  return response.json();
}

// Send a message to the agent
export async function sendAgentMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error('Failed to send message to agent');
  }
  
  return response.json();
}

// Quick chat endpoint for testing
export async function quickChat(message: string): Promise<{ response: string; tools_used: string }> {
  const params = new URLSearchParams({ message });
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/quick?${params}`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to send quick message');
  }
  
  return response.json();
}

// Google Calendar OAuth functions
export async function getGoogleAuthStatus(userId: string = 'default_user'): Promise<GoogleAuthStatus> {
  const params = new URLSearchParams({ user_id: userId });
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/google/status?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to get Google auth status');
  }
  
  return response.json();
}

export function getGoogleAuthUrl(userId: string = 'default_user'): string {
  const params = new URLSearchParams({ user_id: userId });
  return `${API_BASE_URL}/api/v1/auth/google/login?${params}`;
}

export async function disconnectGoogleCalendar(userId: string = 'default_user'): Promise<{ success: boolean; message: string }> {
  const params = new URLSearchParams({ user_id: userId });
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/google/logout?${params}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to disconnect Google Calendar');
  }
  
  return response.json();
}