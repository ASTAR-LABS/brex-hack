"use client";

import { useState, useEffect } from "react";
import { extractActions, executeAction, getActionStatus, type Action, type ActionStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, XCircle, PlayCircle, Clock } from "lucide-react";

export function ActionTracker() {
  const [text, setText] = useState("");
  const [actions, setActions] = useState<Action[]>([]);
  const [actionStatuses, setActionStatuses] = useState<Record<string, ActionStatus>>({});
  const [loading, setLoading] = useState(false);
  const [pollingIds, setPollingIds] = useState<Set<string>>(new Set());

  // Poll for action status
  useEffect(() => {
    if (pollingIds.size === 0) return;

    const interval = setInterval(async () => {
      const newStatuses = { ...actionStatuses };
      const newPollingIds = new Set(pollingIds);

      for (const actionId of pollingIds) {
        try {
          const status = await getActionStatus(actionId);
          newStatuses[actionId] = status;

          // Stop polling if action is resolved or failed
          if (status.state === 'resolved' || status.state === 'failed') {
            newPollingIds.delete(actionId);
          }
        } catch (err) {
          console.error(`Failed to get status for ${actionId}:`, err);
        }
      }

      setActionStatuses(newStatuses);
      setPollingIds(newPollingIds);
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [pollingIds, actionStatuses]);

  const handleExtract = async () => {
    if (!text.trim()) return;

    setLoading(true);
    try {
      const result = await extractActions(text);
      setActions(result.actions);
      
      // Initialize statuses for new actions
      const newStatuses: Record<string, ActionStatus> = {};
      for (const action of result.actions) {
        newStatuses[action.id] = {
          id: action.id,
          type: action.type,
          description: action.description,
          state: 'extracted'
        };
      }
      setActionStatuses(newStatuses);
    } catch (err) {
      console.error('Failed to extract actions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (actionId: string) => {
    try {
      // Start polling
      setPollingIds(prev => new Set([...prev, actionId]));
      
      // Execute action
      const status = await executeAction(actionId);
      setActionStatuses(prev => ({ ...prev, [actionId]: status }));
      
      // If already resolved, stop polling
      if (status.state === 'resolved' || status.state === 'failed') {
        setPollingIds(prev => {
          const newIds = new Set(prev);
          newIds.delete(actionId);
          return newIds;
        });
      }
    } catch (err) {
      console.error('Failed to execute action:', err);
      setPollingIds(prev => {
        const newIds = new Set(prev);
        newIds.delete(actionId);
        return newIds;
      });
    }
  };

  const getStateIcon = (state: ActionStatus['state']) => {
    switch (state) {
      case 'extracted':
        return <Clock className="w-4 h-4 text-gray-400" />;
      case 'queued':
      case 'executing':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getStateColor = (state: ActionStatus['state']) => {
    switch (state) {
      case 'extracted':
        return 'bg-gray-500/10 text-gray-400';
      case 'queued':
      case 'executing':
        return 'bg-blue-500/10 text-blue-400';
      case 'resolved':
        return 'bg-green-500/10 text-green-400';
      case 'failed':
        return 'bg-red-500/10 text-red-400';
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-light mb-6 text-white">Action Tracker</h2>
      
      {/* Input Section */}
      <div className="mb-6">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to extract actions (e.g., 'Create an issue about implementing user authentication')"
          className="w-full p-3 rounded-lg bg-gray-900/50 border border-gray-700 text-white placeholder-gray-400 min-h-[100px]"
        />
        <Button
          onClick={handleExtract}
          disabled={loading || !text.trim()}
          className="mt-3"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Extracting...
            </>
          ) : (
            'Extract Actions'
          )}
        </Button>
      </div>

      {/* Actions List */}
      {actions.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-white mb-3">Extracted Actions</h3>
          {actions.map((action) => {
            const status = actionStatuses[action.id];
            const isExecuting = status?.state === 'executing' || status?.state === 'queued';
            const canExecute = status?.state === 'extracted';
            
            return (
              <div
                key={action.id}
                className="p-4 rounded-lg bg-gray-800/40 border border-gray-700"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-gray-300">
                        {action.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({(action.confidence * 100).toFixed(0)}% confidence)
                      </span>
                      {status && (
                        <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${getStateColor(status.state)}`}>
                          {getStateIcon(status.state)}
                          <span>{status.state}</span>
                        </div>
                      )}
                    </div>
                    <p className="text-white">{action.description}</p>
                    
                    {/* Show result or error */}
                    {status?.state === 'resolved' && status.result && (
                      <div className="mt-3">
                        {status.result.html_url ? (
                          <Button
                            asChild
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <a 
                              href={status.result.html_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                            >
                              View on GitHub →
                            </a>
                          </Button>
                        ) : (
                          <div className="p-2 bg-green-500/10 rounded text-sm text-green-400">
                            ✓ Success
                          </div>
                        )}
                      </div>
                    )}
                    
                    {status?.state === 'failed' && status.error && (
                      <div className="mt-2 p-2 bg-red-500/10 rounded text-sm text-red-400">
                        {status.error}
                      </div>
                    )}
                  </div>
                  
                  {canExecute && (
                    <Button
                      onClick={() => handleExecute(action.id)}
                      size="sm"
                      variant="outline"
                      className="ml-3"
                    >
                      <PlayCircle className="w-4 h-4 mr-1" />
                      Execute
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}