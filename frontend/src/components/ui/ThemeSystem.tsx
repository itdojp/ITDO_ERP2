import React, { useState, useRef, useCallback, useEffect, useMemo, createContext, useContext } from 'react';
import { cn } from '@/lib/utils';

export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

export interface Typography {
  fontFamily: string;
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
    '4xl': string;
  };
  fontWeight: {
    light: number;
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
  lineHeight: {
    tight: number;
    normal: number;
    relaxed: number;
  };
  letterSpacing: {
    tight: string;
    normal: string;
    wide: string;
  };
}

export interface Spacing {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
  '3xl': string;
  '4xl': string;
}

export interface BorderRadius {
  none: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  full: string;
}

export interface Shadows {
  none: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  inner: string;
}

export interface Animations {
  duration: {
    fast: string;
    normal: string;
    slow: string;
  };
  easing: {
    linear: string;
    easeIn: string;
    easeOut: string;
    easeInOut: string;
  };
  transitions: {
    all: string;
    colors: string;
    transform: string;
    opacity: string;
  };
}

export interface Theme {
  id: string;
  name: string;
  description?: string;
  mode: 'light' | 'dark' | 'auto';
  colors: ColorPalette;
  typography: Typography;
  spacing: Spacing;
  borderRadius: BorderRadius;
  shadows: Shadows;
  animations: Animations;
  customProperties?: Record<string, string>;
  components?: {
    button?: Record<string, any>;
    input?: Record<string, any>;
    card?: Record<string, any>;
    modal?: Record<string, any>;
    [key: string]: Record<string, any> | undefined;
  };
}

