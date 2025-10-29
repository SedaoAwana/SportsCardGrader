import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Settings, Server, Database, Bug, Download, Trash2, RefreshCw } from 'lucide-react';
import { MainLayout } from '../templates';
import { Button, Card, LoadingSpinner } from '../atoms';
import { SportsCardAPI } from '../../services/api';
import { downloadAsJson } from '../../utils';

const DebugContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
`;

const Title = styled.h1`
  font-size: 32px;
  font-weight: 800;
  color: #1f2937;
  margin: 0 0 32px 0;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Section = styled(Card)`
  padding: 24px;
  margin-bottom: 24px;
`;

const SectionTitle = styled.h2`
  font-size: 20px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const StatusGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`;

const StatusItem = styled.div`
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f9fafb;
`;

const StatusLabel = styled.div`
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
`;

const StatusValue = styled.div<{ status?: 'success' | 'warning' | 'error' }>`
  font-size: 14px;
  font-weight: 600;
  color: ${({ status }) => {
    switch (status) {
      case 'success': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#374151';
    }
  }};
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
`;

const CodeBlock = styled.pre`
  background-color: #1f2937;
  color: #f3f4f6;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.4;
  margin: 16px 0;
`;

const AnalysisItem = styled.div`
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 8px;
  background-color: white;
`;

const AnalysisHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const AnalysisId = styled.code`
  background-color: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #374151;
`;

const AnalysisStatus = styled.span<{ status: string }>`
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  background-color: ${({ status }) => {
    switch (status) {
      case 'completed': return '#d1fae5';
      case 'processing': return '#fef3c7';
      case 'error': return '#fee2e2';
      default: return '#f3f4f6';
    }
  }};
  color: ${({ status }) => {
    switch (status) {
      case 'completed': return '#065f46';
      case 'processing': return '#92400e';
      case 'error': return '#991b1b';
      default: return '#374151';
    }
  }};
`;

