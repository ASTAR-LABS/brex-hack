'use client';

import { Wifi, WifiOff } from 'lucide-react';

export type ConnectionStatusType = 'idle' | 'connecting' | 'connected' | 'error' | 'disconnected';

interface ConnectionStatusProps {
  status: ConnectionStatusType;
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getIcon = () => {
    return status === 'connected' ? 
      <Wifi className="w-4 h-4" /> : 
      <WifiOff className="w-4 h-4" />;
  };

  return (
    <div className="absolute top-4 right-4 flex items-center gap-2">
      <div className={`flex items-center gap-2 ${getStatusColor()}`}>
        {getIcon()}
        <span className="text-xs uppercase tracking-wider">
          {status}
        </span>
      </div>
    </div>
  );
}