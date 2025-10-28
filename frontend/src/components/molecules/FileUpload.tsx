import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import styled from 'styled-components';
import { Upload, Image as ImageIcon, X } from 'lucide-react';
import { FileUploadProps } from '../../types';
import { validateImageFile, formatFileSize } from '../../utils';
import { Button } from '../atoms';

const DropzoneContainer = styled.div<{ isDragActive: boolean; disabled: boolean }>`
  border: 2px dashed ${({ isDragActive, disabled }) => 
    disabled ? '#d1d5db' : isDragActive ? '#3b82f6' : '#e5e7eb'};
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  background-color: ${({ isDragActive, disabled }) => 
    disabled ? '#f9fafb' : isDragActive ? '#eff6ff' : '#fafafa'};
  transition: all 0.2s ease;
  cursor: ${({ disabled }) => disabled ? 'not-allowed' : 'pointer'};
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
`;

const UploadIcon = styled(Upload)<{ isDragActive: boolean }>`
  width: 48px;
  height: 48px;
  color: ${({ isDragActive }) => isDragActive ? '#3b82f6' : '#9ca3af'};
  transition: color 0.2s ease;
`;

const UploadText = styled.div`
  color: #374151;
  font-size: 16px;
  font-weight: 600;
`;

const UploadSubtext = styled.div`
  color: #6b7280;
  font-size: 14px;
  margin-top: 4px;
`;

const PreviewContainer = styled.div`
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: white;
`;

const PreviewHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
`;

const FileInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const FileName = styled.span`
  font-weight: 600;
  color: #374151;
`;

const FileSize = styled.span`
  color: #6b7280;
  font-size: 14px;
`;

const PreviewImage = styled.img`
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
`;

const ErrorMessage = styled.div`
  color: #ef4444;
  font-size: 14px;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 4px;
`;

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  accept = 'image/*',
  disabled = false,
  maxSizeMB = 10
}) => {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [preview, setPreview] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file
    const validation = validateImageFile(file);
    if (!validation.valid) {
      setError(validation.error || 'Invalid file');
      return;
    }

    // Check size limit
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File size must be less than ${maxSizeMB}MB`);
      return;
    }

    setError(null);
    setSelectedFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Notify parent
    onFileSelect(file);
  }, [onFileSelect, maxSizeMB]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { [accept]: [] },
    multiple: false,
    disabled
  });

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setPreview(null);
    setError(null);
  };

  return (
    <div>
      {!selectedFile && (
        <DropzoneContainer
          {...getRootProps()}
          isDragActive={isDragActive}
          disabled={disabled}
        >
          <input {...getInputProps()} />
          <UploadIcon isDragActive={isDragActive} />
          <div>
            <UploadText>
              {isDragActive ? 'Drop the image here' : 'Drop an image here or click to select'}
            </UploadText>
            <UploadSubtext>
              Supports JPG, PNG, BMP, TIFF (max {maxSizeMB}MB)
            </UploadSubtext>
          </div>
        </DropzoneContainer>
      )}

      {selectedFile && (
        <PreviewContainer>
          <PreviewHeader>
            <FileInfo>
              <ImageIcon size={20} color="#6b7280" />
              <FileName>{selectedFile.name}</FileName>
              <FileSize>({formatFileSize(selectedFile.size)})</FileSize>
            </FileInfo>
            <Button
              variant="secondary"
              size="small"
              onClick={handleRemoveFile}
            >
              <X size={16} />
              Remove
            </Button>
          </PreviewHeader>
          
          {preview && (
            <PreviewImage
              src={preview}
              alt="Card preview"
            />
          )}
        </PreviewContainer>
      )}

      {error && (
        <ErrorMessage>
          {error}
        </ErrorMessage>
      )}
    </div>
  );
};

export default FileUpload;