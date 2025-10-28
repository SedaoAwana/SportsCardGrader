// Base types for the Sports Card Grader application

export interface AnalysisResult {
  analysis_id: string;
  predicted_grade: number;
  grade_description: string;
  overall_score: number;
  confidence_level: string;
  component_breakdown: ComponentBreakdown;
  psa_compliance: PSACompliance;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
  centering_evaluation?: CenteringEvaluation;
  debug_info?: DebugInfo;
}

export interface ComponentBreakdown {
  edges: ComponentScore;
  corners: ComponentScore;
  surface: ComponentScore;
  centering: ComponentScore;
}

export interface ComponentScore {
  score: number;
  grade: number;
  weight: number;
}

export interface PSACompliance {
  overall_compliant: boolean;
  compliance_summary: string;
  component_compliance?: Record<string, any>;
}

export interface CenteringEvaluation {
  estimated_centering_ratio: string;
  required_for_grade: string;
  meets_psa_standard: boolean;
}

export interface DebugInfo {
  file_size: number;
  file_type: string;
  analysis_steps: string[];
  raw_analysis?: any;
  error?: string;
}

export interface AnalysisStatus {
  analysis_id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress?: number;
  message?: string;
  result?: AnalysisResult;
  debug_info?: DebugInfo;
}

export interface ApiHealthResponse {
  status: 'healthy' | 'degraded';
  message: string;
  backend_available: boolean;
  opencv_available?: boolean;
  grading_system_available?: boolean;
}

export interface UploadResponse {
  analysis_id: string;
  status: string;
}

// UI Component Props Types
export interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  type?: 'button' | 'submit' | 'reset';
}

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  elevated?: boolean;
}

export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
}

export interface ProgressBarProps {
  progress: number;
  showPercentage?: boolean;
  color?: string;
  height?: string;
}

export interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  disabled?: boolean;
  maxSizeMB?: number;
}

export interface GradeDisplayProps {
  grade: number;
  description: string;
  score: number;
  confidenceLevel: string;
}

export interface ComponentBreakdownProps {
  breakdown: ComponentBreakdown;
}

export interface AnalysisResultsProps {
  result: AnalysisResult;
  onStartNewAnalysis: () => void;
}

// Route types
export type RouteParams = {
  analysisId?: string;
};