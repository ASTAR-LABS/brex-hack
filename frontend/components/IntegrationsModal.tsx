"use client";

import { useState, useEffect } from "react";
import { Settings, Github, Calendar, Database, FileText, Check, Loader2, AlertCircle } from "lucide-react";
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

type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

export function IntegrationsModal() {
  const [open, setOpen] = useState(false);
  const [connectionStates, setConnectionStates] = useState<Record<string, ConnectionState>>({});
  const [showGitHubForm, setShowGitHubForm] = useState(false);
  const [githubToken, setGithubToken] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [error, setError] = useState("");

  // Check for existing session on mount
  useEffect(() => {
    const sessionToken = getSessionToken();
    const repo = localStorage.getItem('github_repo');
    
    if (sessionToken && repo) {
      setConnectionStates(prev => ({ ...prev, github: "connected" }));
      setGithubRepo(repo);
    }
  }, []);

  const handleGitHubConnect = async () => {
    if (!githubToken || !githubRepo) {
      setError("Please fill in both fields");
      return;
    }

    // Parse owner/repo format
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
      <DialogContent className="max-w-2xl bg-gray-950 border-gray-700 backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-light text-white">Integrations</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6 mt-6">
          {/* GitHub Integration */}
          <div className={`
            p-5 rounded-xl transition-all duration-200
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
                <h3 className="font-semibold text-white text-lg">GitHub</h3>
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

          {/* Other integrations (disabled for now) */}
          <div className="space-y-3 opacity-50">
            {[
              { name: "Google Calendar", icon: Calendar, description: "Coming soon" },
              { name: "File System", icon: FileText, description: "Coming soon" },
              { name: "PostgreSQL", icon: Database, description: "Coming soon" },
            ].map((integration) => {
              const Icon = integration.icon;
              return (
                <div
                  key={integration.name}
                  className="flex items-center gap-4 p-5 rounded-xl bg-gray-800/40 border border-gray-700"
                >
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gray-700/50">
                    <Icon className="w-6 h-6 text-gray-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-400 text-lg">{integration.name}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">{integration.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}