const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface MCPServer {
  name: string;
  display_name: string;
  description: string;
  transport: string;
  capabilities: string[];
  enabled: boolean;
  configured: boolean;
}

export interface MCPStatus {
  total: number;
  enabled: number;
  servers: Array<{
    name: string;
    display_name: string;
    enabled: boolean;
    configured: boolean;
    capabilities: string[];
    missing_vars?: string[];
  }>;
}

export async function getMCPStatus(): Promise<MCPStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/status`);
  
  if (!response.ok) {
    throw new Error('Failed to get MCP status');
  }
  
  return response.json();
}

export async function getMCPRegistry(): Promise<{ total: number; servers: MCPServer[] }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/registry`);
  
  if (!response.ok) {
    throw new Error('Failed to get MCP registry');
  }
  
  return response.json();
}

export async function testMCPConnection(mcpName: string): Promise<{
  status: string;
  message: string;
  tools_count?: number;
  tools?: string[];
  missing_vars?: string[];
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/test/${mcpName}`, {
    method: 'POST'
  });
  
  if (!response.ok) {
    throw new Error('Failed to test MCP connection');
  }
  
  return response.json();
}