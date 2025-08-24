"use client";

import { useState, useEffect } from "react";
import { CheckCircle, Loader2, AlertCircle, Github, Calculator, ExternalLink } from "lucide-react";
import { websocketManager, type WebSocketMessage } from "@/lib/websocket-manager";

interface Action {
  id: string;
  type: string;
  description: string;
  status: 'pending' | 'executing' | 'completed' | 'error';
  timestamp: string;
  result?: any;
  error?: string;
}

export function ActionsPanel() {
  const [actions, setActions] = useState<Action[]>([]);
  const [agentMessages, setAgentMessages] = useState<string[]>([]);

  useEffect(() => {
    // Listen for WebSocket messages
    const unsubscribe = websocketManager.addMessageListener((message: WebSocketMessage) => {
      // Handle actions extracted
      if (message.type === 'actions_extracted' && message.actions) {
        const newActions = message.actions.map((action: any) => ({
          id: `${Date.now()}-${Math.random()}`,
          type: action.type,
          description: action.description,
          status: 'pending' as const,
          timestamp: new Date().toISOString(),
        }));
        setActions(prev => [...newActions, ...prev].slice(0, 10)); // Keep last 10
      }

      // Handle agent responses
      if (message.type === 'agent_response') {
        if (message.message) {
          setAgentMessages(prev => [message.message, ...prev].slice(0, 5)); // Keep last 5
        }
        // Update action status based on tools used
        if (message.tools_used && message.tools_used.length > 0) {
          setActions(prev => prev.map(action => {
            if (action.status === 'pending') {
              return { ...action, status: 'completed' };
            }
            return action;
          }));
        }
      }

      // Handle action execution
      if (message.type === 'action_executed') {
        setActions(prev => prev.map(action => {
          if (action.status === 'pending' || action.status === 'executing') {
            return { 
              ...action, 
              status: 'completed',
              result: message.result 
            };
          }
          return action;
        }));
      }

      // Handle errors
      if (message.type === 'action_error') {
        setActions(prev => prev.map(action => {
          if (action.status === 'pending' || action.status === 'executing') {
            return { 
              ...action, 
              status: 'error',
              error: message.message 
            };
          }
          return action;
        }));
      }
    });

    return () => unsubscribe();
  }, []);

  const getStatusIcon = (status: Action['status']) => {
    switch (status) {
      case 'pending':
        return <Loader2 className="w-4 h-4 text-gray-400 animate-pulse" />;
      case 'executing':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getActionIcon = (type: string) => {
    if (type.toLowerCase().includes('github')) {
      return <Github className="w-4 h-4" />;
    }
    return <Calculator className="w-4 h-4" />;
  };

  if (actions.length === 0 && agentMessages.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-8 right-8 w-96 max-h-[500px] bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 bg-gray-800/50">
        <h3 className="text-sm font-medium text-white">AI Agent Activity</h3>
      </div>

      {/* Content */}
      <div className="overflow-y-auto max-h-[400px]">
        {/* Agent Messages */}
        {agentMessages.length > 0 && (
          <div className="p-4 border-b border-gray-700">
            <div className="space-y-2">
              {agentMessages.map((message, i) => (
                <div 
                  key={i} 
                  className={`text-sm text-gray-300 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 ${
                    i === 0 ? 'animate-slide-in' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-blue-400">🤖</span>
                    <span className="flex-1">{message}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        {actions.length > 0 && (
          <div className="p-4">
            <div className="space-y-2">
              {actions.map((action) => (
                <div 
                  key={action.id} 
                  className={`flex items-start gap-3 p-3 rounded-lg transition-all ${
                    action.status === 'completed' 
                      ? 'bg-green-500/10 border border-green-500/20' 
                      : action.status === 'error'
                      ? 'bg-red-500/10 border border-red-500/20'
                      : 'bg-gray-800/50 border border-gray-700'
                  }`}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getActionIcon(action.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-400">
                        {action.type.replace(/_/g, ' ')}
                      </span>
                      {getStatusIcon(action.status)}
                    </div>
                    <p className="text-sm text-white break-words">
                      {action.description}
                    </p>
                    
                    {/* Show result link for GitHub actions */}
                    {action.status === 'completed' && action.result?.issue_url && (
                      <a 
                        href={action.result.issue_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-xs text-blue-400 hover:text-blue-300"
                      >
                        View on GitHub
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    
                    {/* Show error */}
                    {action.status === 'error' && action.error && (
                      <p className="text-xs text-red-400 mt-1">
                        {action.error}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes slide-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}