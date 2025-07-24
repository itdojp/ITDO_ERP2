import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { RichTextEditor } from "./RichTextEditor";

describe("RichTextEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders rich text editor with toolbar", () => {
    render(<RichTextEditor />);

    expect(screen.getByTestId("richtexteditor-container")).toBeInTheDocument();
    expect(screen.getByTestId("richtexteditor-toolbar")).toBeInTheDocument();
    expect(screen.getByTestId("richtexteditor-content")).toBeInTheDocument();
  });

  it("displays initial content in editor", () => {
    const content = "<p>Hello <strong>World</strong></p>";
    render(<RichTextEditor value={content} />);

    const editor = screen.getByTestId("richtexteditor-content");
    expect(editor.innerHTML).toContain("Hello");
    expect(editor.innerHTML).toContain("World");
  });

  it("handles text formatting - bold", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const boldButton = screen.getByTestId("toolbar-bold");
    fireEvent.click(boldButton);

    expect(boldButton).toHaveClass("active");
  });

  it("handles text formatting - italic", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const italicButton = screen.getByTestId("toolbar-italic");
    fireEvent.click(italicButton);

    expect(italicButton).toHaveClass("active");
  });

  it("handles text formatting - underline", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const underlineButton = screen.getByTestId("toolbar-underline");
    fireEvent.click(underlineButton);

    expect(underlineButton).toHaveClass("active");
  });

  it("handles text alignment - left", () => {
    render(<RichTextEditor />);

    const alignLeftButton = screen.getByTestId("toolbar-align-left");
    fireEvent.click(alignLeftButton);

    expect(alignLeftButton).toHaveClass("active");
  });

  it("handles text alignment - center", () => {
    render(<RichTextEditor />);

    const alignCenterButton = screen.getByTestId("toolbar-align-center");
    fireEvent.click(alignCenterButton);

    expect(alignCenterButton).toHaveClass("active");
  });

  it("handles text alignment - right", () => {
    render(<RichTextEditor />);

    const alignRightButton = screen.getByTestId("toolbar-align-right");
    fireEvent.click(alignRightButton);

    expect(alignRightButton).toHaveClass("active");
  });

  it("handles heading formats", () => {
    render(<RichTextEditor />);

    const headingSelect = screen.getByTestId("toolbar-heading-select");
    fireEvent.change(headingSelect, { target: { value: "h1" } });

    expect(headingSelect).toHaveValue("h1");
  });

  it("handles font size changes", () => {
    render(<RichTextEditor />);

    const fontSizeSelect = screen.getByTestId("toolbar-fontsize-select");
    fireEvent.change(fontSizeSelect, { target: { value: "5" } });

    expect(fontSizeSelect).toHaveValue("5");
  });

  it("handles font family changes", () => {
    render(<RichTextEditor />);

    const fontFamilySelect = screen.getByTestId("toolbar-fontfamily-select");
    fireEvent.change(fontFamilySelect, { target: { value: "Georgia" } });

    expect(fontFamilySelect).toHaveValue("Georgia");
  });

  it("handles text color changes", () => {
    render(<RichTextEditor />);

    const textColorButton = screen.getByTestId("toolbar-text-color");
    fireEvent.click(textColorButton);

    expect(screen.getByTestId("color-picker-text")).toBeInTheDocument();
  });

  it("handles background color changes", () => {
    render(<RichTextEditor />);

    const bgColorButton = screen.getByTestId("toolbar-bg-color");
    fireEvent.click(bgColorButton);

    expect(screen.getByTestId("color-picker-background")).toBeInTheDocument();
  });

  it("handles list creation - unordered", () => {
    render(<RichTextEditor />);

    const bulletListButton = screen.getByTestId("toolbar-bullet-list");
    fireEvent.click(bulletListButton);

    expect(bulletListButton).toHaveClass("active");
  });

  it("handles list creation - ordered", () => {
    render(<RichTextEditor />);

    const numberedListButton = screen.getByTestId("toolbar-numbered-list");
    fireEvent.click(numberedListButton);

    expect(numberedListButton).toHaveClass("active");
  });

  it("handles link insertion", () => {
    render(<RichTextEditor />);

    const linkButton = screen.getByTestId("toolbar-link");
    fireEvent.click(linkButton);

    expect(screen.getByTestId("link-dialog")).toBeInTheDocument();
  });

  it("handles image insertion", () => {
    render(<RichTextEditor />);

    const imageButton = screen.getByTestId("toolbar-image");
    fireEvent.click(imageButton);

    expect(screen.getByTestId("image-dialog")).toBeInTheDocument();
  });

  it("handles table insertion", () => {
    render(<RichTextEditor />);

    const tableButton = screen.getByTestId("toolbar-table");
    fireEvent.click(tableButton);

    expect(screen.getByTestId("table-dialog")).toBeInTheDocument();
  });

  it("handles undo operation", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const undoButton = screen.getByTestId("toolbar-undo");
    fireEvent.click(undoButton);

    // Undo button should be clickable
    expect(undoButton).not.toBeDisabled();
  });

  it("handles redo operation", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const redoButton = screen.getByTestId("toolbar-redo");
    fireEvent.click(redoButton);

    // Redo button should be clickable
    expect(redoButton).not.toBeDisabled();
  });

  it("handles copy operation", () => {
    render(<RichTextEditor />);

    const copyButton = screen.getByTestId("toolbar-copy");
    fireEvent.click(copyButton);

    // Copy operation should work without errors
    expect(copyButton).toBeInTheDocument();
  });

  it("handles paste operation", () => {
    render(<RichTextEditor />);

    const pasteButton = screen.getByTestId("toolbar-paste");
    fireEvent.click(pasteButton);

    // Paste operation should work without errors
    expect(pasteButton).toBeInTheDocument();
  });

  it("handles clear formatting", () => {
    render(<RichTextEditor />);

    const clearButton = screen.getByTestId("toolbar-clear-format");
    fireEvent.click(clearButton);

    // Clear formatting should work without errors
    expect(clearButton).toBeInTheDocument();
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<RichTextEditor theme={theme} />);
      const container = screen.getByTestId("richtexteditor-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<RichTextEditor size={size} />);
      const container = screen.getByTestId("richtexteditor-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports disabled state", () => {
    render(<RichTextEditor disabled />);

    const editor = screen.getByTestId("richtexteditor-content");
    expect(editor).toHaveAttribute("contenteditable", "false");
  });

  it("supports readonly state", () => {
    render(<RichTextEditor readonly />);

    const editor = screen.getByTestId("richtexteditor-content");
    expect(editor).toHaveAttribute("contenteditable", "false");
  });

  it("shows word count when enabled", () => {
    render(<RichTextEditor showWordCount />);

    expect(screen.getByTestId("word-count")).toBeInTheDocument();
  });

  it("shows character count when enabled", () => {
    render(<RichTextEditor showCharCount />);

    expect(screen.getByTestId("char-count")).toBeInTheDocument();
  });

  it("supports custom toolbar configuration", () => {
    const customToolbar = ["bold", "italic", "link"];
    render(<RichTextEditor toolbar={customToolbar} />);

    expect(screen.getByTestId("toolbar-bold")).toBeInTheDocument();
    expect(screen.getByTestId("toolbar-italic")).toBeInTheDocument();
    expect(screen.getByTestId("toolbar-link")).toBeInTheDocument();
    expect(screen.queryByTestId("toolbar-underline")).not.toBeInTheDocument();
  });

  it("handles content changes", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const editor = screen.getByTestId("richtexteditor-content");
    fireEvent.input(editor, { target: { innerHTML: "<p>New content</p>" } });

    expect(onChange).toHaveBeenCalled();
  });

  it("handles focus events", () => {
    const onFocus = vi.fn();
    render(<RichTextEditor onFocus={onFocus} />);

    const editor = screen.getByTestId("richtexteditor-content");
    fireEvent.focus(editor);

    expect(onFocus).toHaveBeenCalledTimes(1);
  });

  it("handles blur events", () => {
    const onBlur = vi.fn();
    render(<RichTextEditor onBlur={onBlur} />);

    const editor = screen.getByTestId("richtexteditor-content");
    fireEvent.blur(editor);

    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it("supports placeholder text", () => {
    render(<RichTextEditor placeholder="Enter your text here..." />);

    const editor = screen.getByTestId("richtexteditor-content");
    expect(editor).toHaveAttribute(
      "data-placeholder",
      "Enter your text here...",
    );
  });

  it("supports maximum length limit", () => {
    render(<RichTextEditor maxLength={100} />);

    const editor = screen.getByTestId("richtexteditor-content");
    // Type long text
    const longText = "a".repeat(150);
    fireEvent.input(editor, { target: { textContent: longText } });

    // Should be limited
    expect(editor.textContent?.length).toBeLessThanOrEqual(100);
  });

  it("supports auto-save functionality", async () => {
    const onAutoSave = vi.fn();
    render(
      <RichTextEditor
        autoSave
        onAutoSave={onAutoSave}
        autoSaveInterval={100}
      />,
    );

    const editor = screen.getByTestId("richtexteditor-content");
    fireEvent.input(editor, { target: { innerHTML: "<p>Auto save test</p>" } });

    // Wait for auto-save to trigger
    await waitFor(
      () => {
        expect(onAutoSave).toHaveBeenCalled();
      },
      { timeout: 200 },
    );
  });

  it("supports spell check", () => {
    render(<RichTextEditor spellCheck />);

    const editor = screen.getByTestId("richtexteditor-content");
    expect(editor).toHaveAttribute("spellcheck", "true");
  });

  it("supports custom plugins", () => {
    const customPlugin = {
      name: "custom",
      render: () => <button data-testid="custom-plugin">Custom</button>,
    };
    render(<RichTextEditor plugins={[customPlugin]} />);

    expect(screen.getByTestId("custom-plugin")).toBeInTheDocument();
  });

  it("handles keyboard shortcuts", () => {
    render(<RichTextEditor />);

    const editor = screen.getByTestId("richtexteditor-content");

    // Test Ctrl+B for bold
    fireEvent.keyDown(editor, { key: "b", ctrlKey: true });

    const boldButton = screen.getByTestId("toolbar-bold");
    expect(boldButton).toHaveClass("active");
  });

  it("supports fullscreen mode", () => {
    render(<RichTextEditor />);

    const fullscreenButton = screen.getByTestId("toolbar-fullscreen");
    fireEvent.click(fullscreenButton);

    const container = screen.getByTestId("richtexteditor-container");
    expect(container).toHaveClass("fullscreen");
  });

  it("supports markdown import/export", () => {
    render(<RichTextEditor supportMarkdown />);

    const markdownButton = screen.getByTestId("toolbar-markdown");
    fireEvent.click(markdownButton);

    expect(screen.getByTestId("markdown-dialog")).toBeInTheDocument();
  });

  it("supports HTML view mode", () => {
    render(<RichTextEditor />);

    const htmlButton = screen.getByTestId("toolbar-html");
    fireEvent.click(htmlButton);

    expect(screen.getByTestId("html-view")).toBeInTheDocument();
  });

  it("supports print functionality", () => {
    render(<RichTextEditor />);

    const printButton = screen.getByTestId("toolbar-print");
    fireEvent.click(printButton);

    // Print functionality should be available
    expect(printButton).toBeInTheDocument();
  });

  it("supports custom styling", () => {
    render(<RichTextEditor className="custom-editor" />);

    const container = screen.getByTestId("richtexteditor-container");
    expect(container).toHaveClass("custom-editor");
  });

  it("supports loading state", () => {
    render(<RichTextEditor loading />);

    expect(screen.getByTestId("richtexteditor-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading editor...</div>
    );
    render(<RichTextEditor loading loadingComponent={<LoadingComponent />} />);

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports error state", () => {
    render(<RichTextEditor error="Editor failed to load" />);

    const container = screen.getByTestId("richtexteditor-container");
    expect(container).toHaveClass("error");
    expect(screen.getByText("Editor failed to load")).toBeInTheDocument();
  });

  it("supports label", () => {
    render(<RichTextEditor label="Content Editor" />);

    expect(screen.getByText("Content Editor")).toBeInTheDocument();
  });

  it("marks required field", () => {
    render(<RichTextEditor label="Content Editor" required />);

    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("supports helper text", () => {
    render(
      <RichTextEditor helperText="Format your content using the toolbar above" />,
    );

    expect(
      screen.getByText("Format your content using the toolbar above"),
    ).toBeInTheDocument();
  });

  it("supports custom data attributes", () => {
    render(
      <RichTextEditor data-category="content-editor" data-id="main-editor" />,
    );

    const container = screen.getByTestId("richtexteditor-container");
    expect(container).toHaveAttribute("data-category", "content-editor");
    expect(container).toHaveAttribute("data-id", "main-editor");
  });

  it("handles paste from external sources", () => {
    const onChange = vi.fn();
    render(<RichTextEditor onChange={onChange} />);

    const editor = screen.getByTestId("richtexteditor-content");

    // Simulate paste event with clipboard data
    const clipboardData = {
      getData: vi.fn().mockReturnValue("Pasted content"),
    };

    fireEvent.paste(editor, {
      clipboardData,
    });

    expect(onChange).toHaveBeenCalled();
  });

  it("supports drag and drop functionality", () => {
    render(<RichTextEditor allowDragDrop />);

    const editor = screen.getByTestId("richtexteditor-content");

    // Test drop zone
    fireEvent.dragOver(editor);
    expect(editor).toHaveClass("drag-over");
  });

  it("supports collaborative editing indicators", () => {
    const collaborators = [
      { id: "1", name: "User 1", color: "#ff0000" },
      { id: "2", name: "User 2", color: "#00ff00" },
    ];
    render(<RichTextEditor collaborative collaborators={collaborators} />);

    expect(screen.getByTestId("collaborators-list")).toBeInTheDocument();
    expect(screen.getByText("User 1")).toBeInTheDocument();
    expect(screen.getByText("User 2")).toBeInTheDocument();
  });
});
