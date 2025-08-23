'use client';

import { X } from 'lucide-react';

interface TranscriptionDisplayProps {
  transcription: string[];
  isRecording: boolean;
  onClear: () => void;
}

export function TranscriptionDisplay({ transcription, isRecording, onClear }: TranscriptionDisplayProps) {
  if (!isRecording && transcription.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl mt-12 min-h-[200px]">
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
    </div>
  );
}