export const DebugPage: React.FC = () => {
  const [apiHealth, setApiHealth] = useState<any>(null);
  const [analyses, setAnalyses] = useState<any>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchApiHealth = async () => {
    setLoading(true);
    try {
      const health = await SportsCardAPI.checkHealth();
      setApiHealth(health);
    } catch (error: any) {
      setApiHealth({ status: 'error', message: error.message });
    }
    setLoading(false);
  };

  const fetchAnalyses = async () => {
    setLoading(true);
    try {
      const result = await SportsCardAPI.listAnalyses();
      setAnalyses(result);
    } catch (error: any) {
      setAnalyses({ error: error.message });
    }
    setLoading(false);
  };

  const fetchAnalysisDebug = async (analysisId: string) => {
    setLoading(true);
    try {
      const debug = await SportsCardAPI.getAnalysisDebugInfo(analysisId);
      setSelectedAnalysis(debug);
    } catch (error: any) {
      setSelectedAnalysis({ error: error.message });
    }
    setLoading(false);
  };

  const clearAllAnalyses = async () => {
    if (!analyses?.analyses) return;
    
    setLoading(true);
    for (const analysis of analyses.analyses) {
      try {
        await SportsCardAPI.deleteAnalysis(analysis.analysis_id);
      } catch (error) {
        console.warn('Failed to delete analysis:', analysis.analysis_id);
      }
    }
    await fetchAnalyses();
    setSelectedAnalysis(null);
    setLoading(false);
  };

  const downloadDebugData = () => {
    const debugData = {
      api_health: apiHealth,
      analyses: analyses,
      selected_analysis: selectedAnalysis,
      timestamp: new Date().toISOString(),
    };
    
    downloadAsJson(debugData, `debug-data-${Date.now()}.json`);
  };

  useEffect(() => {
    fetchApiHealth();
    fetchAnalyses();
  }, []);

  return (
    <MainLayout>
      <DebugContainer>
        <Title>
          <Settings size={32} />
          Debug Console
        </Title>

        <Section elevated>
          <SectionTitle>
            <Server size={20} />
            API Health Status
          </SectionTitle>
          
          <ButtonGroup>
            <Button
              variant="secondary"
              size="small"
              onClick={fetchApiHealth}
              disabled={loading}
            >
              <RefreshCw size={16} />
              Refresh
            </Button>
          </ButtonGroup>

          {apiHealth && (
            <StatusGrid>
              <StatusItem>
                <StatusLabel>Status</StatusLabel>
                <StatusValue status={apiHealth.status === 'healthy' ? 'success' : 'error'}>
                  {apiHealth.status}
                </StatusValue>
              </StatusItem>
              
              <StatusItem>
                <StatusLabel>Backend Available</StatusLabel>
                <StatusValue status={apiHealth.backend_available ? 'success' : 'error'}>
                  {apiHealth.backend_available ? 'Yes' : 'No'}
                </StatusValue>
              </StatusItem>
              
              <StatusItem>
                <StatusLabel>OpenCV Available</StatusLabel>
                <StatusValue status={apiHealth.opencv_available ? 'success' : 'warning'}>
                  {apiHealth.opencv_available ? 'Yes' : 'No'}
                </StatusValue>
              </StatusItem>
              
              <StatusItem>
                <StatusLabel>Message</StatusLabel>
                <StatusValue>{apiHealth.message}</StatusValue>
              </StatusItem>
            </StatusGrid>
          )}

          {apiHealth && (
            <CodeBlock>
              {JSON.stringify(apiHealth, null, 2)}
            </CodeBlock>
          )}
        </Section>

        <Section elevated>
          <SectionTitle>
            <Database size={20} />
            Analysis History
          </SectionTitle>
          
          <ButtonGroup>
            <Button
              variant="secondary"
              size="small"
              onClick={fetchAnalyses}
              disabled={loading}
            >
              <RefreshCw size={16} />
              Refresh
            </Button>
            
            <Button
              variant="danger"
              size="small"
              onClick={clearAllAnalyses}
              disabled={loading || !analyses?.analyses?.length}
            >
              <Trash2 size={16} />
              Clear All
            </Button>
            
            <Button
              variant="secondary"
              size="small"
              onClick={downloadDebugData}
              disabled={loading}
            >
              <Download size={16} />
              Download Debug Data
            </Button>
          </ButtonGroup>

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '16px 0' }}>
              <LoadingSpinner size="small" />
              <span>Loading...</span>
            </div>
          )}

          {analyses && (
            <>
              <StatusGrid>
                <StatusItem>
                  <StatusLabel>Total Analyses</StatusLabel>
                  <StatusValue>{analyses.total || 0}</StatusValue>
                </StatusItem>
              </StatusGrid>

              {analyses.analyses && analyses.analyses.length > 0 && (
                <div>
                  <h4>Recent Analyses:</h4>
                  {analyses.analyses.map((analysis: any) => (
                    <AnalysisItem key={analysis.analysis_id}>
                      <AnalysisHeader>
                        <div>
                          <AnalysisId>{analysis.analysis_id}</AnalysisId>
                          <AnalysisStatus status={analysis.status}>
                            {analysis.status}
                          </AnalysisStatus>
                        </div>
                        <Button
                          variant="secondary"
                          size="small"
                          onClick={() => fetchAnalysisDebug(analysis.analysis_id)}
                        >
                          <Bug size={14} />
                          Debug
                        </Button>
                      </AnalysisHeader>
                      
                      <div style={{ fontSize: '12px', color: '#6b7280' }}>
                        {analysis.filename && `File: ${analysis.filename}`}
                        {analysis.progress !== undefined && ` • Progress: ${analysis.progress}%`}
                      </div>
                    </AnalysisItem>
                  ))}
                </div>
              )}
            </>
          )}
        </Section>

        {selectedAnalysis && (
          <Section elevated>
            <SectionTitle>
              <Bug size={20} />
              Analysis Debug Info
            </SectionTitle>
            
            <CodeBlock>
              {JSON.stringify(selectedAnalysis, null, 2)}
            </CodeBlock>
          </Section>
        )}
      </DebugContainer>
    </MainLayout>
  );
};

export default DebugPage;