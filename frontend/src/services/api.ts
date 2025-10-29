import axios from 'axios';
import { AnalysisStatus, ApiHealthResponse, UploadResponse } from '../types';

// Configure axios defaults
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export class SportsCardAPI {
  /**
   * Check API health status
   */
  static async checkHealth(): Promise<ApiHealthResponse> {
    try {
      const response = await api.get<ApiHealthResponse>('/api/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Failed to connect to API server');
    }
  }

  /**
   * Upload image and start analysis
   */
  static async uploadAndAnalyze(file: File): Promise<UploadResponse> {
    try {
      // Validate file
      if (!file.type.startsWith('image/')) {
        throw new Error('File must be an image');
      }

      // Check file size (limit to 10MB)
      const maxSizeBytes = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSizeBytes) {
        throw new Error('File size must be less than 10MB');
      }

      // Create form data
      const formData = new FormData();
      formData.append('file', file);

      // Upload with progress tracking
      const response = await api.post<UploadResponse>('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            console.log(`⬆️ Upload Progress: ${percentCompleted}%`);
          }
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Upload failed:', error);
      
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.message) {
        throw new Error(error.message);
      } else {
        throw new Error('Failed to upload and analyze image');
      }
    }
  }

  /**
   * Get analysis status and results
   */
  static async getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
    try {
      const response = await api.get<AnalysisStatus>(`/api/analysis/${analysisId}`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to get analysis status:', error);
      
      if (error.response?.status === 404) {
        throw new Error('Analysis not found');
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else {
        throw new Error('Failed to get analysis status');
      }
    }
  }

  /**
   * Get detailed debug information for analysis
   */
  static async getAnalysisDebugInfo(analysisId: string): Promise<any> {
    try {
      const response = await api.get(`/api/analysis/${analysisId}/debug`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to get debug info:', error);
      throw new Error('Failed to get debug information');
    }
  }

  /**
   * Delete analysis data (cleanup)
   */
  static async deleteAnalysis(analysisId: string): Promise<void> {
    try {
      await api.delete(`/api/analysis/${analysisId}`);
    } catch (error: any) {
      console.error('Failed to delete analysis:', error);
      // Don't throw error for cleanup operations
    }
  }

  /**
   * List all analyses (for debugging)
   */
  static async listAnalyses(): Promise<any> {
    try {
      const response = await api.get('/api/analyses');
      return response.data;
    } catch (error: any) {
      console.error('Failed to list analyses:', error);
      throw new Error('Failed to list analyses');
    }
  }

  /**
   * Poll for analysis completion
   */
  static async pollAnalysisStatus(
    analysisId: string,
    onProgress?: (status: AnalysisStatus) => void,
    maxAttempts: number = 60, // 5 minutes with 5-second intervals
    intervalMs: number = 5000
  ): Promise<AnalysisStatus> {
    return new Promise((resolve, reject) => {
      let attempts = 0;

      const poll = async () => {
        try {
          attempts++;
          const status = await this.getAnalysisStatus(analysisId);

          // Call progress callback if provided
          if (onProgress) {
            onProgress(status);
          }

          // Check if completed
          if (status.status === 'completed') {
            resolve(status);
            return;
          }

          // Check if failed
          if (status.status === 'error') {
            reject(new Error(status.message || 'Analysis failed'));
            return;
          }

          // Check if max attempts reached
          if (attempts >= maxAttempts) {
            reject(new Error('Analysis timeout: Taking longer than expected'));
            return;
          }

          // Continue polling
          setTimeout(poll, intervalMs);
        } catch (error) {
          reject(error);
        }
      };

      // Start polling
      poll();
    });
  }
}

export default SportsCardAPI;