export interface ThemePreset {
  id: string;
  name: string;
  description?: string;
  preview?: string;
  theme: Theme;
  category: 'system' | 'user' | 'shared';
  tags?: string[];
  author?: string;
  version?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface ThemeContextValue {
  currentTheme: Theme;
  availableThemes: ThemePreset[];
  setTheme: (themeId: string) => void;
  updateTheme: (updates: Partial<Theme>) => void;
  createTheme: (theme: Theme) => void;
  deleteTheme: (themeId: string) => void;
  exportTheme: (themeId: string) => string;
  importTheme: (themeData: string) => void;
  resetTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Default themes
export const defaultThemes: ThemePreset[] = [
  {
    id: 'light',
    name: 'Light',
    description: 'Clean light theme with modern aesthetics',
    category: 'system',
    theme: {
      id: 'light',
      name: 'Light',
      mode: 'light',
      colors: {
        primary: '#3B82F6',
        secondary: '#6B7280',
        accent: '#8B5CF6',
        background: '#FFFFFF',
        surface: '#F9FAFB',
        text: '#111827',
        textSecondary: '#6B7280',
        border: '#E5E7EB',
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6'
      },
      typography: {
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: {
          xs: '0.75rem',
          sm: '0.875rem',
          base: '1rem',
          lg: '1.125rem',
          xl: '1.25rem',
          '2xl': '1.5rem',
          '3xl': '1.875rem',
          '4xl': '2.25rem'
        },
        fontWeight: {
          light: 300,
          normal: 400,
          medium: 500,
          semibold: 600,
          bold: 700
        },
        lineHeight: {
          tight: 1.25,
          normal: 1.5,
          relaxed: 1.75
        },
        letterSpacing: {
          tight: '-0.025em',
          normal: '0em',
          wide: '0.025em'
        }
      },
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
        '2xl': '2.5rem',
        '3xl': '3rem',
        '4xl': '4rem'
      },
      borderRadius: {
        none: '0',
        sm: '0.125rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        full: '9999px'
      },
      shadows: {
        none: 'none',
        sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)'
      },
      animations: {
        duration: {
          fast: '150ms',
          normal: '300ms',
          slow: '500ms'
        },
        easing: {
          linear: 'linear',
          easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
          easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
          easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
        },
        transitions: {
          all: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          colors: 'color 300ms cubic-bezier(0.4, 0, 0.2, 1), background-color 300ms cubic-bezier(0.4, 0, 0.2, 1), border-color 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          transform: 'transform 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          opacity: 'opacity 300ms cubic-bezier(0.4, 0, 0.2, 1)'
        }
      }
    }
  },
  {
    id: 'dark',
    name: 'Dark',
    description: 'Sleek dark theme for reduced eye strain',
    category: 'system',
    theme: {
      id: 'dark',
      name: 'Dark',
      mode: 'dark',
      colors: {
        primary: '#60A5FA',
        secondary: '#9CA3AF',
        accent: '#A78BFA',
        background: '#111827',
        surface: '#1F2937',
        text: '#F9FAFB',
        textSecondary: '#9CA3AF',
        border: '#374151',
        success: '#34D399',
        warning: '#FBBF24',
        error: '#F87171',
        info: '#60A5FA'
      },
      typography: {
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: {
          xs: '0.75rem',
          sm: '0.875rem',
          base: '1rem',
          lg: '1.125rem',
          xl: '1.25rem',
          '2xl': '1.5rem',
          '3xl': '1.875rem',
          '4xl': '2.25rem'
        },
        fontWeight: {
          light: 300,
          normal: 400,
          medium: 500,
          semibold: 600,
          bold: 700
        },
        lineHeight: {
          tight: 1.25,
          normal: 1.5,
          relaxed: 1.75
        },
        letterSpacing: {
          tight: '-0.025em',
          normal: '0em',
          wide: '0.025em'
        }
      },
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
        '2xl': '2.5rem',
        '3xl': '3rem',
        '4xl': '4rem'
      },
      borderRadius: {
        none: '0',
        sm: '0.125rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        full: '9999px'
      },
      shadows: {
        none: 'none',
        sm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3)',
        xl: '0 20px 25px -5px rgb(0 0 0 / 0.3), 0 8px 10px -6px rgb(0 0 0 / 0.3)',
        inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.3)'
      },
      animations: {
        duration: {
          fast: '150ms',
          normal: '300ms',
          slow: '500ms'
        },
        easing: {
          linear: 'linear',
          easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
          easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
          easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
        },
        transitions: {
          all: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          colors: 'color 300ms cubic-bezier(0.4, 0, 0.2, 1), background-color 300ms cubic-bezier(0.4, 0, 0.2, 1), border-color 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          transform: 'transform 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          opacity: 'opacity 300ms cubic-bezier(0.4, 0, 0.2, 1)'
        }
      }
    }
  }
];

export interface ThemeSystemProps {
  themes?: ThemePreset[];
  defaultThemeId?: string;
  enableCustomization?: boolean;
  enablePresets?: boolean;
  enableExport?: boolean;
  enableImport?: boolean;
  enablePreview?: boolean;
  autoSave?: boolean;
  storageKey?: string;
  className?: string;
  style?: React.CSSProperties;
  onThemeChange?: (theme: Theme) => void;
  onThemeCreate?: (theme: Theme) => void;
  onThemeUpdate?: (theme: Theme) => void;
  onThemeDelete?: (themeId: string) => void;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const ThemeSystem: React.FC<ThemeSystemProps> = ({
  themes = defaultThemes,
  defaultThemeId = 'light',
  enableCustomization = true,
  enablePresets = true,
  enableExport = true,
  enableImport = true,
  enablePreview = true,
  autoSave = true,
  storageKey = 'app-theme',
  className,
  style,
  onThemeChange,
  onThemeCreate,
  onThemeUpdate,
  onThemeDelete,
  onError,
  'data-testid': dataTestId = 'theme-system'
}) => {
  const [availableThemes, setAvailableThemes] = useState<ThemePreset[]>(themes);
  const [currentThemeId, setCurrentThemeId] = useState<string>(defaultThemeId);
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [customTheme, setCustomTheme] = useState<Theme | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'system' | 'user' | 'shared'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showColorPicker, setShowColorPicker] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get current theme
  const currentTheme = useMemo(() => {
    const themePreset = availableThemes.find(t => t.id === currentThemeId);
    return customTheme || themePreset?.theme || defaultThemes[0].theme;
  }, [availableThemes, currentThemeId, customTheme]);

