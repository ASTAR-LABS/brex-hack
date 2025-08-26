'use client';

interface SessionInfoProps {
  sessionId?: string;
}

export function SessionInfo({ sessionId }: SessionInfoProps) {
  if (!sessionId) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-full bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm">
      <div className="w-2 h-2 rounded-full bg-blue-500" />
      <span className="text-xs text-slate-400 font-mono">
        {sessionId.slice(0, 8)}...
      </span>
    </div>
  );
}