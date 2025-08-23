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
    <div className="w-full max-w-4xl mb-12">
      <div className="bg-gray-900/30 border border-gray-800 rounded-2xl p-8 backdrop-blur-sm relative">
        {/* Clear button */}
        {transcription.length > 0 && !isRecording && (
          <button
            onClick={onClear}
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
        
        {/* Scrollable content area - 10 lines */}
        <div 
          ref={scrollContainerRef}
          className="overflow-y-auto scroll-smooth custom-scrollbar"
          style={{
            maxHeight: '15rem', // 10 lines with line-height of 1.5rem
          }}
        >
          <div className="text-lg leading-relaxed text-gray-300">
            {transcription.map((word, i) => (
              <span
                key={i}
                className="inline-block mr-2"
              >
                {word}
              </span>
            ))}
            {isRecording && transcription.length > 0 && (
              <span className="inline-block w-0.5 h-5 bg-gray-500 animate-pulse ml-1" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}