  // Filtered themes for display
  const filteredThemes = useMemo(() => {
    let filtered = availableThemes;

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(theme => theme.category === selectedCategory);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(theme =>
        theme.name.toLowerCase().includes(query) ||
        theme.description?.toLowerCase().includes(query) ||
        theme.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    return filtered;
  }, [availableThemes, selectedCategory, searchQuery]);

  // Apply theme to DOM
  const applyTheme = useCallback((theme: Theme) => {
    const root = document.documentElement;
    
    // Apply CSS custom properties
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
      root.style.setProperty(`--font-size-${key}`, value);
    });

    Object.entries(theme.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });

    Object.entries(theme.borderRadius).forEach(([key, value]) => {
      root.style.setProperty(`--border-radius-${key}`, value);
    });

    Object.entries(theme.shadows).forEach(([key, value]) => {
      root.style.setProperty(`--shadow-${key}`, value);
    });

    // Apply font family
    root.style.setProperty('--font-family', theme.typography.fontFamily);

    // Apply custom properties
    if (theme.customProperties) {
      Object.entries(theme.customProperties).forEach(([key, value]) => {
        root.style.setProperty(`--${key}`, value);
      });
    }

    // Apply theme mode class
    root.classList.remove('light-theme', 'dark-theme');
    root.classList.add(`${theme.mode}-theme`);

