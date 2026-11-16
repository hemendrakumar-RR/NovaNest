import React, { useState, useRef, useEffect } from 'react';
import { Palette, Check, ChevronDown, Sparkles, Sun, Moon, Waves, Cpu } from 'lucide-react';
import { useTheme, ThemeId, ThemeMeta } from '../context/ThemeContext';

export const ThemeSwitcher: React.FC = () => {
  const { theme, setTheme, availableThemes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close popover on outside click or Escape key
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  // Theme Icon mapping
  const getThemeIcon = (id: ThemeId) => {
    switch (id) {
      case 'novanest':
        return <Sparkles size={14} className="text-blue-600" />;
      case 'light':
        return <Sun size={14} className="text-amber-500" />;
      case 'cyberpunk':
        return <Cpu size={14} className="text-purple-500" />;
      case 'glassmorphism':
        return <Sparkles size={14} className="text-sky-500" />;
      case 'ocean':
        return <Waves size={14} className="text-cyan-500" />;
      case 'midnight':
      default:
        return <Moon size={14} className="text-slate-600" />;
    }
  };

  const currentTheme = availableThemes.find((t) => t.id === theme) || availableThemes[0];

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label={`Current theme: ${currentTheme.name}. Click to change theme.`}
        className={`flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border cursor-pointer select-none ${
          isOpen
            ? 'bg-blue-50 text-blue-600 border-blue-300 shadow-sm'
            : 'bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border-slate-200'
        }`}
      >
        <span className="flex items-center justify-center w-4 h-4">
          {getThemeIcon(theme)}
        </span>
        <span className="hidden sm:inline font-semibold">{currentTheme.name}</span>
        {/* Preview swatch dot */}
        <span
          className="w-2.5 h-2.5 rounded-full border border-slate-300 shadow-sm"
          style={{ backgroundColor: currentTheme.accentColor }}
        />
        <ChevronDown
          size={12}
          className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-blue-600' : ''}`}
        />
      </button>

      {/* Theme Selection Popover Dropdown */}
      {isOpen && (
        <div
          role="menu"
          aria-orientation="vertical"
          className="absolute right-0 top-full mt-2 w-72 sm:w-80 rounded-xl bg-white border border-slate-200 shadow-xl p-2.5 z-50 animate-fadeIn space-y-1.5"
          style={{ animationDuration: '180ms' }}
        >
          {/* Header */}
          <div className="px-2.5 py-2 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Palette size={14} className="text-blue-600" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Design Theme
              </span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {availableThemes.length} Profiles
            </span>
          </div>

          {/* Theme Options */}
          <div className="space-y-1 max-h-80 overflow-y-auto pr-0.5">
            {availableThemes.map((t: ThemeMeta) => {
              const isSelected = theme === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setTheme(t.id);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg transition-all duration-150 flex items-center justify-between gap-3 group border ${
                    isSelected
                      ? 'bg-blue-50 border-blue-200 text-slate-900'
                      : 'hover:bg-slate-50 border-transparent text-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div
                      className={`p-1.5 rounded-md ${
                        isSelected
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-100 text-slate-600 group-hover:bg-blue-50 group-hover:text-blue-600'
                      }`}
                    >
                      {getThemeIcon(t.id)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-semibold truncate text-slate-800">{t.name}</span>
                        {t.id === 'novanest' && (
                          <span className="text-[9px] font-bold px-1 py-0.2 rounded bg-orange-100 text-orange-700 border border-orange-200">
                            OFFICIAL
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500 truncate">{t.subtitle}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* 3 Color swatches preview */}
                    <div className="flex items-center -space-x-1">
                      {t.palette.map((color, idx) => (
                        <span
                          key={idx}
                          className="w-3 h-3 rounded-full border border-white shadow-xs inline-block"
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                    {isSelected && <Check size={14} className="text-blue-600 shrink-0 font-bold" />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
