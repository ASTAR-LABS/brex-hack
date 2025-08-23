"use client";

import { Mic, MicOff, X, Wifi, WifiOff } from "lucide-react";
import { useTranscription } from "@/hooks/use-transcription";

export default function Home() {

  const {
    isRecording,
    transcription,
    connectionStatus,
    session,
    waveformData,
    startRecording,
    stopRecording,
    clearTranscription,
    isConnecting,
  } = useTranscription({
    onTranscription: (text) => {
      console.log("New transcription:", text);
    },
    onSessionStart: (sessionId) => {
      console.log("Session started:", sessionId);
    },
    onError: (error) => {
      console.error("Transcription error:", error);
    },
  });

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Connection status indicator
  const getConnectionColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getConnectionIcon = () => {
    return connectionStatus === 'connected' ? 
      <Wifi className="w-4 h-4" /> : 
      <WifiOff className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8">
      {/* Connection Status */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <div className={`flex items-center gap-2 ${getConnectionColor()}`}>
          {getConnectionIcon()}
          <span className="text-xs uppercase tracking-wider">
            {connectionStatus}
          </span>
        </div>
      </div>

      {/* Session Info */}
      {session && (
        <div className="absolute top-4 left-4 text-xs text-gray-500">
          Session: {session.id?.slice(0, 8)}...
        </div>
      )}

      {/* Title when not recording */}
      {!isRecording && transcription.length === 0 && (
        <div className="mb-16 text-center animate-fade-in">
          <h1 className="text-3xl text-gray-400 font-light">
            What would you like to record?
          </h1>
          {connectionStatus === 'error' && (
            <p className="text-red-500 text-sm mt-2">
              Connection error. Please check your backend is running.
            </p>
          )}
        </div>
      )}

      {/* Waveform Visualization - Only when recording */}
      {isRecording && (
        <div className="w-full max-w-5xl mb-12 h-40 flex items-center justify-center gap-[2px]">
          {waveformData.map((level, i) => (
            <div
              key={i}
              className="flex-1 bg-gradient-to-t from-emerald-500/80 to-blue-500/80 rounded-sm transition-all duration-100"
              style={{
                height: `${Math.max(2, level * 160)}px`,
                opacity: 0.7 + level * 0.3,
              }}
            />
          ))}
        </div>
      )}

      {/* Record Button */}
      <button
        onClick={toggleRecording}
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

      {/* Transcription Display */}
      <div className="w-full max-w-4xl mt-12 min-h-[200px]">
        {(isRecording || transcription.length > 0) && (
          <div className="bg-gray-900/30 border border-gray-800 rounded-2xl p-8 backdrop-blur-sm relative">
            {/* Clear button */}
            {transcription.length > 0 && !isRecording && (
              <button
                onClick={() => clearTranscription()}
                className="absolute top-4 right-4 p-2 text-gray-500 hover:text-gray-300 transition-colors"
                title="Clear transcript"
              >
                <X className="w-5 h-5" />
              </button>
            )}
            
            {/* Stats */}
            {transcription.length > 0 && (
              <div className="absolute top-4 left-4 text-xs text-gray-500">
                {transcription.length} words
              </div>
            )}
            
            <p className="text-lg leading-relaxed text-gray-300">
              {transcription.map((word, i) => (
                <span
                  key={i}
                  className="inline-block mr-2 animate-fade-in"
                  style={{
                    animationDelay: `${i * 50}ms`,
                    opacity: 0,
                    animationFillMode: 'forwards',
                  }}
                >
                  {word}
                </span>
              ))}
              {isRecording && transcription.length > 0 && (
                <span className="inline-block w-0.5 h-5 bg-gray-500 animate-pulse ml-1" />
              )}
            </p>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}