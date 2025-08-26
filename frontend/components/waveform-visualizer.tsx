'use client';

interface WaveformVisualizerProps {
  data: number[];
  isActive: boolean;
}

export function WaveformVisualizer({ data, isActive }: WaveformVisualizerProps) {
  if (!isActive) return null;

  return (
    <div className="w-full max-w-6xl h-32 flex items-center justify-center gap-[1px] px-8">
      {data.map((level, i) => (
        <div
          key={i}
          className="flex-1 bg-gradient-to-t from-cyan-500/60 via-blue-500/70 to-purple-500/60 rounded-full transition-all duration-150 ease-out shadow-sm"
          style={{
            height: `${Math.max(3, level * 120)}px`,
            opacity: 0.6 + level * 0.4,
            boxShadow: level > 0.5 ? `0 0 ${level * 10}px rgba(59, 130, 246, 0.3)` : 'none',
          }}
        />
      ))}
    </div>
  );
}