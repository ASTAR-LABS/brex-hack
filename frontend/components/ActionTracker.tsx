"use client";

import { useState, useEffect } from "react";
import { extractActions, getSessionActions, getSessionToken, type ActionStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export function ActionTracker() {
  const [text, setText] = useState("");
  const [actions, setActions] = useState<ActionStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [isPolling, setIsPolling] = useState(false);

  // Poll for all session actions
  useEffect(() => {
    const sessionToken = getSessionToken();
    if (!sessionToken) return;

    // Load initial actions
    loadSessionActions();
    setIsPolling(true);

    // Poll for updates
    const interval = setInterval(async () => {
      await loadSessionActions();
    }, 2000); // Poll every 2 seconds

    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, []);

  const loadSessionActions = async () => {
    try {
      const result = await getSessionActions();
      setActions(result.actions);
    } catch (err) {
      console.error('Failed to load session actions:', err);
    }
  };

  const handleExtract = async () => {
    if (!text.trim()) return;

    setLoading(true);
    try {
      await extractActions(text);
      setText(""); // Clear input after successful extraction
      
      // Actions will appear automatically via polling
      await loadSessionActions();
    } catch (err) {
      console.error('Failed to extract actions:', err);
    } finally {
      setLoading(false);
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
          <h3 className="text-lg font-medium text-white mb-3">
            Session Actions {isPolling && <span className="text-xs text-gray-400 ml-2">(Live)</span>}
          </h3>
          {actions.map((action) => {
            const willAutoExecute = action.confidence > 0.8;
            
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
                      {action.confidence > 0 && (
                        <span className="text-xs text-gray-500">
                          ({(action.confidence * 100).toFixed(0)}% confidence)
                        </span>
                      )}
                      <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${getStateColor(action.state)}`}>
                        {getStateIcon(action.state)}
                        <span>{action.state}</span>
                      </div>
                      {willAutoExecute && action.state === 'queued' && (
                        <span className="text-xs text-blue-400">• Auto-executing</span>
                      )}
                    </div>
                    <p className="text-white">{action.description}</p>
                    
                    {/* Show result or error */}
                    {action.state === 'resolved' && action.result && (
                      <div className="mt-3">
                        {action.result.html_url ? (
                          <Button
                            asChild
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <a 
                              href={action.result.html_url} 
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
                    
                    {action.state === 'failed' && action.error && (
                      <div className="mt-2 p-2 bg-red-500/10 rounded text-sm text-red-400">
                        {action.error}
                      </div>
                    )}
                    
                    {!willAutoExecute && action.state === 'extracted' && (
                      <div className="mt-2 text-xs text-gray-500">
                        Low confidence - requires manual execution
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}