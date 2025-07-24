import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { FileUpload } from "./FileUpload";

// Mock FileReader for tests
global.FileReader = class {
  readAsDataURL = vi.fn();
  readAsText = vi.fn();
  result = null;
  onload = null;
  onerror = null;
} as any;

describe("FileUpload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders file upload component", () => {
    render(<FileUpload />);

    expect(screen.getByTestId("fileupload-container")).toBeInTheDocument();
    expect(screen.getByTestId("fileupload-dropzone")).toBeInTheDocument();
  });

  it("displays upload instructions", () => {
    render(<FileUpload />);

    expect(screen.getByText(/drag.*drop.*files.*here/i)).toBeInTheDocument();
    expect(screen.getByText(/click.*browse/i)).toBeInTheDocument();
  });

  it("shows file input on click", () => {
    render(<FileUpload />);

    const dropzone = screen.getByTestId("fileupload-dropzone");
    fireEvent.click(dropzone);

    expect(screen.getByTestId("fileupload-input")).toBeInTheDocument();
  });

  it("handles file selection via input", () => {
    const onUpload = vi.fn();
    render(<FileUpload onUpload={onUpload} />);

    const file = new File(["test content"], "test.txt", { type: "text/plain" });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [file] } });

    expect(onUpload).toHaveBeenCalledWith([file]);
  });

  it("handles drag and drop", () => {
    const onUpload = vi.fn();
    render(<FileUpload onUpload={onUpload} />);

    const dropzone = screen.getByTestId("fileupload-dropzone");
    const file = new File(["test content"], "test.txt", { type: "text/plain" });

    fireEvent.dragOver(dropzone);
    expect(dropzone).toHaveClass("drag-over");

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] },
    });

    expect(onUpload).toHaveBeenCalledWith([file]);
  });

  it("prevents default drag behaviors", () => {
    render(<FileUpload />);

    const dropzone = screen.getByTestId("fileupload-dropzone");

    // Create a proper DragEvent mock
    const mockDragEvent = new Event("dragover", { bubbles: true });
    Object.defineProperty(mockDragEvent, "preventDefault", {
      value: vi.fn(),
      writable: false,
    });
    Object.defineProperty(mockDragEvent, "stopPropagation", {
      value: vi.fn(),
      writable: false,
    });

    dropzone.dispatchEvent(mockDragEvent);

    expect(mockDragEvent.preventDefault).toHaveBeenCalled();
    expect(mockDragEvent.stopPropagation).toHaveBeenCalled();
  });

  it("supports multiple file upload", () => {
    const onUpload = vi.fn();
    render(<FileUpload multiple onUpload={onUpload} />);

    const files = [
      new File(["content1"], "file1.txt", { type: "text/plain" }),
      new File(["content2"], "file2.txt", { type: "text/plain" }),
    ];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    expect(onUpload).toHaveBeenCalledWith(files);
  });

  it("respects file type restrictions", () => {
    const onUpload = vi.fn();
    const onError = vi.fn();
    render(
      <FileUpload accept=".txt,.doc" onUpload={onUpload} onError={onError} />,
    );

    const invalidFile = new File(["content"], "image.jpg", {
      type: "image/jpeg",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(onError).toHaveBeenCalledWith("File type not allowed");
    expect(onUpload).not.toHaveBeenCalled();
  });

  it("enforces maximum file size", () => {
    const onUpload = vi.fn();
    const onError = vi.fn();
    render(<FileUpload maxSize={1024} onUpload={onUpload} onError={onError} />);

    // Create a file larger than 1KB
    const largeFile = new File(["x".repeat(2048)], "large.txt", {
      type: "text/plain",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [largeFile] } });

    expect(onError).toHaveBeenCalledWith("File size exceeds limit");
    expect(onUpload).not.toHaveBeenCalled();
  });

  it("enforces maximum number of files", () => {
    const onUpload = vi.fn();
    const onError = vi.fn();
    render(<FileUpload maxFiles={2} onUpload={onUpload} onError={onError} />);

    const files = [
      new File(["1"], "file1.txt"),
      new File(["2"], "file2.txt"),
      new File(["3"], "file3.txt"),
    ];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    expect(onError).toHaveBeenCalledWith("Too many files selected");
    expect(onUpload).not.toHaveBeenCalled();
  });

  it("shows file preview for images", () => {
    render(<FileUpload showPreview showFileList />);

    const imageFile = new File(["fake-image"], "image.jpg", {
      type: "image/jpeg",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [imageFile] } });

    expect(screen.getByTestId("file-preview")).toBeInTheDocument();
  });

  it("displays upload progress", () => {
    render(<FileUpload showProgress status="uploading" />);

    expect(screen.getByTestId("upload-progress")).toBeInTheDocument();
  });

  it("supports custom upload button", () => {
    render(
      <FileUpload
        customButton={
          <button data-testid="custom-upload-btn">Upload Files</button>
        }
      />,
    );

    expect(screen.getByTestId("custom-upload-btn")).toBeInTheDocument();
  });

  it("shows file list when files are selected", () => {
    render(<FileUpload showFileList />);

    const files = [
      new File(["content1"], "file1.txt", { type: "text/plain" }),
      new File(["content2"], "file2.txt", { type: "text/plain" }),
    ];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    expect(screen.getByTestId("file-list")).toBeInTheDocument();
    expect(screen.getByText("file1.txt")).toBeInTheDocument();
    expect(screen.getByText("file2.txt")).toBeInTheDocument();
  });

  it("allows file removal from list", () => {
    const onFilesChange = vi.fn();
    render(<FileUpload showFileList onFilesChange={onFilesChange} />);

    const files = [
      new File(["content1"], "file1.txt", { type: "text/plain" }),
      new File(["content2"], "file2.txt", { type: "text/plain" }),
    ];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    const removeButton = screen.getAllByTestId("remove-file")[0];
    fireEvent.click(removeButton);

    expect(onFilesChange).toHaveBeenCalled();
  });

  it("supports different upload states", () => {
    const states = ["idle", "uploading", "success", "error"] as const;

    states.forEach((state) => {
      const { unmount } = render(<FileUpload status={state} />);
      const container = screen.getByTestId("fileupload-container");
      expect(container).toHaveClass(`status-${state}`);
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<FileUpload size={size} />);
      const container = screen.getByTestId("fileupload-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<FileUpload theme={theme} />);
      const container = screen.getByTestId("fileupload-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports disabled state", () => {
    render(<FileUpload disabled />);

    const dropzone = screen.getByTestId("fileupload-dropzone");
    const input = screen.getByTestId("fileupload-input");

    expect(dropzone).toHaveClass("disabled");
    expect(input).toBeDisabled();
  });

  it("displays custom placeholder text", () => {
    render(<FileUpload placeholder="Drop your documents here" />);

    expect(screen.getByText("Drop your documents here")).toBeInTheDocument();
  });

  it("shows file size formatting", () => {
    render(<FileUpload showFileList />);

    // 1024 bytes = 1KB
    const file = new File(["x".repeat(1024)], "test.txt", {
      type: "text/plain",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/1.*KB/)).toBeInTheDocument();
  });

  it("supports auto-upload functionality", () => {
    const onAutoUpload = vi.fn();
    render(<FileUpload autoUpload onAutoUpload={onAutoUpload} />);

    const file = new File(["content"], "test.txt", { type: "text/plain" });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [file] } });

    expect(onAutoUpload).toHaveBeenCalledWith([file]);
  });

  it("handles upload cancellation", () => {
    const onCancel = vi.fn();
    render(<FileUpload onCancel={onCancel} status="uploading" />);

    const cancelButton = screen.getByTestId("cancel-upload");
    fireEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  it("supports retry functionality", () => {
    const onRetry = vi.fn();
    render(<FileUpload onRetry={onRetry} status="error" />);

    const retryButton = screen.getByTestId("retry-upload");
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalled();
  });

  it("displays upload statistics", () => {
    render(<FileUpload showStats />);

    const files = [
      new File(["content1"], "file1.txt", { type: "text/plain" }),
      new File(["content2"], "file2.txt", { type: "text/plain" }),
    ];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    expect(screen.getByTestId("upload-stats")).toBeInTheDocument();
    expect(screen.getByText(/2 files/i)).toBeInTheDocument();
  });

  it("supports custom error messages", () => {
    const customErrors = {
      fileTooLarge: "Custom file too large message",
      fileTypeInvalid: "Custom file type message",
      tooManyFiles: "Custom too many files message",
    };

    render(<FileUpload maxSize={100} errorMessages={customErrors} />);

    const largeFile = new File(["x".repeat(200)], "large.txt", {
      type: "text/plain",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [largeFile] } });

    expect(
      screen.getByText("Custom file too large message"),
    ).toBeInTheDocument();
  });

  it("supports file validation callback", () => {
    const validate = vi
      .fn()
      .mockReturnValue({ valid: false, message: "Custom validation error" });
    render(<FileUpload onValidate={validate} />);

    const file = new File(["content"], "test.txt", { type: "text/plain" });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [file] } });

    expect(validate).toHaveBeenCalledWith(file);
    expect(screen.getByText("Custom validation error")).toBeInTheDocument();
  });

  it("supports loading state", () => {
    render(<FileUpload loading />);

    expect(screen.getByTestId("fileupload-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Uploading...</div>
    );
    render(<FileUpload loading loadingComponent={<LoadingComponent />} />);

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports helper text", () => {
    render(<FileUpload helperText="Maximum file size: 10MB" />);

    expect(screen.getByText("Maximum file size: 10MB")).toBeInTheDocument();
  });

  it("supports label", () => {
    render(<FileUpload label="Upload Documents" />);

    expect(screen.getByText("Upload Documents")).toBeInTheDocument();
  });

  it("marks required field", () => {
    render(<FileUpload label="Upload Documents" required />);

    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("supports custom styling", () => {
    render(<FileUpload className="custom-upload" />);

    const container = screen.getByTestId("fileupload-container");
    expect(container).toHaveClass("custom-upload");
  });

  it("supports custom data attributes", () => {
    render(<FileUpload data-category="file-input" data-id="document-upload" />);

    const container = screen.getByTestId("fileupload-container");
    expect(container).toHaveAttribute("data-category", "file-input");
    expect(container).toHaveAttribute("data-id", "document-upload");
  });

  it("handles keyboard accessibility", () => {
    render(<FileUpload />);

    const dropzone = screen.getByTestId("fileupload-dropzone");

    fireEvent.keyDown(dropzone, { key: "Enter" });

    // Should trigger file input click
    expect(dropzone).toHaveAttribute("tabindex", "0");
  });

  it("supports drag leave event", () => {
    render(<FileUpload />);

    const dropzone = screen.getByTestId("fileupload-dropzone");

    fireEvent.dragOver(dropzone);
    expect(dropzone).toHaveClass("drag-over");

    fireEvent.dragLeave(dropzone);
    expect(dropzone).not.toHaveClass("drag-over");
  });

  it("supports file type icon display", () => {
    render(<FileUpload showFileList showFileIcons />);

    const textFile = new File(["content"], "document.txt", {
      type: "text/plain",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [textFile] } });

    expect(screen.getByTestId("file-icon")).toBeInTheDocument();
  });

  it("supports upload queue management", () => {
    const onQueueChange = vi.fn();
    render(<FileUpload queueMode onQueueChange={onQueueChange} />);

    const files = [new File(["1"], "file1.txt"), new File(["2"], "file2.txt")];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    expect(onQueueChange).toHaveBeenCalled();
    expect(screen.getByTestId("upload-queue")).toBeInTheDocument();
  });

  it("supports batch upload functionality", () => {
    const onBatchUpload = vi.fn();
    render(<FileUpload batchUpload onBatchUpload={onBatchUpload} />);

    const files = [new File(["1"], "file1.txt"), new File(["2"], "file2.txt")];

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files } });

    const batchButton = screen.getByTestId("batch-upload-btn");
    fireEvent.click(batchButton);

    expect(onBatchUpload).toHaveBeenCalledWith(files);
  });

  it("supports upload compression", () => {
    const onCompress = vi.fn();
    render(<FileUpload compress onCompress={onCompress} />);

    const imageFile = new File(["fake-image"], "image.jpg", {
      type: "image/jpeg",
    });
    const input = screen.getByTestId("fileupload-input");

    fireEvent.change(input, { target: { files: [imageFile] } });

    expect(onCompress).toHaveBeenCalledWith(imageFile);
  });

  it("supports file metadata display", () => {
    render(<FileUpload showFileList showMetadata />);

    const file = new File(["content"], "test.txt", { type: "text/plain" });
    Object.defineProperty(file, "lastModified", {
      value: new Date("2023-01-01").getTime(),
    });

    const input = screen.getByTestId("fileupload-input");
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByTestId("file-metadata")).toBeInTheDocument();
  });
});
