import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type ThemeId =
  | 'novanest'
  | 'light'
  | 'midnight'
  | 'ocean'
  | 'glassmorphism'
  | 'cyberpunk';

export interface ThemeMeta {
  id: ThemeId;
  name: string;
  subtitle: string;
  description: string;
  palette: [string, string, string]; // 3 primary preview swatches
  isLight: boolean;
  accentColor: string;
  chartColors: {
    primary: string;
    secondary: string;
    accent: string;
    amber: string;
    crimson: string;
    grid: string;
    axis: string;
    text: string;
    tooltipBg: string;
    tooltipBorder: string;
    tooltipText: string;
  };
}

export const THEMES: Record<ThemeId, ThemeMeta> = {
  novanest: {
    id: 'novanest',
    name: 'NovaNest Official',
    subtitle: 'Royal Blue & Vibrant Orange',
    description: 'Official enterprise design system with Slate-50 background, Royal Blue navigation, and Vibrant Orange highlights.',
    palette: ['#F8FAFC', '#2563EB', '#F97316'],
    isLight: true,
    accentColor: '#2563EB',
    chartColors: {
      primary: '#2563EB',
      secondary: '#F97316',
      accent: '#0EA5E9',
      amber: '#F59E0B',
      crimson: '#DC2626',
      grid: '#E2E8F0',
      axis: '#64748B',
      text: '#1E293B',
      tooltipBg: '#FFFFFF',
      tooltipBorder: '#E2E8F0',
      tooltipText: '#1E293B',
    },
  },
  light: {
    id: 'light',
    name: 'Enterprise Light',
    subtitle: 'Crisp White & Slate',
    description: 'Clean professional executive light interface with soft shadows and readable slate typography.',
    palette: ['#FFFFFF', '#2563EB', '#F1F5F9'],
    isLight: true,
    accentColor: '#2563EB',
    chartColors: {
      primary: '#2563EB',
      secondary: '#F97316',
      accent: '#0EA5E9',
      amber: '#F59E0B',
      crimson: '#DC2626',
      grid: '#E2E8F0',
      axis: '#64748B',
      text: '#1E293B',
      tooltipBg: '#FFFFFF',
      tooltipBorder: '#CBD5E1',
      tooltipText: '#0F172A',
    },
  },
  midnight: {
    id: 'midnight',
    name: 'Midnight Dark',
    subtitle: 'Obsidian & Sapphire',
    description: 'High-contrast dark cockpit with deep obsidian and vibrant sapphire accents.',
    palette: ['#06090E', '#3B82F6', '#06B6D4'],
    isLight: false,
    accentColor: '#3B82F6',
    chartColors: {
      primary: '#3B82F6',
      secondary: '#F97316',
      accent: '#06B6D4',
      amber: '#F59E0B',
      crimson: '#EF4444',
      grid: '#1E293B',
      axis: '#64748B',
      text: '#94A3B8',
      tooltipBg: '#0F1622',
      tooltipBorder: '#334155',
      tooltipText: '#F8FAFC',
    },
  },
  ocean: {
    id: 'ocean',
    name: 'Ocean Blue',
    subtitle: 'Deep Navy & Cyan',
    description: 'Deep maritime oceanic palette with cyan radiance and cool indigo depths.',
    palette: ['#030C19', '#0EA5E9', '#06B6D4'],
    isLight: false,
    accentColor: '#0EA5E9',
    chartColors: {
      primary: '#0EA5E9',
      secondary: '#F97316',
      accent: '#38BDF8',
      amber: '#F59E0B',
      crimson: '#EF4444',
      grid: 'rgba(14, 165, 233, 0.2)',
      axis: '#0284C7',
      text: '#7DD3FC',
      tooltipBg: '#081E38',
      tooltipBorder: '#0EA5E9',
      tooltipText: '#F0F9FF',
    },
  },
  glassmorphism: {
    id: 'glassmorphism',
    name: 'Glassmorphism',
    subtitle: 'Frosted Glass & Depth',
    description: 'Translucent acrylic panels with ambient lighting and frosted depth.',
    palette: ['#080E1A', '#38BDF8', 'rgba(255, 255, 255, 0.2)'],
    isLight: false,
    accentColor: '#38BDF8',
    chartColors: {
      primary: '#38BDF8',
      secondary: '#F97316',
      accent: '#818CF8',
      amber: '#FBBF24',
      crimson: '#F87171',
      grid: 'rgba(255, 255, 255, 0.12)',
      axis: 'rgba(255, 255, 255, 0.45)',
      text: '#CBD5E1',
      tooltipBg: 'rgba(15, 23, 42, 0.9)',
      tooltipBorder: 'rgba(255, 255, 255, 0.2)',
      tooltipText: '#F8FAFC',
    },
  },
  cyberpunk: {
    id: 'cyberpunk',
    name: 'Cyberpunk',
    subtitle: 'Neon Cyan & Purple',
    description: 'Futuristic high-energy interface with electric neon glows and violet matrices.',
    palette: ['#060512', '#00F0FF', '#A855F7'],
    isLight: false,
    accentColor: '#00F0FF',
    chartColors: {
      primary: '#00F0FF',
      secondary: '#F97316',
      accent: '#A855F7',
      amber: '#F59E0B',
      crimson: '#F43F5E',
      grid: 'rgba(168, 85, 247, 0.25)',
      axis: '#C084FC',
      text: '#E9D5FF',
      tooltipBg: '#120C2A',
      tooltipBorder: '#A855F7',
      tooltipText: '#FAF5FF',
    },
  },
};

const THEME_STORAGE_KEY = 'novanest_theme';

interface ThemeContextType {
  theme: ThemeId;
  themeMeta: ThemeMeta;
  setTheme: (themeId: ThemeId) => void;
  availableThemes: ThemeMeta[];
  isLight: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeId>(() => {
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY) as ThemeId | null;
      if (saved && saved in THEMES && saved !== ('emerald' as any)) {
        return saved;
      }
    } catch {
      // LocalStorage unavailable
    }
    // Default strictly to official NovaNest Enterprise Theme
    return 'novanest';
  });

  const setTheme = (newTheme: ThemeId) => {
    if (newTheme in THEMES) {
      setThemeState(newTheme);
      try {
        localStorage.setItem(THEME_STORAGE_KEY, newTheme);
      } catch {
        // Ignore quota/storage errors
      }
    }
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const currentThemeMeta = THEMES[theme] || THEMES.novanest;
  const availableThemes = Object.values(THEMES);

  return (
    <ThemeContext.Provider
      value={{
        theme,
        themeMeta: currentThemeMeta,
        setTheme,
        availableThemes,
        isLight: currentThemeMeta.isLight,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
