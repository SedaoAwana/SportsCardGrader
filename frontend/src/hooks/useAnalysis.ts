import { useState, useCallback } from 'react';
import { AnalysisStatus, AnalysisResult } from '../types';
import { SportsCardAPI } from '../services/api';

interface UseAnalysisState {
  isAnalyzing: boolean;
  progress: number;
  status: string;
  error: string | null;
  result: AnalysisResult | null;
  analysisId: string | null;
}

interface UseAnalysisActions {
  startAnalysis: (file: File) => Promise<void>;
  reset: () => void;
  pollStatus: () => Promise<void>;
}

export const useAnalysis = (): [UseAnalysisState, UseAnalysisActions] => {
  const [state, setState] = useState<UseAnalysisState>({
    isAnalyzing: false,
    progress: 0,
    status: 'idle',
    error: null,
    result: null,
    analysisId: null,
  });

  const startAnalysis = useCallback(async (file: File) => {
    try {
      setState(prev => ({
        ...prev,
        isAnalyzing: true,
        progress: 0,
        status: 'Uploading...',
        error: null,
        result: null,
      }));

      // Upload file and start analysis
      const uploadResponse = await SportsCardAPI.uploadAndAnalyze(file);
      
      setState(prev => ({
        ...prev,
        analysisId: uploadResponse.analysis_id,
        progress: 10,
        status: 'Analysis started...',
      }));

      // Poll for results
      const finalStatus = await SportsCardAPI.pollAnalysisStatus(
        uploadResponse.analysis_id,
        (status: AnalysisStatus) => {
          setState(prev => ({
            ...prev,
            progress: status.progress || 0,
            status: status.message || 'Processing...',
          }));
        }
      );

      if (finalStatus.status === 'completed' && finalStatus.result) {
        setState(prev => ({
          ...prev,
          isAnalyzing: false,
          progress: 100,
          status: 'Complete',
          result: finalStatus.result || null,
        }));
      } else {
        throw new Error('Analysis completed but no results received');
      }

    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isAnalyzing: false,
        error: error.message || 'Analysis failed',
        status: 'Error',
      }));
    }
  }, []);

  const pollStatus = useCallback(async () => {
    if (!state.analysisId) return;

    try {
      const status = await SportsCardAPI.getAnalysisStatus(state.analysisId);
      
      setState(prev => ({
        ...prev,
        progress: status.progress || prev.progress,
        status: status.message || prev.status,
      }));

      if (status.status === 'completed' && status.result) {
        setState(prev => ({
          ...prev,
          isAnalyzing: false,
          progress: 100,
          status: 'Complete',
          result: status.result || null,
        }));
      } else if (status.status === 'error') {
        setState(prev => ({
          ...prev,
          isAnalyzing: false,
          error: status.message || 'Analysis failed',
          status: 'Error',
        }));
      }
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isAnalyzing: false,
        error: error.message || 'Failed to check status',
        status: 'Error',
      }));
    }
  }, [state.analysisId]);

  const reset = useCallback(() => {
    setState({
      isAnalyzing: false,
      progress: 0,
      status: 'idle',
      error: null,
      result: null,
      analysisId: null,
    });
  }, []);

  return [
    state,
    { startAnalysis, reset, pollStatus }
  ];
};