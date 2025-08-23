const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Action {
  id: string;
  type: string;
  description: string;
  confidence: number;
}

export interface ActionStatus {
  id: string;
  state: 'extracted' | 'queued' | 'executing' | 'resolved' | 'failed';
  type: string;
  description: string;
  error?: string;
  result?: any;
  created_at?: string;
  executed_at?: string;
  resolved_at?: string;
}

export async function connectGitHub(token: string, owner: string, repo: string): Promise<{ session_token: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/actions/integrations/connect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      github_token: token,
      github_owner: owner,
      github_repo: repo,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to connect GitHub');
  }

  return response.json();
}

export async function extractActions(text: string): Promise<{ actions: Action[], error?: string }> {
  const sessionToken = getSessionToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/actions/extract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(sessionToken && { 'X-Session-Token': sessionToken }),
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error('Failed to extract actions');
  }

  return response.json();
}

export async function executeAction(actionId: string): Promise<ActionStatus> {
  const sessionToken = getSessionToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/actions/execute/${actionId}`, {
    method: 'POST',
    headers: {
      ...(sessionToken && { 'X-Session-Token': sessionToken }),
    },
  });

  if (!response.ok) {
    throw new Error('Failed to execute action');
  }

  return response.json();
}

export async function getSessionActions(): Promise<{ actions: ActionStatus[] }> {
  const sessionToken = getSessionToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/actions/session`, {
    method: 'GET',
    headers: {
      ...(sessionToken && { 'X-Session-Token': sessionToken }),
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get session actions');
  }

  return response.json();
}

export async function getActionStatus(actionId: string): Promise<ActionStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/actions/status/${actionId}`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error('Failed to get action status');
  }

  return response.json();
}

export async function checkSession(sessionToken: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/actions/integrations/check`, {
      method: 'GET',
      headers: {
        'X-Session-Token': sessionToken,
      },
    });
    return response.ok;
  } catch {
    return false;
  }
}

export function getSessionToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('session_token');
}

export function setSessionToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('session_token', token);
}

export function clearSessionToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('session_token');
  localStorage.removeItem('github_repo');
}