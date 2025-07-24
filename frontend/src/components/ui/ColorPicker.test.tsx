<<<<<<< HEAD
import { render, fireEvent, screen } from '@testing-library/react';
import { ColorPicker } from './ColorPicker';

describe('ColorPicker', () => {
  it('renders color button with initial color', () => {
    render(<ColorPicker value="#FF5733" />);
    const button = screen.getByRole('button');
    expect(button).toHaveStyle('background-color: #FF5733');
  });

  it('opens color picker when button is clicked', () => {
    render(<ColorPicker />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText('カスタムカラー')).toBeInTheDocument();
  });

  it('shows preset colors when enabled', () => {
    render(<ColorPicker showPresets />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText('プリセットカラー')).toBeInTheDocument();
  });

  it('hides preset colors when disabled', () => {
    render(<ColorPicker showPresets={false} />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.queryByText('プリセットカラー')).not.toBeInTheDocument();
  });

  it('calls onChange when preset color is selected', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    // Click on first preset color
    const presetButtons = screen.getAllByRole('button');
    const firstPreset = presetButtons.find(btn => btn.getAttribute('title') === '#FF5733');
    if (firstPreset) {
      fireEvent.click(firstPreset);
      expect(handleChange).toHaveBeenCalledWith('#FF5733');
    }
  });

  it('applies custom color when apply button is clicked', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    const customColorInput = screen.getByPlaceholderText('#000000');
    fireEvent.change(customColorInput, { target: { value: '#123456' } });
    
    const applyButton = screen.getByText('適用');
    fireEvent.click(applyButton);
    
    expect(handleChange).toHaveBeenCalledWith('#123456');
  });

  it('formats color in RGB format', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} format="rgb" />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    const presetButtons = screen.getAllByRole('button');
    const firstPreset = presetButtons.find(btn => btn.getAttribute('title') === '#FF5733');
    if (firstPreset) {
      fireEvent.click(firstPreset);
      expect(handleChange).toHaveBeenCalledWith('rgb(255, 87, 51)');
    }
  });

  it('formats color in HSL format', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} format="hsl" />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    const presetButtons = screen.getAllByRole('button');
    const firstPreset = presetButtons.find(btn => btn.getAttribute('title') === '#FF5733');
    if (firstPreset) {
      fireEvent.click(firstPreset);
      expect(handleChange).toHaveBeenCalledWith(expect.stringMatching(/^hsl\(\d+, \d+%, \d+%\)$/));
    }
  });

  it('respects disabled state', () => {
    render(<ColorPicker disabled />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    
    fireEvent.click(button);
    expect(screen.queryByText('カスタムカラー')).not.toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<ColorPicker size="sm" />);
    expect(screen.getByRole('button')).toHaveClass('w-8', 'h-8');

    rerender(<ColorPicker size="lg" />);
    expect(screen.getByRole('button')).toHaveClass('w-12', 'h-12');
  });

  it('closes picker when clicking outside', () => {
    render(
      <div>
        <ColorPicker />
        <button>Outside button</button>
      </div>
    );
    
    const colorButton = screen.getAllByRole('button')[0];
    fireEvent.click(colorButton);
    expect(screen.getByText('カスタムカラー')).toBeInTheDocument();
    
    const outsideButton = screen.getByText('Outside button');
    fireEvent.mouseDown(outsideButton);
    
    expect(screen.queryByText('カスタムカラー')).not.toBeInTheDocument();
  });

  it('shows current color information', () => {
    render(<ColorPicker value="#FF5733" />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(screen.getByText('選択中:')).toBeInTheDocument();
    expect(screen.getByText('#FF5733')).toBeInTheDocument();
  });
});
=======
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ColorPicker } from "./ColorPicker";

