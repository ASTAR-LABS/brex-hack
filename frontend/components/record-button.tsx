'use client';

import { Mic, MicOff } from 'lucide-react';

interface RecordButtonProps {
  isRecording: boolean;
  isConnecting: boolean;
  onClick: () => void;
}

export function RecordButton({ isRecording, isConnecting, onClick }: RecordButtonProps) {
  return (
    <div className="relative">
      {/* Animated ring around button when recording */}
      {isRecording && (
        <div className="absolute -inset-4 rounded-full border border-red-500/30 animate-ping" />
      )}
      
      <button
        onClick={onClick}
        disabled={isConnecting}
        className={`
          relative w-32 h-32 rounded-full backdrop-blur-sm
          transition-all duration-300 ease-out transform
          shadow-2xl hover:scale-105 active:scale-95
          ${isRecording 
            ? 'bg-gradient-to-br from-red-500/20 to-red-600/30 border-2 border-red-500/50 shadow-red-500/20' 
            : 'bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-2 border-slate-600/50 hover:border-slate-500/60 shadow-slate-900/50'
          }
          ${isConnecting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {/* Inner glow effect */}
        <div className={`
          absolute inset-1 rounded-full transition-all duration-300
          ${isRecording 
            ? 'bg-gradient-to-br from-red-500/10 to-red-600/20' 
            : 'bg-gradient-to-br from-white/5 to-white/10'
          }
        `} />

        <div className="relative flex items-center justify-center w-full h-full">
          {isRecording ? (
            <MicOff className="w-10 h-10 text-white drop-shadow-lg" />
          ) : (
            <Mic className="w-10 h-10 text-white drop-shadow-lg" />
          )}
        </div>

        {/* Live indicator */}
        {isRecording && (
          <div className="absolute -top-3 -right-3">
            <div className="flex items-center gap-2 bg-gradient-to-r from-red-500 to-red-600 px-3 py-1.5 rounded-full shadow-lg">
              <div className="w-2.5 h-2.5 bg-white rounded-full animate-pulse" />
              <span className="text-xs text-white font-semibold tracking-wider">LIVE</span>
            </div>
          </div>
        )}

        {/* Connecting spinner */}
        {isConnecting && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-20 h-20 border-3 border-slate-600/30 border-t-white rounded-full animate-spin" />
          </div>
        )}
      </button>

      {/* Microphone status text */}
      <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
        <p className="text-sm text-gray-400 font-medium">
          {isConnecting ? 'Connecting...' : isRecording ? 'Recording' : 'Click to record'}
        </p>
      </div>
    </div>
  );
}