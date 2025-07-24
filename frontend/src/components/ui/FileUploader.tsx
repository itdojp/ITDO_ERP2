import React, { useState, useRef, useCallback } from "react";

interface FileUploaderProps {
  onFileSelect?: (files: File[]) => void;
  onFileUpload?: (files: File[]) => Promise<void>;
  acceptedTypes?: string[];
  maxFileSize?: number; // in bytes
  maxFiles?: number;
  multiple?: boolean;
  disabled?: boolean;
  dragAndDrop?: boolean;
  showPreview?: boolean;
}

interface FileItem {
  file: File;
  id: string;
  preview?: string;
  progress?: number;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFileSelect,
  onFileUpload,
  acceptedTypes = ["image/*", "application/pdf", ".doc", ".docx"],
  maxFileSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  multiple = true,
  disabled = false,
  dragAndDrop = true,
  showPreview = true,
}) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const validateFile = (file: File): string | null => {
    if (file.size > maxFileSize) {
      return `ファイルサイズが上限（${formatFileSize(maxFileSize)}）を超えています`;
    }

    const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
    const isAccepted = acceptedTypes.some((type) => {
      if (type.startsWith(".")) {
        return type.toLowerCase() === fileExtension;
      }
      if (type.includes("*")) {
        const baseType = type.split("/")[0];
        return file.type.startsWith(baseType);
      }
      return file.type === type;
    });

    if (!isAccepted) {
      return `許可されていないファイル形式です（${acceptedTypes.join(", ")}）`;
    }

    return null;
  };

  const createFilePreview = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.readAsDataURL(file);
      } else {
        resolve("");
      }
    });
  };

  const processFiles = useCallback(
    async (fileList: FileList) => {
      const newFiles = Array.from(fileList);

      if (files.length + newFiles.length > maxFiles) {
        alert(`最大${maxFiles}個のファイルまでアップロードできます`);
        return;
      }

      const processedFiles: FileItem[] = [];

      for (const file of newFiles) {
        const validationError = validateFile(file);
        const preview = showPreview ? await createFilePreview(file) : "";

        const fileItem: FileItem = {
          file,
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          preview,
          status: validationError ? "error" : "pending",
          error: validationError || undefined,
          progress: 0,
        };

        processedFiles.push(fileItem);
      }

      setFiles((prev) => [...prev, ...processedFiles]);

      const validFiles = processedFiles
        .filter((f) => f.status === "pending")
        .map((f) => f.file);
      if (validFiles.length > 0) {
        onFileSelect?.(validFiles);
      }
    },
    [
      files.length,
      maxFiles,
      maxFileSize,
      acceptedTypes,
      showPreview,
      onFileSelect,
    ],
  );

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (fileList) {
      processFiles(fileList);
    }
    // Reset input value to allow selecting same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled && dragAndDrop) {
        setIsDragging(true);
      }
    },
    [disabled, dragAndDrop],
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (!disabled && dragAndDrop) {
        const fileList = e.dataTransfer.files;
        if (fileList) {
          processFiles(fileList);
        }
      }
    },
    [disabled, dragAndDrop, processFiles],
  );

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const uploadFiles = async () => {
    if (!onFileUpload) return;

    const pendingFiles = files.filter((f) => f.status === "pending");
    if (pendingFiles.length === 0) return;

    // Update status to uploading
    setFiles((prev) =>
      prev.map((f) =>
        f.status === "pending"
          ? { ...f, status: "uploading" as const, progress: 0 }
          : f,
      ),
    );

    try {
      const filesToUpload = pendingFiles.map((f) => f.file);
      await onFileUpload(filesToUpload);

      // Update status to success
      setFiles((prev) =>
        prev.map((f) =>
          f.status === "uploading"
            ? { ...f, status: "success" as const, progress: 100 }
            : f,
        ),
      );
    } catch (error) {
      // Update status to error
      setFiles((prev) =>
        prev.map((f) =>
          f.status === "uploading"
            ? {
                ...f,
                status: "error" as const,
                error:
                  error instanceof Error ? error.message : "アップロードエラー",
              }
            : f,
        ),
      );
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "text-blue-600 bg-blue-100";
      case "uploading":
        return "text-yellow-600 bg-yellow-100";
      case "success":
        return "text-green-600 bg-green-100";
      case "error":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return "待機中";
      case "uploading":
        return "アップロード中";
      case "success":
        return "完了";
      case "error":
        return "エラー";
      default:
        return "不明";
    }
  };

  return (
    <div className="w-full">
      {/* File Input Area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging && dragAndDrop ? "border-blue-400 bg-blue-50" : "border-gray-300"}
          ${disabled ? "bg-gray-50 cursor-not-allowed" : "hover:border-gray-400 cursor-pointer"}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={acceptedTypes.join(",")}
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
        />

        <div className="space-y-4">
          <div className="text-4xl text-gray-400">📁</div>
          <div>
            <p className="text-lg font-medium text-gray-700">
              {dragAndDrop
                ? "ファイルをドラッグ＆ドロップまたはクリック"
                : "クリックしてファイルを選択"}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              最大{maxFiles}ファイル、{formatFileSize(maxFileSize)}まで
            </p>
            <p className="text-xs text-gray-400 mt-1">
              対応形式: {acceptedTypes.join(", ")}
            </p>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">
            選択されたファイル
          </h3>

          {files.map((fileItem) => (
            <div
              key={fileItem.id}
              className="flex items-center space-x-4 p-3 border border-gray-200 rounded-lg"
            >
              {/* Preview */}
              {showPreview && fileItem.preview && (
                <img
                  src={fileItem.preview}
                  alt={fileItem.file.name}
                  className="w-12 h-12 object-cover rounded"
                />
              )}

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {fileItem.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(fileItem.file.size)}
                </p>
                {fileItem.error && (
                  <p className="text-xs text-red-600 mt-1">{fileItem.error}</p>
                )}
              </div>

              {/* Status */}
              <div className="flex items-center space-x-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${getStatusColor(fileItem.status)}`}
                >
                  {getStatusText(fileItem.status)}
                </span>

                {/* Remove Button */}
                <button
                  onClick={() => removeFile(fileItem.id)}
                  disabled={fileItem.status === "uploading"}
                  className="text-gray-400 hover:text-red-600 disabled:cursor-not-allowed"
                  type="button"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}

          {/* Upload Button */}
          {onFileUpload && files.some((f) => f.status === "pending") && (
            <div className="flex justify-end pt-4">
              <button
                onClick={uploadFiles}
                disabled={
                  disabled || files.every((f) => f.status !== "pending")
                }
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                type="button"
              >
                アップロード (
                {files.filter((f) => f.status === "pending").length})
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUploader;
