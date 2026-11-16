import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, RotateCcw } from 'lucide-react';

interface Hero3DBannerProps {
  selectedCity?: string;
}

export const Hero3DBanner: React.FC<Hero3DBannerProps> = ({ selectedCity = 'All' }) => {
  const [animStage, setAnimStage] = useState<'intro-mosaic' | 'intro-glitch' | 'intro-subtitle' | 'settled'>('intro-mosaic');
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const timeoutsRef = useRef<number[]>([]);

  const clearAllTimeouts = () => {
    timeoutsRef.current.forEach((t) => clearTimeout(t));
    timeoutsRef.current = [];
  };

  const startIntroSequence = () => {
    clearAllTimeouts();
    setAnimStage('intro-mosaic');

    // Stage 1: Data-mosaic resolves into glitch title reveal at 500ms
    const t1 = window.setTimeout(() => {
      setAnimStage('intro-glitch');
    }, 500);

    // Stage 2: Reveal subtitle with cyan laser expansion at 1150ms
    const t2 = window.setTimeout(() => {
      setAnimStage('intro-subtitle');
    }, 1150);

    // Stage 3: Settle into clean, pristine final state at 2150ms
    const t3 = window.setTimeout(() => {
      setAnimStage('settled');
    }, 2150);

    timeoutsRef.current = [t1, t2, t3];
  };

  useEffect(() => {
    // Check reduced motion accessibility
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    if (mediaQuery.matches) {
      setAnimStage('settled');
      return;
    }

    startIntroSequence();

    return () => {
      clearAllTimeouts();
    };
  }, []);

  // Subtle interactive 3D depth tilt on hover
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (prefersReducedMotion || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setTilt({
      x: -(y / rect.height) * 12, // Pitch
      y: (x / rect.width) * 14,   // Yaw
    });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
  };

  const replayIntro = () => {
    if (prefersReducedMotion) return;
    startIntroSequence();
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative overflow-hidden rounded-2xl p-8 sm:p-10 md:p-12 transition-all duration-300"
      style={{
        perspective: '1200px',
        transformStyle: 'preserve-3d',
        background: 'var(--hero-bg-gradient)',
        borderColor: 'var(--hero-border)',
        borderWidth: '1px',
        borderStyle: 'solid',
        boxShadow: 'var(--hero-shadow)',
      }}
    >
      {/* Subtle ambient scanline overlay on hero background (pointer-events: none) */}
      <div className="cinematic-scanlines" aria-hidden="true" />

      {/* Sweeping scanline beam across hero container during intro */}
      {animStage !== 'settled' && !prefersReducedMotion && (
        <div className="scanline-beam" aria-hidden="true" />
      )}

      {/* Background ambient lighting effects with cyan-blue accents */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full blur-3xl transition-colors duration-300"
          style={{ backgroundColor: 'var(--hero-flare-1)' }}
        />
        <div
          className="absolute -bottom-24 left-1/3 w-80 h-80 rounded-full blur-3xl transition-colors duration-300"
          style={{ backgroundColor: 'var(--hero-flare-2)' }}
        />
        <div
          className="absolute inset-0 opacity-15"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.2) 1px, transparent 0)`,
            backgroundSize: '24px 24px',
          }}
        />
      </div>

      {/* Replay 3D intro button for interactive verification */}
      <button
        onClick={replayIntro}
        title="Replay 3D Intro Animation"
        aria-label="Replay 3D Intro Animation"
        className="absolute top-4 right-4 z-20 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/90 hover:bg-slate-100 border border-slate-200 text-slate-600 hover:text-slate-900 text-xs transition-colors shadow-sm"
      >
        <RotateCcw size={12} />
        <span className="hidden sm:inline text-[11px] font-medium">Replay Intro</span>
      </button>

      {/* Main 3D Text Stage */}
      <div
        className="relative z-10 flex flex-col items-center justify-center text-center transition-transform duration-200 ease-out"
        style={{
          transform: prefersReducedMotion
            ? 'none'
            : `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
          transformStyle: 'preserve-3d',
        }}
      >
        {/* Territory Status Tag & Futuristic AI Indicator */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-3">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-[11px] font-semibold text-blue-700 transition-all ${
              animStage === 'intro-glitch' && !prefersReducedMotion ? 'ai-glitch-badge' : ''
            }`}
          >
            <Sparkles size={11} className="text-blue-600" />
            ENTERPRISE PLATFORM
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-xs text-slate-500 font-mono">
            Territory: <span className="text-slate-800 font-semibold">{selectedCity}</span>
          </span>
          <span className="text-slate-300 hidden sm:inline">•</span>
          <span className="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-mono text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
            {animStage === 'intro-mosaic' && 'AI_CORE: DECODING MATRIX'}
            {animStage === 'intro-glitch' && 'SIGNAL: SYNCING TELEMETRY'}
            {animStage === 'intro-subtitle' && 'NEURAL: OPTIMIZING MODEL'}
            {animStage === 'settled' && 'AI ENGINE: NOMINAL'}
          </span>
        </div>

        {/* LINE 1: NOVANEST (3D Cinematic Depth Typography & Effects) */}
        <div className="relative overflow-visible my-1 select-none">
          {/* Brief Data-Mosaic transition layer during intro */}
          {animStage === 'intro-mosaic' && !prefersReducedMotion && (
            <div className="data-mosaic-grid" aria-hidden="true">
              {Array.from({ length: 48 }).map((_, i) => (
                <div
                  key={i}
                  className="data-mosaic-cell"
                  style={{
                    animationDelay: `${(i % 12) * 20 + Math.floor(i / 12) * 35}ms`,
                    opacity: i % 2 === 0 ? 0.8 : 0.45,
                  }}
                >
                  {['0x', 'NN', '4F', 'AI', '9B', '10', '01', 'SYS'][i % 8]}
                </div>
              ))}
            </div>
          )}

          {/* Digital signal interference horizontal glitch bar */}
          {animStage === 'intro-glitch' && !prefersReducedMotion && (
            <div className="signal-interference-bar" aria-hidden="true" />
          )}

          <h1
            data-text="NOVANEST"
            className={`font-black tracking-tight text-slate-900 uppercase transition-all duration-700 ease-out text-4xl sm:text-6xl md:text-7xl lg:text-8xl ${
              animStage === 'intro-mosaic' && !prefersReducedMotion
                ? 'opacity-0 scale-90 translate-y-6 blur-md'
                : animStage === 'intro-glitch' && !prefersReducedMotion
                ? 'ai-glitch-intro opacity-100 scale-100 translate-y-0 blur-0'
                : 'opacity-100 scale-100 translate-y-0 blur-0'
            }`}
            style={{
              transform: 'translateZ(35px)',
              background: 'var(--hero-title-gradient)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              filter: 'drop-shadow(0 4px 12px rgba(37, 99, 235, 0.15))',
            }}
          >
            NOVANEST
          </h1>

          {/* Dynamic Light Sweep Flare during Intro */}
          {animStage !== 'settled' && !prefersReducedMotion && (
            <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-transparent via-blue-500/10 to-transparent animate-shimmer" />
          )}
        </div>

        {/* LINE 2: EXACT SUBTITLE DIRECTLY BENEATH NOVANEST */}
        <div
          className={`mt-2 sm:mt-3 transition-all duration-700 ease-out select-none ${
            (animStage === 'intro-mosaic' || animStage === 'intro-glitch') && !prefersReducedMotion
              ? 'opacity-0 translate-y-4 scale-95'
              : 'opacity-100 translate-y-0 scale-100'
          }`}
          style={{ transform: 'translateZ(22px)' }}
        >
          <div className="inline-block relative">
            <h2
              className="text-[11px] sm:text-xs md:text-sm lg:text-base font-bold text-transparent bg-clip-text tracking-[0.20em] sm:tracking-[0.28em] md:tracking-[0.34em] uppercase text-center leading-relaxed"
              style={{
                background: 'var(--hero-subtitle-gradient)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              END - TO - END BUSINESS ANALYTICS SYSTEM
            </h2>
            {/* Subtle glow underline bar with laser expansion */}
            <div
              className={`h-0.5 mx-auto mt-2 opacity-85 transition-all duration-300 ${
                animStage === 'intro-subtitle' && !prefersReducedMotion ? 'subtitle-laser-expand' : 'w-full'
              }`}
              style={{
                background: 'var(--hero-subtitle-gradient)',
                boxShadow: '0 0 8px rgba(37, 99, 235, 0.4)',
              }}
            />
          </div>
        </div>

        {/* Executive summary caption */}
        <p className="mt-4 text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
          Integrated intelligence ecosystem connecting data engineering, predictive machine learning,
          what-if decision simulation, and an analytical digital twin.
        </p>
      </div>
    </div>
  );
};

