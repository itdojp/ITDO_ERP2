import React, { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

export interface ColorSwatch {
  name: string;
  color: string;
}

export interface ColorPickerProps {
  value?: string | null;
  defaultValue?: string | null;
  mode?: "hex" | "rgb" | "hsl";
  format?: "hex" | "rgb" | "hsl";
  size?: "sm" | "md" | "lg";
  theme?: "light" | "dark";
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  clearable?: boolean;
  showAlpha?: boolean;
  showEyedropper?: boolean;
  showGradients?: boolean;
  inline?: boolean;
  portal?: boolean;
  animated?: boolean;
  closeOnSelect?: boolean;
  loading?: boolean;
  error?: string | boolean;
  success?: boolean;
  warning?: boolean;
  label?: string;
  helperText?: string;
  position?: "bottom" | "top" | "left" | "right";
  palette?: string[];
  recentColors?: string[];
  swatches?: ColorSwatch[];
  loadingComponent?: React.ReactNode;
  customTrigger?: React.ReactElement;
  onChange?: (color: string | null) => void;
  onFocus?: (e: React.FocusEvent<HTMLButtonElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLButtonElement>) => void;
  onError?: (error: string) => void;
  onHistoryChange?: (colors: string[]) => void;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

const DEFAULT_PALETTE = [
  "#ff0000",
  "#ff8000",
  "#ffff00",
  "#80ff00",
  "#00ff00",
  "#00ff80",
  "#00ffff",
  "#0080ff",
  "#0000ff",
  "#8000ff",
  "#ff00ff",
  "#ff0080",
  "#800000",
  "#804000",
  "#808000",
  "#408000",
  "#008000",
  "#008040",
  "#008080",
  "#004080",
  "#000080",
  "#400080",
  "#800080",
  "#800040",
  "#400000",
  "#402000",
  "#404000",
  "#204000",
  "#004000",
  "#004020",
  "#004040",
  "#002040",
  "#000040",
  "#200040",
  "#400040",
  "#400020",
  "#000000",
  "#404040",
  "#808080",
  "#c0c0c0",
  "#ffffff",
];

export const ColorPicker: React.FC<ColorPickerProps> = ({
  value,
  defaultValue,
  mode = "hex",
  format = "hex",
  size = "md",
  theme = "light",
  disabled = false,
  readonly = false,
  required = false,
  clearable = false,
  showAlpha = false,
  showEyedropper = false,
  showGradients = false,
  inline = false,
  portal = false,
  animated = false,
  closeOnSelect = true,
  loading = false,
  error,
  success = false,
  warning = false,
  label,
  helperText,
  position = "bottom",
  palette = DEFAULT_PALETTE,
  recentColors = [],
  swatches = [],
  loadingComponent,
  customTrigger,
  onChange,
  onFocus,
  onBlur,
  onError,
  onHistoryChange,
  className,
  "data-testid": dataTestId = "colorpicker-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(inline);
  const [internalValue, setInternalValue] = useState<string | null>(
    value || defaultValue || null,
  );
  const [hexValue, setHexValue] = useState("");
  const [rgbValue, setRgbValue] = useState({ r: 0, g: 0, b: 0 });
  const [hslValue, setHslValue] = useState({ h: 0, s: 0, l: 0 });
  const [alphaValue, setAlphaValue] = useState(1);

  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const paletteRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: "size-sm w-8 h-8",
    md: "size-md w-10 h-10",
    lg: "size-lg w-12 h-12",
  };

  const themeClasses = {
    light: "theme-light border-gray-300",
    dark: "theme-dark border-gray-600",
  };

  // Convert hex to RGB
  const hexToRgb = useCallback((hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : { r: 0, g: 0, b: 0 };
  }, []);

  // Convert RGB to hex
  const rgbToHex = useCallback((r: number, g: number, b: number) => {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  }, []);

  // Convert HSL to hex
  const hslToHex = useCallback((h: number, s: number, l: number) => {
    l /= 100;
    const a = (s * Math.min(l, 1 - l)) / 100;
    const f = (n: number) => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color)
        .toString(16)
        .padStart(2, "0");
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  }, []);

  // Convert hex to HSL
  const hexToHsl = useCallback(
    (hex: string) => {
      const { r, g, b } = hexToRgb(hex);
      const rNorm = r / 255;
      const gNorm = g / 255;
      const bNorm = b / 255;

      const max = Math.max(rNorm, gNorm, bNorm);
      const min = Math.min(rNorm, gNorm, bNorm);
      let h = 0,
        s = 0,
        l = (max + min) / 2;

      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
          case rNorm:
            h = (gNorm - bNorm) / d + (gNorm < bNorm ? 6 : 0);
            break;
          case gNorm:
            h = (bNorm - rNorm) / d + 2;
            break;
          case bNorm:
            h = (rNorm - gNorm) / d + 4;
            break;
        }
        h /= 6;
      }

      return {
        h: Math.round(h * 360),
        s: Math.round(s * 100),
        l: Math.round(l * 100),
      };
    },
    [hexToRgb],
  );

  // Validate hex color
  const isValidHex = useCallback((hex: string) => {
    return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(hex);
  }, []);

  // Update internal state when value changes
  useEffect(() => {
    if (internalValue) {
      setHexValue(internalValue);
      setRgbValue(hexToRgb(internalValue));
      setHslValue(hexToHsl(internalValue));
    }
  }, [internalValue, hexToRgb, hexToHsl]);

  // Close palette on outside click
  useEffect(() => {
    if (inline) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen, inline]);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen]);

  const handleTriggerClick = () => {
    if (disabled || readonly) return;
    setIsOpen(!isOpen);
  };

  const handleTriggerKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleTriggerClick();
    }
  };

  const handleColorSelect = (color: string) => {
    setInternalValue(color);
    onChange?.(color);

    // Add to history
    if (onHistoryChange) {
      const newHistory = [
        color,
        ...recentColors.filter((c) => c !== color),
      ].slice(0, 10);
      onHistoryChange(newHistory);
    }

    if (closeOnSelect) {
      setIsOpen(false);
    }
  };

  const handleHexChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setHexValue(value);
  };

  const handleHexBlur = () => {
    if (isValidHex(hexValue)) {
      handleColorSelect(hexValue);
    } else if (hexValue && hexValue.trim() !== "") {
      onError?.("Invalid hex color format");
    }
  };

  const handleRgbChange = (component: "r" | "g" | "b", value: string) => {
    const numValue = Math.max(0, Math.min(255, parseInt(value) || 0));
    const newRgb = { ...rgbValue, [component]: numValue };
    setRgbValue(newRgb);

    const hexColor = rgbToHex(newRgb.r, newRgb.g, newRgb.b);
    setHexValue(hexColor);
  };

  const handleRgbBlur = () => {
    const hexColor = rgbToHex(rgbValue.r, rgbValue.g, rgbValue.b);
    handleColorSelect(hexColor);
  };

  const handleHslChange = (component: "h" | "s" | "l", value: string) => {
    const numValue =
      component === "h"
        ? Math.max(0, Math.min(360, parseInt(value) || 0))
        : Math.max(0, Math.min(100, parseInt(value) || 0));
    const newHsl = { ...hslValue, [component]: numValue };
    setHslValue(newHsl);

    const hexColor = hslToHex(newHsl.h, newHsl.s, newHsl.l);
    setHexValue(hexColor);
  };

  const handleHslBlur = () => {
    const hexColor = hslToHex(hslValue.h, hslValue.s, hslValue.l);
    handleColorSelect(hexColor);
  };

  const handleAlphaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setAlphaValue(value);
    // Trigger onChange when alpha changes
    if (internalValue) {
      onChange?.(internalValue);
    }
  };

  const handleClear = () => {
    setInternalValue(null);
    setHexValue("");
    onChange?.(null);
  };

  const renderTrigger = () => {
    if (customTrigger) {
      return React.cloneElement(customTrigger, {
        onClick: handleTriggerClick,
        onKeyDown: handleTriggerKeyDown,
        onFocus,
        onBlur,
        "data-testid": "colorpicker-trigger",
      });
    }

    return (
      <button
        ref={triggerRef}
        type="button"
        onClick={handleTriggerClick}
        onKeyDown={handleTriggerKeyDown}
        onFocus={onFocus}
        onBlur={onBlur}
        disabled={disabled}
        className={cn(
          "border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors relative overflow-hidden",
          sizeClasses[size],
          themeClasses[theme],
          error && "border-red-500",
          success && "border-green-500",
          warning && "border-yellow-500",
          disabled && "opacity-50 cursor-not-allowed",
        )}
        style={{
          backgroundColor: internalValue || "#ffffff",
        }}
        data-testid="colorpicker-trigger"
      >
        {!internalValue && (
          <div className="absolute inset-0 bg-gradient-to-br from-transparent via-gray-200 to-gray-300" />
        )}
        {clearable && internalValue && (
          <div
            onClick={(e) => {
              e.stopPropagation();
              handleClear();
            }}
            className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs flex items-center justify-center cursor-pointer"
            data-testid="colorpicker-clear"
          >
            ✕
          </div>
        )}
      </button>
    );
  };

  const renderPalette = () => {
    const paletteElement = (
      <div
        ref={paletteRef}
        className={cn(
          "absolute bg-white border rounded-lg shadow-lg z-50 p-4 w-80",
          `position-${position}`,
          animated && "animated",
          position === "bottom" && "top-full mt-2",
          position === "top" && "bottom-full mb-2",
          position === "left" && "right-full mr-2",
          position === "right" && "left-full ml-2",
        )}
        data-testid="colorpicker-palette"
      >
        {/* Color Input Section */}
        <div className="mb-4">
          {mode === "hex" && (
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Hex
              </label>
              <input
                type="text"
                value={hexValue}
                onChange={handleHexChange}
                onBlur={handleHexBlur}
                placeholder="#000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                data-testid="colorpicker-hex-input"
              />
            </div>
          )}

          {mode === "rgb" && (
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  R
                </label>
                <input
                  type="number"
                  min="0"
                  max="255"
                  value={rgbValue.r}
                  onChange={(e) => handleRgbChange("r", e.target.value)}
                  onBlur={handleRgbBlur}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  data-testid="colorpicker-r-input"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  G
                </label>
                <input
                  type="number"
                  min="0"
                  max="255"
                  value={rgbValue.g}
                  onChange={(e) => handleRgbChange("g", e.target.value)}
                  onBlur={handleRgbBlur}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  data-testid="colorpicker-g-input"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  B
                </label>
                <input
                  type="number"
                  min="0"
                  max="255"
                  value={rgbValue.b}
                  onChange={(e) => handleRgbChange("b", e.target.value)}
                  onBlur={handleRgbBlur}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  data-testid="colorpicker-b-input"
                />
              </div>
            </div>
          )}

          {mode === "hsl" && (
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  H
                </label>
                <input
                  type="number"
                  min="0"
                  max="360"
                  value={hslValue.h}
                  onChange={(e) => handleHslChange("h", e.target.value)}
                  onBlur={handleHslBlur}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  data-testid="colorpicker-h-input"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  S
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={hslValue.s}
                  onChange={(e) => handleHslChange("s", e.target.value)}
                  onBlur={handleHslBlur}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  data-testid="colorpicker-s-input"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  L
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={hslValue.l}
                  onChange={(e) => handleHslChange("l", e.target.value)}
                  onBlur={handleHslBlur}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  data-testid="colorpicker-l-input"
                />
              </div>
            </div>
          )}
        </div>

        {/* Alpha Slider */}
        {showAlpha && (
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Alpha
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={alphaValue}
              onChange={handleAlphaChange}
              className="w-full"
              data-testid="colorpicker-alpha-slider"
            />
          </div>
        )}

        {/* Tools */}
        <div className="flex gap-2 mb-4">
          {showEyedropper && (
            <button
              type="button"
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              data-testid="colorpicker-eyedropper"
            >
              🔍 Eyedropper
            </button>
          )}
        </div>

        {/* Color Palette */}
        <div className="mb-4">
          <div className="grid grid-cols-7 gap-1">
            {palette.map((color, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleColorSelect(color)}
                className={cn(
                  "w-8 h-8 rounded border-2 hover:scale-110 transition-transform",
                  internalValue === color
                    ? "border-gray-800"
                    : "border-gray-300",
                )}
                style={{ backgroundColor: color }}
                data-testid={`color-option-${color}`}
              />
            ))}
          </div>
        </div>

        {/* Swatches */}
        {swatches.length > 0 && (
          <div className="mb-4" data-testid="colorpicker-swatches">
            <h4 className="text-xs font-medium text-gray-700 mb-2">Swatches</h4>
            <div className="space-y-1">
              {swatches.map((swatch, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleColorSelect(swatch.color)}
                  className="flex items-center gap-2 w-full text-left hover:bg-gray-50 p-1 rounded"
                >
                  <div
                    className="w-4 h-4 rounded border border-gray-300"
                    style={{ backgroundColor: swatch.color }}
                  />
                  <span className="text-sm">{swatch.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Recent Colors */}
        {recentColors.length > 0 && (
          <div data-testid="colorpicker-recent">
            <h4 className="text-xs font-medium text-gray-700 mb-2">Recent</h4>
            <div className="flex gap-1">
              {recentColors.slice(0, 10).map((color, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleColorSelect(color)}
                  className="w-6 h-6 rounded border border-gray-300 hover:scale-110 transition-transform"
                  style={{ backgroundColor: color }}
                  data-testid={`recent-color-${color}`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Gradients */}
        {showGradients && (
          <div className="mt-4" data-testid="colorpicker-gradients">
            <h4 className="text-xs font-medium text-gray-700 mb-2">
              Gradients
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="h-8 rounded bg-gradient-to-r from-red-500 to-yellow-500" />
              <div className="h-8 rounded bg-gradient-to-r from-blue-500 to-purple-500" />
              <div className="h-8 rounded bg-gradient-to-r from-green-500 to-blue-500" />
              <div className="h-8 rounded bg-gradient-to-r from-purple-500 to-pink-500" />
            </div>
          </div>
        )}
      </div>
    );

    if (portal && typeof window !== "undefined") {
      return createPortal(paletteElement, document.body);
    }

    return paletteElement;
  };

  if (loading) {
    return (
      <div
        className={cn("flex items-center", className)}
        data-testid="colorpicker-loading"
      >
        {loadingComponent || (
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </div>
    );
  }

  if (inline) {
    return (
      <div
        className={cn("inline-colorpicker", className)}
        data-testid={dataTestId}
        data-category={dataCategory}
        data-id={dataId}
        {...props}
      >
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        {renderPalette()}

        {helperText && (
          <p className="mt-2 text-sm text-gray-600">{helperText}</p>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative",
        `size-${size}`,
        `theme-${theme}`,
        error && "error",
        success && "success",
        warning && "warning",
        className,
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {renderTrigger()}

      {error && typeof error === "string" && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-600">{helperText}</p>
      )}

      {isOpen && renderPalette()}
    </div>
  );
};

export default ColorPicker;