"use client";

import { useState, useEffect } from "react";
import { Settings, Github, Calendar, MessageSquare, Calculator, Check, Loader2, AlertCircle, ExternalLink, LogOut } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { 
  getAgentTools, 
  getGoogleAuthStatus, 
  getGoogleAuthUrl, 
  disconnectGoogleCalendar,
  sendAgentMessage,
  type ToolsResponse,
  type GoogleAuthStatus 
} from "@/lib/agent";

// Icon mapping for tool categories
const iconMap: Record<string, any> = {
  github: Github,
  calendar: Calendar,
  slack: MessageSquare,
  utility: Calculator,
};

// Category color mapping
const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
  github: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/20" },
  calendar: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" },
  slack: { bg: "bg-green-500/10", text: "text-green-400", border: "border-green-500/20" },
  utility: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/20" },
};

export function IntegrationsModal() {
  const [open, setOpen] = useState(false);
  const [tools, setTools] = useState<ToolsResponse | null>(null);
  const [googleAuth, setGoogleAuth] = useState<GoogleAuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingTool, setTestingTool] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  // Fetch tools and auth status when dialog opens
  useEffect(() => {
    if (open) {
      fetchToolsAndStatus();
    }
  }, [open]);

  const fetchToolsAndStatus = async () => {
    try {
      setLoading(true);
      
      // Fetch available tools
      const toolsData = await getAgentTools();
      setTools(toolsData);
      
      // Check Google Calendar auth status
      const authStatus = await getGoogleAuthStatus();
      setGoogleAuth(authStatus);
      
    } catch (err) {
      console.error("Failed to fetch tools and status:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestTool = async (toolName: string, category: string) => {
    try {
      setTestingTool(toolName);
      
      // Test the tool with a simple message
      let testMessage = "";
      if (category === "github") {
        testMessage = "List open issues in the current repository";
      } else if (category === "calendar") {
        testMessage = "Check my calendar for tomorrow";
      } else if (category === "slack") {
        testMessage = "Test Slack connection";
      } else {
        testMessage = "What time is it?";
      }
      
      const result = await sendAgentMessage({
        message: testMessage,
        categories: [category]
      });
      
      if (result.success) {
        alert(`✅ Tool test successful!\n\nResponse: ${result.response}\n\nTools used: ${result.tools_used.join(', ') || 'None'}`);
      } else {
        alert(`❌ Tool test failed: ${result.error}`);
      }
      
    } catch (err) {
      alert(`Failed to test tool: ${err}`);
    } finally {
      setTestingTool(null);
    }
  };

  const handleGoogleAuth = () => {
    // Open Google OAuth in a new window
    const authUrl = getGoogleAuthUrl();
    const authWindow = window.open(authUrl, 'google-auth', 'width=600,height=700');
    
    // Poll for auth completion
    const checkInterval = setInterval(async () => {
      if (authWindow?.closed) {
        clearInterval(checkInterval);
        // Refresh auth status
        const status = await getGoogleAuthStatus();
        setGoogleAuth(status);
      }
    }, 1000);
  };

  const handleGoogleDisconnect = async () => {
    try {
      await disconnectGoogleCalendar();
      const status = await getGoogleAuthStatus();
      setGoogleAuth(status);
    } catch (err) {
      alert(`Failed to disconnect: ${err}`);
    }
  };

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
          <DialogTitle className="text-2xl font-light text-white">AI Agent Tools</DialogTitle>
          {tools && (
            <p className="text-sm text-gray-400 mt-2">
              {tools.total_categories} tool categories available
            </p>
          )}
        </DialogHeader>
        
        <div className="space-y-4 mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-400">Loading tools...</span>
            </div>
          ) : (
            <>
              {/* Google Calendar OAuth Status (Special handling) */}
              {googleAuth && (
                <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 mb-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Calendar className="w-6 h-6 text-blue-400" />
                      <div>
                        <h3 className="font-semibold text-white">Google Calendar</h3>
                        {googleAuth.authenticated ? (
                          <p className="text-sm text-gray-400">
                            Connected as {googleAuth.email}
                          </p>
                        ) : (
                          <p className="text-sm text-gray-400">
                            Connect to manage your calendar
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {googleAuth.authenticated ? (
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-full">
                          <Check className="w-4 h-4 text-emerald-400" />
                          <span className="text-sm text-emerald-400 font-medium">Connected</span>
                        </div>
                        <Button
                          onClick={handleGoogleDisconnect}
                          size="sm"
                          variant="ghost"
                          className="text-gray-400 hover:text-red-400"
                        >
                          <LogOut className="w-4 h-4" />
                        </Button>
                      </div>
                    ) : (
                      <Button
                        onClick={handleGoogleAuth}
                        size="sm"
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Connect
                      </Button>
                    )}
                  </div>
                </div>
              )}
              
              {/* Tool Categories */}
              {tools && Object.entries(tools.categories).map(([categoryKey, category]) => {
                const Icon = iconMap[categoryKey] || Calculator;
                const colors = categoryColors[categoryKey] || { 
                  bg: "bg-gray-500/10", 
                  text: "text-gray-400", 
                  border: "border-gray-500/20" 
                };
                const isExpanded = expandedCategory === categoryKey;
                const toolCount = category.tools.length;
                
                return (
                  <div
                    key={categoryKey}
                    className={`p-4 rounded-xl transition-all duration-200 ${colors.bg} border ${colors.border}`}
                  >
                    <div 
                      className="flex items-center gap-4 cursor-pointer"
                      onClick={() => setExpandedCategory(isExpanded ? null : categoryKey)}
                    >
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colors.bg}`}>
                        <Icon className={`w-6 h-6 ${colors.text}`} />
                      </div>
                      
                      <div className="flex-1">
                        <h3 className="font-semibold text-white text-lg">
                          {category.name}
                        </h3>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {category.description}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <span className={`text-sm ${colors.text} font-medium`}>
                          {toolCount} tools
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={colors.text}
                        >
                          {isExpanded ? "▲" : "▼"}
                        </Button>
                      </div>
                    </div>
                    
                    {/* Expanded Tool List */}
                    {isExpanded && (
                      <div className="mt-4 space-y-2 pl-16">
                        {category.tools.map((tool) => (
                          <div 
                            key={tool.name}
                            className="flex items-center justify-between p-2 rounded-lg bg-gray-900/30"
                          >
                            <div className="flex-1">
                              <p className="text-sm font-medium text-white">
                                {tool.name.replace(/_/g, ' ')}
                              </p>
                              <p className="text-xs text-gray-400 mt-0.5">
                                {tool.description}
                              </p>
                            </div>
                            <Button
                              onClick={() => handleTestTool(tool.name, categoryKey)}
                              disabled={testingTool === tool.name}
                              size="sm"
                              variant="ghost"
                              className={`ml-2 ${colors.text}`}
                            >
                              {testingTool === tool.name ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                "Test"
                              )}
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
              
              {/* Examples Section */}
              <div className="mt-6 p-4 bg-gray-800/30 rounded-lg border border-gray-700">
                <h4 className="text-sm font-semibold text-gray-300 mb-3">Example Commands</h4>
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-gray-500">•</span>
                    <p className="text-xs text-gray-400">
                      "Create a GitHub issue about the bug in the login system"
                    </p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-gray-500">•</span>
                    <p className="text-xs text-gray-400">
                      "Schedule a meeting tomorrow at 2pm for 30 minutes"
                    </p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-gray-500">•</span>
                    <p className="text-xs text-gray-400">
                      "Check my calendar availability for next Tuesday"
                    </p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-gray-500">•</span>
                    <p className="text-xs text-gray-400">
                      "Calculate the hours in a work week"
                    </p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}