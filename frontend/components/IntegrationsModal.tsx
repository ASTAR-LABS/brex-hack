"use client";

import { useState } from "react";
import { Settings, Github, Calendar, Database, FileText, Check, Loader2, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

const integrations = [
  {
    id: "github",
    name: "GitHub",
    description: "Access repositories and issues",
    icon: Github,
    type: "oauth",
    connected: false,
  },
  {
    id: "calendar",
    name: "Google Calendar",
    description: "Manage events and schedules",
    icon: Calendar,
    type: "oauth",
    connected: false,
  },
  {
    id: "filesystem",
    name: "File System",
    description: "Access local files and folders",
    icon: FileText,
    type: "mcp",
    connected: false,
  },
  {
    id: "database",
    name: "PostgreSQL",
    description: "Query and manage databases",
    icon: Database,
    type: "mcp",
    connected: false,
  },
];

type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

export function IntegrationsModal() {
  const [open, setOpen] = useState(false);
  const [connectionStates, setConnectionStates] = useState<Record<string, ConnectionState>>({});

  const handleConnect = async (id: string) => {
    setConnectionStates(prev => ({ ...prev, [id]: "connecting" }));
    
    // Simulate connection process
    setTimeout(() => {
      setConnectionStates(prev => ({ ...prev, [id]: "connected" }));
    }, 1500);
  };

  const handleDisconnect = (id: string) => {
    setConnectionStates(prev => ({ ...prev, [id]: "disconnected" }));
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
      <DialogContent className="max-w-2xl bg-gray-950 border-gray-700 backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-light text-white">Integrations</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-3 mt-6">
          {integrations.map((integration) => {
            const Icon = integration.icon;
            const state = connectionStates[integration.id] || "disconnected";
            
            return (
              <div
                key={integration.id}
                className={`
                  flex items-center justify-between p-5 rounded-xl transition-all duration-200
                  ${state === "connected" 
                    ? "bg-emerald-500/5 border border-emerald-500/20" 
                    : "bg-gray-800/40 border border-gray-700 hover:bg-gray-800/60"
                  }
                `}
              >
                <div className="flex items-center gap-4">
                  <div className={`
                    w-12 h-12 rounded-xl flex items-center justify-center transition-colors
                    ${state === "connected" 
                      ? "bg-emerald-500/10" 
                      : "bg-gray-700/50"
                    }
                  `}>
                    <Icon className={`
                      w-6 h-6 transition-colors
                      ${state === "connected" 
                        ? "text-emerald-400" 
                        : "text-gray-300"
                      }
                    `} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white text-lg">{integration.name}</h3>
                    <p className="text-sm text-gray-400 mt-0.5">{integration.description}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  {state === "connected" && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-full">
                      <Check className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm text-emerald-400 font-medium">Connected</span>
                    </div>
                  )}
                  {state === "connecting" && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 rounded-full">
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                      <span className="text-sm text-blue-400 font-medium">Connecting...</span>
                    </div>
                  )}
                  {state === "error" && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 rounded-full">
                      <AlertCircle className="w-4 h-4 text-red-400" />
                      <span className="text-sm text-red-400 font-medium">Error</span>
                    </div>
                  )}
                  
                  <Button
                    onClick={() => state === "connected" ? handleDisconnect(integration.id) : handleConnect(integration.id)}
                    disabled={state === "connecting"}
                    variant={state === "connected" ? "outline" : "default"}
                    size="sm"
                    className={
                      state === "connected" 
                        ? "border-gray-600 hover:bg-gray-800 hover:border-red-500/50 hover:text-red-400" 
                        : "bg-white hover:bg-gray-200 text-black"
                    }
                  >
                    {state === "connected" ? "Disconnect" : "Connect"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}