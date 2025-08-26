'use client';

import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';

interface TranscriptionDisplayProps {
  transcription: string[];
  isRecording: boolean;
  onClear: () => void;
}

export function TranscriptionDisplay({ transcription, isRecording, onClear }: TranscriptionDisplayProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when new words are added
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [transcription.length]);
  
  if (!isRecording && transcription.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-5xl">
      <div className="bg-gradient-to-br from-slate-800/40 to-slate-900/60 border border-slate-700/50 rounded-3xl p-8 backdrop-blur-lg relative shadow-2xl shadow-black/20">
        {/* Header with stats and controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            {transcription.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                <span className="font-medium">{transcription.length} words</span>
              </div>
            )}
            {isRecording && (
              <div className="flex items-center gap-2 text-sm text-red-400">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                <span className="font-medium">Recording...</span>
              </div>
            )}
          </div>
          
          {/* Clear button */}
          {transcription.length > 0 && !isRecording && (
            <button
              onClick={onClear}
              className="p-2 text-slate-500 hover:text-slate-300 transition-all duration-200 hover:bg-slate-700/30 rounded-lg"
              title="Clear transcript"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
        
        {/* Scrollable content area */}
        <div 
          ref={scrollContainerRef}
          className="overflow-y-auto scroll-smooth custom-scrollbar"
          style={{
            maxHeight: '18rem',
          }}
        >
          <div className="text-xl leading-relaxed text-slate-200 font-light">
            {transcription.length === 0 && isRecording ? (
              <div className="flex items-center justify-center h-24 text-slate-400">
                <span className="animate-pulse">Listening...</span>
              </div>
            ) : transcription.length === 0 && !isRecording ? (
              <div className="flex items-center justify-center h-24 text-slate-500">
                <span>Your transcription will appear here</span>
              </div>
            ) : (
              <>
                {transcription.map((word, i) => (
                  <span
                    key={i}
                    className="inline-block mr-2 animate-fade-in"
                    style={{
                      animationDelay: `${i * 50}ms`
                    }}
                  >
                    {word}
                  </span>
                ))}
                {isRecording && (
                  <span className="inline-block w-1 h-6 bg-slate-400 animate-pulse ml-1 rounded-sm" />
                )}
              </>
            )}
          </div>
        </div>
        
        {/* Gradient fade at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-slate-800/60 to-transparent pointer-events-none rounded-b-3xl" />
      </div>
    </div>
  );
}