'use client';

interface SessionInfoProps {
  sessionId?: string;
}

export function SessionInfo({ sessionId }: SessionInfoProps) {
  if (!sessionId) return null;

  return (
    <div className="absolute top-4 left-4 text-xs text-gray-500">
      Session: {sessionId.slice(0, 8)}...
    </div>
  );
}