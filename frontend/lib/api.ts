const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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