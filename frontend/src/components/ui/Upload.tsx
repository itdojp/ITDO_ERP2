import React, { useState, useRef, useCallback } from 'react';

interface UploadFile {
  uid: string;
  name: string;
  size?: number;
  type?: string;
  status: 'uploading' | 'done' | 'error' | 'removed';
  percent?: number;
  url?: string;
  response?: any;
  error?: any;
  originFileObj?: File;
}

interface UploadError {
  type: 'INVALID_FILE_TYPE' | 'FILE_TOO_LARGE' | 'TOO_MANY_FILES' | 'UPLOAD_ERROR';
  message: string;
  file?: UploadFile;
}

interface UploadProps {
  action?: string;
  method?: 'POST' | 'PUT';
  headers?: Record<string, string>;
  data?: Record<string, any> | ((file: UploadFile) => Record<string, any>);
  name?: string;
  multiple?: boolean;
  directory?: boolean;
  accept?: string;
  maxSize?: number;
  maxCount?: number;
  fileList?: UploadFile[];
  defaultFileList?: UploadFile[];
  listType?: 'text' | 'picture' | 'picture-card';
  className?: string;
  disabled?: boolean;
  children?: React.ReactNode;
  icon?: React.ReactNode;
  beforeUpload?: (file: File) => boolean | Promise<boolean>;
  customRequest?: (options: any) => Promise<any>;
  transformFile?: (file: File) => File | Promise<File>;
  onChange?: (fileList: UploadFile[]) => void;
  onUpload?: (file: File, onProgress?: (percent: number) => void) => Promise<any>;
  onRemove?: (file: UploadFile) => boolean | Promise<boolean>;
  onPreview?: (file: UploadFile) => void;
  onRetry?: (file: UploadFile) => void;
  onError?: (error: UploadError) => void;
  onProgress?: (event: { percent: number }, file: UploadFile) => void;
}