describe("ColorPicker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders color picker with default color", () => {
    render(<ColorPicker />);

    expect(screen.getByTestId("colorpicker-container")).toBeInTheDocument();
    expect(screen.getByTestId("colorpicker-trigger")).toBeInTheDocument();
  });

  it("displays selected color as background", () => {
    render(<ColorPicker value="#ff5733" />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    expect(trigger).toHaveStyle({ backgroundColor: "#ff5733" });
  });

  it("opens color palette on trigger click", () => {
    render(<ColorPicker />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();
  });

  it("closes palette on outside click", async () => {
    render(<ColorPicker />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(
        screen.queryByTestId("colorpicker-palette"),
      ).not.toBeInTheDocument();
    });
  });

  it("selects color from predefined palette", () => {
    const onChange = vi.fn();
    render(<ColorPicker onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const colorOption = screen.getByTestId("color-option-#ff0000");
    fireEvent.click(colorOption);

    expect(onChange).toHaveBeenCalledWith("#ff0000");
  });

  it("allows custom color input via hex field", () => {
    const onChange = vi.fn();
    render(<ColorPicker onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const hexInput = screen.getByTestId("colorpicker-hex-input");
    fireEvent.change(hexInput, { target: { value: "#123456" } });
    fireEvent.blur(hexInput);

    expect(onChange).toHaveBeenCalledWith("#123456");
  });

  it("supports RGB input mode", () => {
    const onChange = vi.fn();
    render(<ColorPicker mode="rgb" onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const rInput = screen.getByTestId("colorpicker-r-input");
    const gInput = screen.getByTestId("colorpicker-g-input");
    const bInput = screen.getByTestId("colorpicker-b-input");

    fireEvent.change(rInput, { target: { value: "255" } });
    fireEvent.change(gInput, { target: { value: "128" } });
    fireEvent.change(bInput, { target: { value: "64" } });
    fireEvent.blur(bInput);

    expect(onChange).toHaveBeenCalledWith("#ff8040");
  });

  it("supports HSL input mode", () => {
    const onChange = vi.fn();
    render(<ColorPicker mode="hsl" onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const hInput = screen.getByTestId("colorpicker-h-input");
    const sInput = screen.getByTestId("colorpicker-s-input");
    const lInput = screen.getByTestId("colorpicker-l-input");

    fireEvent.change(hInput, { target: { value: "240" } });
    fireEvent.change(sInput, { target: { value: "100" } });
    fireEvent.change(lInput, { target: { value: "50" } });
    fireEvent.blur(lInput);

    expect(onChange).toHaveBeenCalled();
  });

  it("supports alpha channel", () => {
    const onChange = vi.fn();
    render(<ColorPicker value="#ff0000" showAlpha onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-alpha-slider")).toBeInTheDocument();

    const alphaSlider = screen.getByTestId("colorpicker-alpha-slider");
    fireEvent.change(alphaSlider, { target: { value: "0.5" } });

    expect(onChange).toHaveBeenCalled();
  });

  it("displays recent colors", () => {
    const recentColors = ["#ff0000", "#00ff00", "#0000ff"];
    render(<ColorPicker recentColors={recentColors} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-recent")).toBeInTheDocument();
    expect(screen.getByTestId("recent-color-#ff0000")).toBeInTheDocument();
    expect(screen.getByTestId("recent-color-#00ff00")).toBeInTheDocument();
    expect(screen.getByTestId("recent-color-#0000ff")).toBeInTheDocument();
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<ColorPicker size={size} />);
      const container = screen.getByTestId("colorpicker-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<ColorPicker theme={theme} />);
      const container = screen.getByTestId("colorpicker-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports disabled state", () => {
    render(<ColorPicker disabled />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    expect(trigger).toBeDisabled();
  });

  it("supports readonly state", () => {
    render(<ColorPicker readonly />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.queryByTestId("colorpicker-palette")).not.toBeInTheDocument();
  });

  it("shows clear button when clearable", () => {
    render(<ColorPicker value="#ff0000" clearable />);

    expect(screen.getByTestId("colorpicker-clear")).toBeInTheDocument();
  });

  it("clears color when clear button clicked", () => {
    const onChange = vi.fn();
    render(<ColorPicker value="#ff0000" clearable onChange={onChange} />);

    const clearButton = screen.getByTestId("colorpicker-clear");
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("validates hex color input", () => {
    const onError = vi.fn();
    render(<ColorPicker onError={onError} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const hexInput = screen.getByTestId("colorpicker-hex-input");
    fireEvent.change(hexInput, { target: { value: "invalid" } });
    fireEvent.blur(hexInput);

    expect(onError).toHaveBeenCalledWith("Invalid hex color format");
  });

  it("supports custom color palettes", () => {
    const customPalette = ["#custom1", "#custom2", "#custom3"];
    render(<ColorPicker palette={customPalette} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("color-option-#custom1")).toBeInTheDocument();
    expect(screen.getByTestId("color-option-#custom2")).toBeInTheDocument();
    expect(screen.getByTestId("color-option-#custom3")).toBeInTheDocument();
  });

  it("supports eyedropper tool", () => {
    const onChange = vi.fn();
    render(<ColorPicker showEyedropper onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-eyedropper")).toBeInTheDocument();
  });

  it("supports gradient selection", () => {
    const onChange = vi.fn();
    render(<ColorPicker showGradients onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-gradients")).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    render(<ColorPicker />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.keyDown(trigger, { key: "Enter" });

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();
  });

  it("closes palette on Escape key", () => {
    render(<ColorPicker />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });

    expect(screen.queryByTestId("colorpicker-palette")).not.toBeInTheDocument();
  });

  it("supports inline mode", () => {
    render(<ColorPicker inline />);

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();
    expect(screen.queryByTestId("colorpicker-trigger")).not.toBeInTheDocument();
  });

  it("supports custom trigger component", () => {
    const CustomTrigger = ({ onClick }: { onClick: () => void }) => (
      <button data-testid="custom-trigger" onClick={onClick}>
        Custom
      </button>
    );

    render(
      <ColorPicker customTrigger={<CustomTrigger onClick={() => {}} />} />,
    );

    expect(screen.getByTestId("custom-trigger")).toBeInTheDocument();
  });

  it("handles focus and blur events", () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<ColorPicker onFocus={onFocus} onBlur={onBlur} />);

    const trigger = screen.getByTestId("colorpicker-trigger");

    fireEvent.focus(trigger);
    expect(onFocus).toHaveBeenCalledTimes(1);

    fireEvent.blur(trigger);
    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it("supports loading state", () => {
    render(<ColorPicker loading />);

    expect(screen.getByTestId("colorpicker-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading...</div>
    );
    render(<ColorPicker loading loadingComponent={<LoadingComponent />} />);

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports error state", () => {
    render(<ColorPicker error="Invalid color" />);

    const container = screen.getByTestId("colorpicker-container");
    expect(container).toHaveClass("error");
    expect(screen.getByText("Invalid color")).toBeInTheDocument();
  });

  it("supports success state", () => {
    render(<ColorPicker success />);

    const container = screen.getByTestId("colorpicker-container");
    expect(container).toHaveClass("success");
  });

  it("supports warning state", () => {
    render(<ColorPicker warning />);

    const container = screen.getByTestId("colorpicker-container");
    expect(container).toHaveClass("warning");
  });

  it("supports helper text", () => {
    render(<ColorPicker helperText="Choose your color" />);

    expect(screen.getByText("Choose your color")).toBeInTheDocument();
  });

  it("supports label", () => {
    render(<ColorPicker label="Theme Color" />);

    expect(screen.getByText("Theme Color")).toBeInTheDocument();
  });

  it("marks required field", () => {
    render(<ColorPicker label="Theme Color" required />);

    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("supports custom positioning", () => {
    render(<ColorPicker position="top" />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const palette = screen.getByTestId("colorpicker-palette");
    expect(palette).toHaveClass("position-top");
  });

  it("supports portal rendering", () => {
    render(<ColorPicker portal />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();
  });

  it("supports animation", () => {
    render(<ColorPicker animated />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const palette = screen.getByTestId("colorpicker-palette");
    expect(palette).toHaveClass("animated");
  });

  it("supports color format conversion", () => {
    const onChange = vi.fn();
    render(<ColorPicker value="#ff0000" mode="rgb" onChange={onChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    // Component should display RGB format
    const rInput = screen.getByTestId("colorpicker-r-input");
    const gInput = screen.getByTestId("colorpicker-g-input");
    const bInput = screen.getByTestId("colorpicker-b-input");

    expect(rInput).toHaveValue(255);
    expect(gInput).toHaveValue(0);
    expect(bInput).toHaveValue(0);
  });

  it("supports custom className", () => {
    render(<ColorPicker className="custom-colorpicker" />);

    const container = screen.getByTestId("colorpicker-container");
    expect(container).toHaveClass("custom-colorpicker");
  });

  it("supports custom data attributes", () => {
    render(<ColorPicker data-category="form-input" data-id="theme-color" />);

    const container = screen.getByTestId("colorpicker-container");
    expect(container).toHaveAttribute("data-category", "form-input");
    expect(container).toHaveAttribute("data-id", "theme-color");
  });

  it("supports close on select", () => {
    render(<ColorPicker closeOnSelect />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const colorOption = screen.getByTestId("color-option-#ff0000");
    fireEvent.click(colorOption);

    expect(screen.queryByTestId("colorpicker-palette")).not.toBeInTheDocument();
  });

  it("keeps palette open when closeOnSelect is false", () => {
    render(<ColorPicker closeOnSelect={false} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const colorOption = screen.getByTestId("color-option-#ff0000");
    fireEvent.click(colorOption);

    expect(screen.getByTestId("colorpicker-palette")).toBeInTheDocument();
  });

  it("supports swatches with custom colors", () => {
    const swatches = [
      { name: "Primary", color: "#007bff" },
      { name: "Secondary", color: "#6c757d" },
      { name: "Success", color: "#28a745" },
    ];
    render(<ColorPicker swatches={swatches} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    expect(screen.getByTestId("colorpicker-swatches")).toBeInTheDocument();
    expect(screen.getByText("Primary")).toBeInTheDocument();
    expect(screen.getByText("Secondary")).toBeInTheDocument();
    expect(screen.getByText("Success")).toBeInTheDocument();
  });

  it("supports color history management", () => {
    const onHistoryChange = vi.fn();
    render(<ColorPicker onHistoryChange={onHistoryChange} />);

    const trigger = screen.getByTestId("colorpicker-trigger");
    fireEvent.click(trigger);

    const colorOption = screen.getByTestId("color-option-#ff0000");
    fireEvent.click(colorOption);

    expect(onHistoryChange).toHaveBeenCalledWith(
      expect.arrayContaining(["#ff0000"]),
    );
  });
});
>>>>>>> origin/main
