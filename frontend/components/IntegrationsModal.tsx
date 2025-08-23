"use client";

import { useState, useEffect } from "react";
import { Settings, Github, Calendar, Database, FileText, Check, Loader2, AlertCircle, Slack, HardDrive, Cloud, ListTodo, Bug, Puzzle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { connectGitHub, getSessionToken, setSessionToken } from "@/lib/api";
import { getMCPStatus, testMCPConnection, type MCPStatus } from "@/lib/mcp";

type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

// Icon mapping for MCP servers
const iconMap: Record<string, any> = {
  github: Github,
  google_calendar: Calendar,
  slack: Slack,
  filesystem: FileText,
  postgres: Database,
  notion: FileText,
  google_drive: Cloud,
  linear: ListTodo,
  jira: Bug,
  custom_api: Puzzle,
};

export function IntegrationsModal() {
  const [open, setOpen] = useState(false);
  const [mcpStatus, setMCPStatus] = useState<MCPStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingMCP, setTestingMCP] = useState<string | null>(null);
  
  // Legacy GitHub form state (for backward compatibility)
  const [connectionStates, setConnectionStates] = useState<Record<string, ConnectionState>>({});
  const [showGitHubForm, setShowGitHubForm] = useState(false);
  const [githubToken, setGithubToken] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [error, setError] = useState("");

  // Fetch MCP status on mount and when dialog opens
  useEffect(() => {
    if (open) {
      fetchMCPStatus();
    }
    
    // Check for existing session (legacy)
    const sessionToken = getSessionToken();
    const repo = localStorage.getItem('github_repo');
    
    if (sessionToken && repo) {
      setConnectionStates(prev => ({ ...prev, github: "connected" }));
      setGithubRepo(repo);
    }
  }, [open]);

  const fetchMCPStatus = async () => {
    try {
      setLoading(true);
      const status = await getMCPStatus();
      setMCPStatus(status);
    } catch (err) {
      console.error("Failed to fetch MCP status:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestMCP = async (mcpName: string) => {
    try {
      setTestingMCP(mcpName);
      const result = await testMCPConnection(mcpName);
      
      // Show result in alert for now (could be improved with toast)
      if (result.status === "connected") {
        alert(`✅ ${mcpName} connected!\nTools available: ${result.tools_count}\n${result.tools?.join(', ')}`);
      } else if (result.status === "disabled") {
        alert(`⚠️ ${mcpName} is disabled.\n${result.message}`);
      } else if (result.status === "not_configured") {
        alert(`❌ ${mcpName} not configured.\nMissing: ${result.missing_vars?.join(', ')}`);
      } else {
        alert(`❌ ${mcpName} error: ${result.message}`);
      }
      
      // Refresh status
      await fetchMCPStatus();
    } catch (err) {
      alert(`Failed to test ${mcpName}`);
    } finally {
      setTestingMCP(null);
    }
  };

  // Legacy GitHub connection (for backward compatibility)
  const handleGitHubConnect = async () => {
    if (!githubToken || !githubRepo) {
      setError("Please fill in both fields");
      return;
    }

    const parts = githubRepo.split('/');
    if (parts.length !== 2) {
      setError("Repository must be in format: owner/repo");
      return;
    }

    const [owner, repo] = parts;

    setError("");
    setConnectionStates(prev => ({ ...prev, github: "connecting" }));
    
    try {
      const { session_token } = await connectGitHub(githubToken, owner, repo);
      
      setSessionToken(session_token);
      localStorage.setItem('github_repo', githubRepo);
      
      setConnectionStates(prev => ({ ...prev, github: "connected" }));
      setGithubToken(""); // Clear token for security
      setShowGitHubForm(false);
    } catch (err) {
      setError("Failed to connect to GitHub");
      setConnectionStates(prev => ({ ...prev, github: "error" }));
    }
  };

  const handleDisconnect = () => {
    localStorage.removeItem('session_token');
    localStorage.removeItem('github_repo');
    setConnectionStates(prev => ({ ...prev, github: "disconnected" }));
    setGithubRepo("");
    setGithubToken("");
    setShowGitHubForm(false);
  };

  const githubState = connectionStates.github || "disconnected";

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="fixed top-8 right-8 z-50 bg-gray-900/30 border border-gray-800 hover:bg-gray-900/50 backdrop-blur-sm"
        >
          <Settings className="h-5 w-5" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto bg-gray-950 border-gray-700 backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-light text-white">Integrations</DialogTitle>
          {mcpStatus && (
            <p className="text-sm text-gray-400 mt-2">
              {mcpStatus.enabled} of {mcpStatus.total} integrations enabled
            </p>
          )}
        </DialogHeader>
        
        <div className="space-y-4 mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-400">Loading integrations...</span>
            </div>
          ) : (
            <>
              {/* MCP Servers */}
              {mcpStatus?.servers.map((server) => {
                const Icon = iconMap[server.name] || Puzzle;
                const isEnabled = server.enabled;
                const isConfigured = server.configured;
                const isConnected = isEnabled && isConfigured;
                
                return (
                  <div
                    key={server.name}
                    className={`
                      p-4 rounded-xl transition-all duration-200
                      ${isConnected 
                        ? "bg-emerald-500/5 border border-emerald-500/20" 
                        : isEnabled
                        ? "bg-yellow-500/5 border border-yellow-500/20"
                        : "bg-gray-800/40 border border-gray-700"
                      }
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`
                        w-12 h-12 rounded-xl flex items-center justify-center transition-colors
                        ${isConnected 
                          ? "bg-emerald-500/10" 
                          : isEnabled
                          ? "bg-yellow-500/10"
                          : "bg-gray-700/50"
                        }
                      `}>
                        <Icon className={`
                          w-6 h-6 transition-colors
                          ${isConnected 
                            ? "text-emerald-400" 
                            : isEnabled
                            ? "text-yellow-400"
                            : "text-gray-400"
                          }
                        `} />
                      </div>
                      
                      <div className="flex-1">
                        <h3 className="font-semibold text-white text-lg">
                          {server.display_name}
                        </h3>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {server.capabilities.slice(0, 3).join(" • ")}
                          {server.capabilities.length > 3 && ` • +${server.capabilities.length - 3} more`}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {isConnected && (
                          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-full">
                            <Check className="w-4 h-4 text-emerald-400" />
                            <span className="text-sm text-emerald-400 font-medium">Ready</span>
                          </div>
                        )}
                        
                        {isEnabled && !isConfigured && (
                          <div className="flex flex-col items-end gap-1">
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 rounded-full">
                              <AlertCircle className="w-4 h-4 text-yellow-400" />
                              <span className="text-sm text-yellow-400 font-medium">Missing Config</span>
                            </div>
                            {server.missing_vars && (
                              <span className="text-xs text-gray-500">
                                Missing: {server.missing_vars.join(", ")}
                              </span>
                            )}
                          </div>
                        )}
                        
                        {!isEnabled && (
                          <span className="text-sm text-gray-500">Disabled</span>
                        )}
                        
                        <Button
                          onClick={() => handleTestMCP(server.name)}
                          disabled={testingMCP === server.name}
                          size="sm"
                          variant="outline"
                          className="ml-2"
                        >
                          {testingMCP === server.name ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            "Test"
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
              
              {/* Legacy GitHub Integration (if not using GitHub MCP) */}
              {!mcpStatus?.servers.find(s => s.name === 'github')?.enabled && (
                <div className="border-t border-gray-800 pt-4 mt-6">
                  <p className="text-sm text-gray-500 mb-4">Legacy Integration (Use GitHub MCP instead)</p>
                  <div className={`
                    p-4 rounded-xl transition-all duration-200
                    ${githubState === "connected" 
                      ? "bg-emerald-500/5 border border-emerald-500/20" 
                      : "bg-gray-800/40 border border-gray-700"
                    }
                  `}>
                    <div className="flex items-center gap-4 mb-4">
                      <div className={`
                        w-12 h-12 rounded-xl flex items-center justify-center transition-colors
                        ${githubState === "connected" 
                          ? "bg-emerald-500/10" 
                          : "bg-gray-700/50"
                        }
                      `}>
                        <Github className={`
                          w-6 h-6 transition-colors
                          ${githubState === "connected" 
                            ? "text-emerald-400" 
                            : "text-gray-300"
                          }
                        `} />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-white text-lg">GitHub (Legacy)</h3>
                        <p className="text-sm text-gray-400 mt-0.5">
                          {githubState === "connected" ? `Connected to ${githubRepo}` : "Connect to create issues and PRs"}
                        </p>
                      </div>
                      {githubState === "connected" && (
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-full">
                          <Check className="w-4 h-4 text-emerald-400" />
                          <span className="text-sm text-emerald-400 font-medium">Connected</span>
                        </div>
                      )}
                    </div>

                    {showGitHubForm && githubState !== "connected" && (
                      <div className="space-y-3 mb-4">
                        <div>
                          <Label htmlFor="token" className="text-sm text-gray-300">Personal Access Token</Label>
                          <Input
                            id="token"
                            type="password"
                            placeholder="ghp_xxxxxxxxxxxx"
                            value={githubToken}
                            onChange={(e) => setGithubToken(e.target.value)}
                            className="mt-1 bg-gray-900/50 border-gray-700 text-white"
                          />
                          <a 
                            href="https://github.com/settings/tokens/new?description=Voice%20Transcription%20App&scopes=repo" 
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mt-1.5"
                          >
                            Generate a new token on GitHub →
                          </a>
                        </div>
                        
                        <div>
                          <Label htmlFor="repo" className="text-sm text-gray-300">Repository</Label>
                          <Input
                            id="repo"
                            placeholder="owner/repo"
                            value={githubRepo}
                            onChange={(e) => setGithubRepo(e.target.value)}
                            className="mt-1 bg-gray-900/50 border-gray-700 text-white"
                          />
                        </div>

                        {error && (
                          <div className="p-2 bg-red-500/10 border border-red-500/20 rounded">
                            <p className="text-sm text-red-400">{error}</p>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button
                            onClick={handleGitHubConnect}
                            disabled={githubState === "connecting" || !githubToken || !githubRepo}
                            size="sm"
                            className="flex-1"
                          >
                            {githubState === "connecting" ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Connecting...
                              </>
                            ) : (
                              "Save"
                            )}
                          </Button>
                          <Button
                            onClick={() => {
                              setShowGitHubForm(false);
                              setError("");
                              setGithubToken("");
                              setGithubRepo("");
                            }}
                            variant="outline"
                            size="sm"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}

                    {!showGitHubForm && (
                      <div className="flex gap-2">
                        {githubState === "connected" ? (
                          <Button
                            onClick={handleDisconnect}
                            variant="outline"
                            size="sm"
                            className="hover:bg-red-500/10 hover:text-red-400 hover:border-red-400/50"
                          >
                            Disconnect
                          </Button>
                        ) : (
                          <Button
                            onClick={() => setShowGitHubForm(true)}
                            size="sm"
                          >
                            Connect
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Configuration Help */}
              <div className="mt-6 p-4 bg-gray-800/30 rounded-lg border border-gray-700">
                <h4 className="text-sm font-semibold text-gray-300 mb-2">Configuration Help</h4>
                <p className="text-xs text-gray-400 mb-2">
                  To enable MCP integrations, add environment variables to your backend .env file:
                </p>
                <pre className="text-xs bg-gray-900/50 p-2 rounded overflow-x-auto">
                  <code>{`# Example for Google Calendar
ENABLE_GOOGLE_CALENDAR_MCP=true
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_secret

# See MCP_INTEGRATION_GUIDE.md for details`}</code>
                </pre>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}