    // Store theme preference
    if (autoSave) {
      try {
        localStorage.setItem(storageKey, JSON.stringify({
          themeId: theme.id,
          customTheme: customTheme
        }));
      } catch (error) {
        console.warn('Failed to save theme preference:', error);
      }
    }
  }, [customTheme, autoSave, storageKey]);

  // Load theme from storage
  useEffect(() => {
    if (autoSave) {
      try {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          const { themeId, customTheme: storedCustomTheme } = JSON.parse(stored);
          if (themeId) {
            setCurrentThemeId(themeId);
          }
          if (storedCustomTheme) {
            setCustomTheme(storedCustomTheme);
          }
        }
      } catch (error) {
        console.warn('Failed to load theme preference:', error);
      }
    }
  }, [autoSave, storageKey]);

  // Apply current theme
  useEffect(() => {
    applyTheme(currentTheme);
    onThemeChange?.(currentTheme);
  }, [currentTheme, applyTheme, onThemeChange]);

  // Handle theme selection
  const handleThemeSelect = useCallback((themeId: string) => {
    setCurrentThemeId(themeId);
    setCustomTheme(null);
    setIsCustomizing(false);
  }, []);

  // Handle theme customization
  const handleCustomizeTheme = useCallback((baseThemeId?: string) => {
    const baseTheme = baseThemeId 
      ? availableThemes.find(t => t.id === baseThemeId)?.theme
      : currentTheme;
    
    if (baseTheme) {
      setCustomTheme({
        ...baseTheme,
        id: `custom-${Date.now()}`,
        name: `Custom ${baseTheme.name}`,
      });
      setIsCustomizing(true);
    }
  }, [availableThemes, currentTheme]);

  // Handle theme update
  const handleThemeUpdate = useCallback((updates: Partial<Theme>) => {
    if (customTheme) {
      const updatedTheme = { ...customTheme, ...updates };
      setCustomTheme(updatedTheme);
      onThemeUpdate?.(updatedTheme);
    }
  }, [customTheme, onThemeUpdate]);

  // Handle color change
  const handleColorChange = useCallback((colorKey: string, value: string) => {
    if (customTheme) {
      const updatedTheme = {
        ...customTheme,
        colors: {
          ...customTheme.colors,
          [colorKey]: value
        }
      };
      setCustomTheme(updatedTheme);
    }
  }, [customTheme]);

  // Save custom theme
  const handleSaveCustomTheme = useCallback(() => {
    if (customTheme) {
      const newPreset: ThemePreset = {
        id: customTheme.id,
        name: customTheme.name,
        theme: customTheme,
        category: 'user',
        createdAt: new Date(),
        updatedAt: new Date()
      };

      setAvailableThemes(prev => [...prev, newPreset]);
      setCurrentThemeId(customTheme.id);
      setIsCustomizing(false);
      onThemeCreate?.(customTheme);
    }
  }, [customTheme, onThemeCreate]);

  // Delete theme
  const handleDeleteTheme = useCallback((themeId: string) => {
    const theme = availableThemes.find(t => t.id === themeId);
    if (theme && theme.category === 'user') {
      setAvailableThemes(prev => prev.filter(t => t.id !== themeId));
      if (currentThemeId === themeId) {
        setCurrentThemeId(defaultThemeId);
      }
      onThemeDelete?.(themeId);
    }
  }, [availableThemes, currentThemeId, defaultThemeId, onThemeDelete]);

  // Export theme
  const handleExportTheme = useCallback((themeId: string) => {
    const theme = availableThemes.find(t => t.id === themeId);
    if (theme) {
      const exportData = JSON.stringify(theme, null, 2);
      const blob = new Blob([exportData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${theme.name.toLowerCase().replace(/\s+/g, '-')}-theme.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  }, [availableThemes]);

  // Import theme
  const handleImportTheme = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedTheme = JSON.parse(e.target?.result as string) as ThemePreset;
        
        // Validate theme structure
        if (!importedTheme.theme || !importedTheme.theme.colors || !importedTheme.theme.typography) {
          throw new Error('Invalid theme format');
        }

        // Update IDs to avoid conflicts
        const newId = `imported-${Date.now()}`;
        const newTheme: ThemePreset = {
          ...importedTheme,
          id: newId,
          theme: {
            ...importedTheme.theme,
            id: newId
          },
          category: 'user',
          createdAt: new Date(),
          updatedAt: new Date()
        };

        setAvailableThemes(prev => [...prev, newTheme]);
        setCurrentThemeId(newId);
      } catch (error) {
        console.error('Failed to import theme:', error);
        onError?.(error as Error);
      }
    };
    reader.readAsText(file);
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onError]);

  // Reset to default theme
  const handleResetTheme = useCallback(() => {
    setCurrentThemeId(defaultThemeId);
    setCustomTheme(null);
    setIsCustomizing(false);
  }, [defaultThemeId]);

  // Render theme card
  const renderThemeCard = useCallback((themePreset: ThemePreset) => {
    const isActive = currentThemeId === themePreset.id;
    const theme = themePreset.theme;

    return (
      <div
        key={themePreset.id}
        className={cn(
          "relative p-4 border-2 rounded-lg cursor-pointer transition-all duration-200",
          isActive 
            ? "border-blue-500 bg-blue-50 shadow-md" 
            : "border-gray-200 hover:border-gray-300 hover:shadow-sm"
        )}
        onClick={() => handleThemeSelect(themePreset.id)}
        data-testid={`theme-card-${themePreset.id}`}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-sm">{themePreset.name}</h3>
          <div className="flex space-x-1">
            {themePreset.category === 'user' && (
              <button
                className="p-1 text-xs text-red-600 hover:text-red-800"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteTheme(themePreset.id);
                }}
                data-testid={`delete-theme-${themePreset.id}`}
              >
                🗑️
              </button>
            )}
            {enableExport && (
              <button
                className="p-1 text-xs text-blue-600 hover:text-blue-800"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportTheme(themePreset.id);
                }}
                data-testid={`export-theme-${themePreset.id}`}
              >
                📤
              </button>
            )}
          </div>
        </div>

        {themePreset.description && (
          <p className="text-xs text-gray-600 mb-3">{themePreset.description}</p>
        )}

        {/* Color palette preview */}
        <div className="flex space-x-1 mb-3">
          {Object.entries(theme.colors).slice(0, 6).map(([key, color]) => (
            <div
              key={key}
              className="w-4 h-4 rounded-full border border-gray-300"
              style={{ backgroundColor: color }}
              title={key}
            />
          ))}
        </div>

        {/* Theme info */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span className="capitalize">{theme.mode}</span>
          <span className="capitalize">{themePreset.category}</span>
        </div>

        {/* Active indicator */}
        {isActive && (
          <div className="absolute top-2 right-2 w-3 h-3 bg-blue-500 rounded-full" />
        )}
      </div>
    );
  }, [currentThemeId, handleThemeSelect, handleDeleteTheme, handleExportTheme, enableExport]);

  // Render color picker
  const renderColorPicker = useCallback((colorKey: string, colorValue: string) => (
    <div className="relative">
      <button
        className="flex items-center space-x-2 p-2 border border-gray-300 rounded hover:bg-gray-50"
        onClick={() => setShowColorPicker(showColorPicker === colorKey ? null : colorKey)}
        data-testid={`color-picker-${colorKey}`}
      >
        <div
          className="w-4 h-4 rounded border border-gray-300"
          style={{ backgroundColor: colorValue }}
        />
        <span className="text-sm capitalize">{colorKey}</span>
        <span className="text-xs text-gray-500">{colorValue}</span>
      </button>
      
      {showColorPicker === colorKey && (
        <div className="absolute top-full left-0 mt-1 p-2 bg-white border border-gray-300 rounded shadow-lg z-10">
          <input
            type="color"
            value={colorValue}
            onChange={(e) => handleColorChange(colorKey, e.target.value)}
            className="w-12 h-8 border-none cursor-pointer"
          />
          <input
            type="text"
            value={colorValue}
            onChange={(e) => handleColorChange(colorKey, e.target.value)}
            className="mt-1 w-20 px-2 py-1 text-xs border border-gray-300 rounded"
          />
        </div>
      )}
    </div>
  ), [showColorPicker, handleColorChange]);

  // Render customization panel
  const renderCustomizationPanel = () => {
    if (!isCustomizing || !customTheme) return null;

    return (
      <div className="p-6 border-t border-gray-200 bg-gray-50" data-testid="customization-panel">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Customize Theme</h3>
          <div className="flex space-x-2">
            <button
              className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              onClick={handleSaveCustomTheme}
              data-testid="save-custom-theme"
            >
              Save Theme
            </button>
            <button
              className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
              onClick={() => setIsCustomizing(false)}
              data-testid="cancel-customization"
            >
              Cancel
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic settings */}
          <div>
            <h4 className="text-sm font-medium mb-3">Basic Settings</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Theme Name
                </label>
                <input
                  type="text"
                  value={customTheme.name}
                  onChange={(e) => handleThemeUpdate({ name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  data-testid="theme-name-input"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Mode
                </label>
                <select
                  value={customTheme.mode}
                  onChange={(e) => handleThemeUpdate({ mode: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  data-testid="theme-mode-select"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
            </div>
          </div>

          {/* Color palette */}
          <div>
            <h4 className="text-sm font-medium mb-3">Color Palette</h4>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(customTheme.colors).map(([key, value]) => (
                <div key={key}>
                  {renderColorPicker(key, value)}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Preview section */}
        {enablePreview && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-3">Preview</h4>
            <div className="p-4 border border-gray-300 rounded bg-white">
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <button
                    className="px-4 py-2 text-sm rounded transition-colors"
                    style={{
                      backgroundColor: customTheme.colors.primary,
                      color: 'white'
                    }}
                  >
                    Primary Button
                  </button>
                  <button
                    className="px-4 py-2 text-sm border rounded transition-colors"
                    style={{
                      borderColor: customTheme.colors.border,
                      color: customTheme.colors.text
                    }}
                  >
                    Secondary Button
                  </button>
                </div>
                <div
                  className="p-3 rounded"
                  style={{
                    backgroundColor: customTheme.colors.surface,
                    borderColor: customTheme.colors.border,
                    color: customTheme.colors.text
                  }}
                >
                  <h5 className="font-medium">Sample Card</h5>
                  <p className="text-sm mt-1" style={{ color: customTheme.colors.textSecondary }}>
                    This is how your theme will look in components.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={cn(
        "bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden",
        className
      )}
      style={style}
      data-testid={dataTestId}
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-200" data-testid="theme-system-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Theme System</h2>
            <p className="text-sm text-gray-600 mt-1">
              Choose and customize your application theme
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {enableCustomization && (
              <button
                className="px-3 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => handleCustomizeTheme()}
                data-testid="customize-theme-button"
              >
                Customize
              </button>
            )}
            
            {enableImport && (
              <>
                <button
                  className="px-3 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                  onClick={() => fileInputRef.current?.click()}
                  data-testid="import-theme-button"
                >
                  Import
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleImportTheme}
                  className="hidden"
                  data-testid="import-file-input"
                />
              </>
            )}
            
            <button
              className="px-3 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
              onClick={handleResetTheme}
              data-testid="reset-theme-button"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Search and filters */}
        {enablePresets && (
          <div className="mt-4 flex items-center space-x-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search themes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                data-testid="theme-search-input"
              />
            </div>
            
            <div className="flex space-x-2">
              {(['all', 'system', 'user', 'shared'] as const).map(category => (
                <button
                  key={category}
                  className={cn(
                    "px-3 py-2 text-xs rounded border transition-colors",
                    selectedCategory === category
                      ? "bg-blue-500 text-white border-blue-500"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  )}
                  onClick={() => setSelectedCategory(category)}
                  data-testid={`category-filter-${category}`}
                >
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Theme grid */}
      {enablePresets && (
        <div className="p-6" data-testid="themes-grid">
          {filteredThemes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredThemes.map(renderThemeCard)}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🎨</div>
              <div className="text-lg">No themes found</div>
              <div className="text-sm mt-1">Try adjusting your search or filters</div>
            </div>
          )}
        </div>
      )}

      {/* Customization panel */}
      {enableCustomization && renderCustomizationPanel()}
    </div>
  );
};

// Theme Provider component
export interface ThemeProviderProps {
  children: React.ReactNode;
  themes?: ThemePreset[];
  defaultThemeId?: string;
  storageKey?: string;
  onThemeChange?: (theme: Theme) => void;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  themes = defaultThemes,
  defaultThemeId = 'light',
  storageKey = 'app-theme',
  onThemeChange
}) => {
  const [availableThemes, setAvailableThemes] = useState<ThemePreset[]>(themes);
  const [currentThemeId, setCurrentThemeId] = useState<string>(defaultThemeId);

  const currentTheme = useMemo(() => {
    const themePreset = availableThemes.find(t => t.id === currentThemeId);
    return themePreset?.theme || defaultThemes[0].theme;
  }, [availableThemes, currentThemeId]);

  const contextValue: ThemeContextValue = {
    currentTheme,
    availableThemes,
    setTheme: (themeId: string) => setCurrentThemeId(themeId),
    updateTheme: (updates: Partial<Theme>) => {
      // Implementation for updating current theme
    },
    createTheme: (theme: Theme) => {
      const newPreset: ThemePreset = {
        id: theme.id,
        name: theme.name,
        theme,
        category: 'user'
      };
      setAvailableThemes(prev => [...prev, newPreset]);
    },
    deleteTheme: (themeId: string) => {
      setAvailableThemes(prev => prev.filter(t => t.id !== themeId));
    },
    exportTheme: (themeId: string) => {
      const theme = availableThemes.find(t => t.id === themeId);
      return theme ? JSON.stringify(theme, null, 2) : '';
    },
    importTheme: (themeData: string) => {
      try {
        const importedTheme = JSON.parse(themeData) as ThemePreset;
        setAvailableThemes(prev => [...prev, importedTheme]);
      } catch (error) {
        console.error('Failed to import theme:', error);
      }
    },
    resetTheme: () => setCurrentThemeId(defaultThemeId)
  };

  useEffect(() => {
    onThemeChange?.(currentTheme);
  }, [currentTheme, onThemeChange]);

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeSystem;