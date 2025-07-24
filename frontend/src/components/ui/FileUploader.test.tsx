import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { FileUploader } from './FileUploader';

// Mock File constructor
const createMockFile = (name: string, size: number, type: string): File => {
  const blob = new Blob(['test content'], { type });
  return new File([blob], name, { type });
};

describe('FileUploader', () => {
  it('renders upload area with correct text', () => {
    render(<FileUploader />);
    expect(screen.getByText('ファイルをドラッグ＆ドロップまたはクリック')).toBeInTheDocument();
  });

  it('shows file size and count limits', () => {
    render(<FileUploader maxFiles={3} maxFileSize={5 * 1024 * 1024} />);
    expect(screen.getByText('最大3ファイル、5 MBまで')).toBeInTheDocument();
  });

  it('shows accepted file types', () => {
    render(<FileUploader acceptedTypes={['image/*', '.pdf']} />);
    expect(screen.getByText('対応形式: image/*, .pdf')).toBeInTheDocument();
  });

  it('calls onFileSelect when files are selected', async () => {
    const handleFileSelect = jest.fn();
    render(<FileUploader onFileSelect={handleFileSelect} />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('test.jpg', 1000, 'image/jpeg');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(handleFileSelect).toHaveBeenCalledWith([file]);
    });
  });

  it('validates file size', async () => {
    render(<FileUploader maxFileSize={500} />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('large.jpg', 1000, 'image/jpeg');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText(/ファイルサイズが上限/)).toBeInTheDocument();
    });
  });

  it('validates file type', async () => {
    render(<FileUploader acceptedTypes={['image/*']} />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('document.pdf', 1000, 'application/pdf');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText(/許可されていないファイル形式/)).toBeInTheDocument();
    });
  });

  it('respects max files limit', async () => {
    // Mock alert
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
    
    render(<FileUploader maxFiles={2} />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const files = [
      createMockFile('file1.jpg', 1000, 'image/jpeg'),
      createMockFile('file2.jpg', 1000, 'image/jpeg'),
      createMockFile('file3.jpg', 1000, 'image/jpeg'),
    ];
    
    Object.defineProperty(input, 'files', {
      value: files,
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('最大2個のファイルまでアップロードできます');
    });
    
    alertSpy.mockRestore();
  });

  it('removes files when remove button is clicked', async () => {
    render(<FileUploader />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('test.jpg', 1000, 'image/jpeg');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText('test.jpg')).toBeInTheDocument();
    });
    
    const removeButton = screen.getByText('✕');
    fireEvent.click(removeButton);
    
    expect(screen.queryByText('test.jpg')).not.toBeInTheDocument();
  });

  it('handles drag and drop events', () => {
    render(<FileUploader />);
    const dropArea = screen.getByRole('button');
    
    // Test drag over
    fireEvent.dragOver(dropArea);
    expect(dropArea).toHaveClass('border-blue-400', 'bg-blue-50');
    
    // Test drag leave
    fireEvent.dragLeave(dropArea);
    expect(dropArea).not.toHaveClass('border-blue-400', 'bg-blue-50');
  });

  it('disables interactions when disabled', () => {
    render(<FileUploader disabled />);
    const dropArea = screen.getByRole('button');
    
    expect(dropArea).toHaveClass('bg-gray-50', 'cursor-not-allowed');
    
    const input = dropArea.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeDisabled();
  });

  it('shows upload button when onFileUpload is provided', async () => {
    const handleUpload = jest.fn().mockResolvedValue(undefined);
    render(<FileUploader onFileUpload={handleUpload} />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('test.jpg', 1000, 'image/jpeg');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText('アップロード (1)')).toBeInTheDocument();
    });
  });

  it('calls onFileUpload when upload button is clicked', async () => {
    const handleUpload = jest.fn().mockResolvedValue(undefined);
    render(<FileUploader onFileUpload={handleUpload} />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('test.jpg', 1000, 'image/jpeg');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      const uploadButton = screen.getByText('アップロード (1)');
      fireEvent.click(uploadButton);
    });
    
    expect(handleUpload).toHaveBeenCalledWith([file]);
  });

  it('shows file status correctly', async () => {
    render(<FileUploader />);
    
    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;
    const file = createMockFile('test.jpg', 1000, 'image/jpeg');
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText('待機中')).toBeInTheDocument();
    });
  });
});