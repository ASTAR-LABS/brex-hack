'use client';

import { Wifi, WifiOff } from 'lucide-react';

export type ConnectionStatusType = 'idle' | 'connecting' | 'connected' | 'error' | 'disconnected';

interface ConnectionStatusProps {
  status: ConnectionStatusType;
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const getStatusStyle = () => {
    switch (status) {
      case 'connected': 
        return {
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/30',
          dot: 'bg-emerald-500'
        };
      case 'connecting': 
        return {
          color: 'text-amber-400',
          bg: 'bg-amber-500/10 border-amber-500/30',
          dot: 'bg-amber-500'
        };
      case 'error': 
        return {
          color: 'text-red-400',
          bg: 'bg-red-500/10 border-red-500/30',
          dot: 'bg-red-500'
        };
      default: 
        return {
          color: 'text-slate-400',
          bg: 'bg-slate-500/10 border-slate-500/30',
          dot: 'bg-slate-500'
        };
    }
  };

  const getIcon = () => {
    return status === 'connected' ? 
      <Wifi className="w-4 h-4" /> : 
      <WifiOff className="w-4 h-4" />;
  };

  const statusStyle = getStatusStyle();

  return (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-full backdrop-blur-sm border ${statusStyle.bg} ${statusStyle.color}`}>
      <div className={`w-2 h-2 rounded-full ${statusStyle.dot} ${status === 'connecting' ? 'animate-pulse' : ''}`} />
      {getIcon()}
      <span className="text-xs font-medium uppercase tracking-wider">
        {status}
      </span>
    </div>
  );
}