const Upload: React.FC<UploadProps> = ({
  action = '/upload',
  method = 'POST',
  headers = {},
  data,
  name = 'file',
  multiple = false,
  directory = false,
  accept,
  maxSize,
  maxCount,
  fileList: controlledFileList,
  defaultFileList = [],
  listType = 'text',
  className = '',
  disabled = false,
  children,
  icon,
  beforeUpload,
  customRequest,
  transformFile,
  onChange,
  onUpload,
  onRemove,
  onPreview,
  onRetry,
  onError,
  onProgress
}) => {
  const [internalFileList, setInternalFileList] = useState<UploadFile[]>(defaultFileList);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const isControlled = controlledFileList !== undefined;
  const fileList = isControlled ? controlledFileList : internalFileList;

  const generateUID = () => `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  const isValidFileType = (file: File): boolean => {
    if (!accept) return true;
    
    const acceptedTypes = accept.split(',').map(type => type.trim());
    
    return acceptedTypes.some(acceptedType => {
      if (acceptedType.startsWith('.')) {
        return file.name.toLowerCase().endsWith(acceptedType.toLowerCase());
      }
      if (acceptedType.includes('*')) {
        const [mainType] = acceptedType.split('/');
        return file.type.startsWith(mainType);
      }
      return file.type === acceptedType;
    });
  };

  const isValidFileSize = (file: File): boolean => {
    if (!maxSize) return true;
    return file.size <= maxSize;
  };

  const validateFiles = (files: FileList): { validFiles: File[], errors: UploadError[] } => {
    const validFiles: File[] = [];
    const errors: UploadError[] = [];
    
    if (maxCount && files.length > maxCount) {
      errors.push({
        type: 'TOO_MANY_FILES',
        message: `Maximum ${maxCount} files allowed`
      });
      return { validFiles, errors };
    }
    
    Array.from(files).forEach(file => {
      if (!isValidFileType(file)) {
        errors.push({
          type: 'INVALID_FILE_TYPE',
          message: `File type ${file.type} is not allowed`,
          file: {
            uid: generateUID(),
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'error',
            originFileObj: file
          }
        });
        return;
      }
      
      if (!isValidFileSize(file)) {
        errors.push({
          type: 'FILE_TOO_LARGE',
          message: `File ${file.name} is too large`,
          file: {
            uid: generateUID(),
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'error',
            originFileObj: file
          }
        });
        return;
      }
      
      validFiles.push(file);
    });
    
    return { validFiles, errors };
  };

  const processFiles = async (files: FileList) => {
    const { validFiles, errors } = validateFiles(files);
    
    // Report errors
    errors.forEach(error => onError?.(error));
    
    if (validFiles.length === 0) return;
    
    // Process valid files
    const newFiles: UploadFile[] = [];
    
    for (const file of validFiles) {
      // Transform file if needed
      let processedFile = file;
      if (transformFile) {
        try {
          processedFile = await transformFile(file);
        } catch (error) {
          onError?.({
            type: 'UPLOAD_ERROR',
            message: 'File transformation failed',
            file: {
              uid: generateUID(),
              name: file.name,
              status: 'error',
              originFileObj: file
            }
          });
          continue;
        }
      }
      
      // Validate with beforeUpload
      if (beforeUpload) {
        try {
          const shouldUpload = await beforeUpload(processedFile);
          if (!shouldUpload) continue;
        } catch (error) {
          onError?.({
            type: 'UPLOAD_ERROR',
            message: 'Pre-upload validation failed',
            file: {
              uid: generateUID(),
              name: file.name,
              status: 'error',
              originFileObj: file
            }
          });
          continue;
        }
      }
      
      const uploadFile: UploadFile = {
        uid: generateUID(),
        name: processedFile.name,
        size: processedFile.size,
        type: processedFile.type,
        status: 'uploading',
        percent: 0,
        originFileObj: processedFile
      };
      
      newFiles.push(uploadFile);
    }
    
    if (newFiles.length === 0) return;
    
    const updatedFileList = [...fileList, ...newFiles];
    
    if (!isControlled) {
      setInternalFileList(updatedFileList);
    }
    onChange?.(updatedFileList);
    
    // Start uploading
    newFiles.forEach(uploadFile => {
      startUpload(uploadFile);
    });
  };

  const startUpload = async (uploadFile: UploadFile) => {
    try {
      const file = uploadFile.originFileObj!;
      
      const onProgressHandler = (percent: number) => {
        const updatedFile = { ...uploadFile, percent };
        updateFileInList(updatedFile);
        onProgress?.({ percent }, updatedFile);
      };
      
      let response;
      
      if (customRequest) {
        response = await customRequest({
          file,
          filename: uploadFile.name,
          action,
          headers,
          data: typeof data === 'function' ? data(uploadFile) : data,
          onProgress: onProgressHandler
        });
      } else if (onUpload) {
        response = await onUpload(file, onProgressHandler);
      } else {
        // Default upload implementation
        response = await defaultUpload(file, uploadFile, onProgressHandler);
      }
      
      const completedFile: UploadFile = {
        ...uploadFile,
        status: 'done',
        percent: 100,
        response,
        url: response?.url
      };
      
      updateFileInList(completedFile);
      
    } catch (error) {
      const errorFile: UploadFile = {
        ...uploadFile,
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed'
      };
      
      updateFileInList(errorFile);
      
      onError?.({
        type: 'UPLOAD_ERROR',
        message: error instanceof Error ? error.message : 'Upload failed',
        file: errorFile
      });
    }
  };

  const defaultUpload = async (
    file: File, 
    uploadFile: UploadFile, 
    onProgressHandler: (percent: number) => void
  ): Promise<any> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append(name, file);
      
      if (data) {
        const dataToAppend = typeof data === 'function' ? data(uploadFile) : data;
        Object.keys(dataToAppend).forEach(key => {
          formData.append(key, dataToAppend[key]);
        });
      }
      
      const xhr = new XMLHttpRequest();
      
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgressHandler(percent);
        }
      };
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch {
            resolve({ url: action });
          }
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      };
      
      xhr.onerror = () => {
        reject(new Error('Upload failed'));
      };
      
      xhr.open(method, action);
      
      Object.keys(headers).forEach(key => {
        xhr.setRequestHeader(key, headers[key]);
      });
      
      xhr.send(formData);
    });
  };

  const updateFileInList = (updatedFile: UploadFile) => {
    const newFileList = fileList.map(file => 
      file.uid === updatedFile.uid ? updatedFile : file
    );
    
    if (!isControlled) {
      setInternalFileList(newFileList);
    }
    onChange?.(newFileList);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      processFiles(files);
    }
    
    // Reset input value to allow selecting the same file again
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleDragEnter = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
    
    if (disabled) return;
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      processFiles(files);
    }
  };

  const handlePaste = (event: React.ClipboardEvent) => {
    const items = event.clipboardData.items;
    const files: File[] = [];
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) files.push(file);
      }
    }
    
    if (files.length > 0) {
      const fileList = new DataTransfer();
      files.forEach(file => fileList.items.add(file));
      processFiles(fileList.files);
    }
  };

  const handleRemove = async (file: UploadFile) => {
    if (onRemove) {
      const shouldRemove = await onRemove(file);
      if (!shouldRemove) return;
    }
    
    const newFileList = fileList.filter(f => f.uid !== file.uid);
    
    if (!isControlled) {
      setInternalFileList(newFileList);
    }
    onChange?.(newFileList);
  };

  const handlePreview = (file: UploadFile) => {
    onPreview?.(file);
  };

  const handleRetry = (file: UploadFile) => {
    if (onRetry) {
      onRetry(file);
    } else {
      const retryFile = { ...file, status: 'uploading' as const, percent: 0 };
      updateFileInList(retryFile);
      startUpload(retryFile);
    }
  };

  const renderUploadArea = () => {
    const uploadClasses = [
      'border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors cursor-pointer',
      dragOver ? 'border-blue-500 bg-blue-50' : '',
      disabled ? 'opacity-50 cursor-not-allowed' : '',
      className
    ].filter(Boolean).join(' ');

    if (children) {
      return (
        <div className={uploadClasses} onClick={() => !disabled && inputRef.current?.click()}>
          {children}
        </div>
      );
    }

    return (
      <div 
        className={uploadClasses}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onPaste={handlePaste}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <div className="flex flex-col items-center">
          {icon || (
            <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          )}
          <p className="text-gray-600 mb-2">
            Drag and drop files here, or <span className="text-blue-500">browse</span>
          </p>
          {accept && (
            <p className="text-sm text-gray-500">
              Supported formats: {accept}
            </p>
          )}
          {maxSize && (
            <p className="text-sm text-gray-500">
              Maximum file size: {Math.round(maxSize / 1024 / 1024)}MB
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderFileList = () => {
    if (fileList.length === 0) return null;

    if (listType === 'picture-card') {
      return (
        <div className="grid grid-cols-4 gap-4 mt-4">
          {fileList.map(file => (
            <div key={file.uid} className="relative border rounded-lg p-2">
              {file.type?.startsWith('image/') && file.url ? (
                <img 
                  src={file.url} 
                  alt={file.name}
                  className="w-full h-20 object-cover rounded"
                  onClick={() => handlePreview(file)}
                />
              ) : (
                <div className="w-full h-20 bg-gray-100 rounded flex items-center justify-center">
                  <span className="text-gray-500 text-xs">{file.name}</span>
                </div>
              )}
              
              <div className="absolute top-1 right-1">
                <button
                  onClick={() => handleRemove(file)}
                  className="w-6 h-6 bg-red-500 text-white rounded-full text-xs hover:bg-red-600"
                >
                  ×
                </button>
              </div>
              
              {file.status === 'uploading' && file.percent !== undefined && (
                <div className="absolute bottom-0 left-0 right-0 bg-blue-500 h-1 rounded-b">
                  <div 
                    className="bg-blue-700 h-full rounded-b transition-all"
                    style={{ width: `${file.percent}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="mt-4 space-y-2">
        {fileList.map(file => (
          <div key={file.uid} className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center flex-1">
              {listType === 'picture' && file.type?.startsWith('image/') && file.url && (
                <img 
                  src={file.url} 
                  alt={file.name}
                  className="w-8 h-8 object-cover rounded mr-3"
                  onClick={() => handlePreview(file)}
                />
              )}
              
              <div className="flex-1">
                <div className="font-medium text-sm">{file.name}</div>
                {file.size && (
                  <div className="text-xs text-gray-500">
                    {Math.round(file.size / 1024)}KB
                  </div>
                )}
                
                {file.status === 'uploading' && file.percent !== undefined && (
                  <div className="mt-1">
                    <div className="flex items-center justify-between text-xs">
                      <span>Uploading...</span>
                      <span>{file.percent}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                      <div 
                        className="bg-blue-600 h-1 rounded-full transition-all"
                        style={{ width: `${file.percent}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {file.status === 'error' && (
                  <div className="text-red-500 text-xs mt-1">
                    {file.error || 'Upload failed'}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {file.status === 'error' && (
                <button
                  onClick={() => handleRetry(file)}
                  className="text-blue-500 hover:text-blue-700 text-sm"
                >
                  Retry
                </button>
              )}
              
              <button
                onClick={() => handleRemove(file)}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="upload-component">
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        disabled={disabled}
        onChange={handleFileChange}
        className="hidden"
        role="textbox"
        aria-hidden="true"
        {...(directory ? { webkitdirectory: 'true' as any } : {})}
      />
      
      {renderUploadArea()}
      {renderFileList()}
    </div>
  );
};

export { Upload };
export default Upload;