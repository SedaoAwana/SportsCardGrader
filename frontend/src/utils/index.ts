/**
 * Utility functions for the Sports Card Grader application
 */

/**
 * Format file size in human readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format grade as display string
 */
export const formatGrade = (grade: number): string => {
  return `${grade}/10`;
};

/**
 * Format score as percentage
 */
export const formatScore = (score: number): string => {
  return `${score.toFixed(1)}/100`;
};

/**
 * Get grade color based on grade value
 */
export const getGradeColor = (grade: number): string => {
  if (grade >= 9) return '#10b981'; // green
  if (grade >= 7) return '#f59e0b'; // yellow
  if (grade >= 5) return '#f97316'; // orange
  return '#ef4444'; // red
};

/**
 * Get confidence level color
 */
export const getConfidenceColor = (confidence: string): string => {
  switch (confidence.toLowerCase()) {
    case 'high':
      return '#10b981'; // green
    case 'medium':
      return '#f59e0b'; // yellow
    case 'low':
      return '#ef4444'; // red
    default:
      return '#6b7280'; // gray
  }
};

/**
 * Truncate text to specified length
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

/**
 * Capitalize first letter
 */
export const capitalize = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1);
};

/**
 * Validate image file
 */
export const validateImageFile = (file: File): { valid: boolean; error?: string } => {
  // Check file type
  if (!file.type.startsWith('image/')) {
    return { valid: false, error: 'File must be an image' };
  }

  // Check file size (10MB limit)
  const maxSizeBytes = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSizeBytes) {
    return { valid: false, error: 'File size must be less than 10MB' };
  }

  // Check for valid image extensions
  const validExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'];
  const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
  
  if (!validExtensions.includes(fileExtension)) {
    return { 
      valid: false, 
      error: 'File must be a valid image format (JPG, PNG, BMP, TIFF)' 
    };
  }

  return { valid: true };
};

/**
 * Generate unique ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).slice(2, 11);
};

/**
 * Debounce function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Format timestamp
 */
export const formatTimestamp = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString();
};

/**
 * Get relative time string
 */
export const getRelativeTime = (timestamp: number): string => {
  const now = Date.now();
  const diff = now - timestamp;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days} day${days === 1 ? '' : 's'} ago`;
  if (hours > 0) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  if (minutes > 0) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  return `${seconds} second${seconds === 1 ? '' : 's'} ago`;
};

/**
 * Check if device is mobile
 */
export const isMobile = (): boolean => {
  return window.innerWidth <= 768;
};

/**
 * Copy text to clipboard
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
};

/**
 * Download data as JSON file
 */
export const downloadAsJson = (data: any, filename: string): void => {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

/**
 * Sleep function for delays
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};