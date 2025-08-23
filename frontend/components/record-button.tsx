'use client';

import { Mic, MicOff } from 'lucide-react';

interface RecordButtonProps {
  isRecording: boolean;
  isConnecting: boolean;
  onClick: () => void;
}

export function RecordButton({ isRecording, isConnecting, onClick }: RecordButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isConnecting}
      className={`
        relative w-24 h-24 rounded-full border backdrop-blur-sm
        transition-all duration-200
        ${isRecording 
          ? 'bg-red-500/10 border-red-500' 
          : 'bg-gray-900/30 border-gray-700 hover:border-gray-600'
        }
        ${isConnecting ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <div className="flex items-center justify-center w-full h-full">
        {isRecording ? (
          <MicOff className="w-8 h-8 text-white" />
        ) : (
          <Mic className="w-8 h-8 text-white" />
        )}
      </div>

      {/* Live indicator */}
      {isRecording && (
        <div className="absolute -top-2 -right-2">
          <div className="flex items-center gap-1.5 bg-black px-2 py-1 rounded-full">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-[10px] text-red-500 font-medium tracking-wider">LIVE</span>
          </div>
        </div>
      )}

      {/* Connecting spinner */}
      {isConnecting && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-16 h-16 border-2 border-gray-600 border-t-white rounded-full animate-spin" />
        </div>
      )}
    </button>
  );
}