import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Zap, Shield, Target } from 'lucide-react';
import { MainLayout } from '../templates';
import { Button, Card, LoadingSpinner, ProgressBar } from '../atoms';
import { FileUpload } from '../molecules';
import { AnalysisResults } from '../organisms';
import { useAnalysis } from '../../hooks';
import { SportsCardAPI } from '../../services/api';

const HomeContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const HeroSection = styled.div`
  text-align: center;
  margin-bottom: 48px;
`;

const HeroTitle = styled.h1`
  font-size: 48px;
  font-weight: 800;
  color: #1f2937;
  margin: 0 0 16px 0;
  line-height: 1.1;
  
  @media (max-width: 768px) {
    font-size: 36px;
  }
`;

const HeroSubtitle = styled.p`
  font-size: 20px;
  color: #6b7280;
  margin: 0 0 32px 0;
  
  @media (max-width: 768px) {
    font-size: 18px;
  }
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
`;

const FeatureCard = styled(Card)`
  padding: 24px;
  text-align: center;
`;

const FeatureIcon = styled.div`
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
`;

const FeatureTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
`;

const FeatureDescription = styled.p`
  font-size: 14px;
  color: #6b7280;
  margin: 0;
`;

const AnalysisSection = styled(Card)`
  padding: 32px;
  margin-bottom: 32px;
`;

const SectionTitle = styled.h2`
  font-size: 24px;
  font-weight: 700;
  color: #374151;
  margin: 0 0 24px 0;
  text-align: center;
`;

const ProgressSection = styled.div`
  margin: 32px 0;
  text-align: center;
`;

const ProgressText = styled.div`
  font-size: 16px;
  color: #374151;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
`;

const ErrorMessage = styled.div`
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 16px;
  border-radius: 8px;
  margin: 16px 0;
  text-align: center;
`;

const HealthStatus = styled.div`
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  color: #0369a1;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 24px;
  text-align: center;
  font-size: 14px;
`;

export const HomePage: React.FC = () => {
  const [analysis, { startAnalysis, reset }] = useAnalysis();
  const [apiHealth, setApiHealth] = useState<string | null>(null);

  useEffect(() => {
    // Check API health on component mount
    SportsCardAPI.checkHealth()
      .then(health => {
        if (health.status === 'healthy') {
          setApiHealth('✅ Backend is ready and operational');
        } else {
          setApiHealth(`⚠️ Backend status: ${health.message}`);
        }
      })
      .catch(() => {
        setApiHealth('❌ Backend server is not responding');
      });
  }, []);

  const handleFileSelect = async (file: File) => {
    await startAnalysis(file);
  };

  const handleStartNewAnalysis = () => {
    reset();
  };

  if (analysis.result) {
    return (
      <MainLayout>
        <AnalysisResults
          result={analysis.result}
          onStartNewAnalysis={handleStartNewAnalysis}
        />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <HomeContainer>
        {!analysis.isAnalyzing && (
          <>
            <HeroSection>
              <HeroTitle>Professional Sports Card Grading</HeroTitle>
              <HeroSubtitle>
                Get instant, AI-powered analysis of your trading cards using professional grading standards
              </HeroSubtitle>
            </HeroSection>

            <FeatureGrid>
              <FeatureCard elevated>
                <FeatureIcon>
                  <Zap size={32} color="#3b82f6" />
                </FeatureIcon>
                <FeatureTitle>Instant Analysis</FeatureTitle>
                <FeatureDescription>
                  Get results in seconds with our advanced computer vision technology
                </FeatureDescription>
              </FeatureCard>

              <FeatureCard elevated>
                <FeatureIcon>
                  <Shield size={32} color="#10b981" />
                </FeatureIcon>
                <FeatureTitle>PSA Standards</FeatureTitle>
                <FeatureDescription>
                  Analysis based on official PSA grading criteria and standards
                </FeatureDescription>
              </FeatureCard>

              <FeatureCard elevated>
                <FeatureIcon>
                  <Target size={32} color="#f59e0b" />
                </FeatureIcon>
                <FeatureTitle>Detailed Breakdown</FeatureTitle>
                <FeatureDescription>
                  Comprehensive analysis of edges, corners, surface, and centering
                </FeatureDescription>
              </FeatureCard>
            </FeatureGrid>
          </>
        )}

        <AnalysisSection elevated>
          {apiHealth && (
            <HealthStatus>
              {apiHealth}
            </HealthStatus>
          )}

          <SectionTitle>
            {analysis.isAnalyzing ? 'Analyzing Your Card' : 'Upload Your Card'}
          </SectionTitle>

          {!analysis.isAnalyzing && (
            <FileUpload
              onFileSelect={handleFileSelect}
              accept="image/*"
              maxSizeMB={10}
            />
          )}

          {analysis.isAnalyzing && (
            <ProgressSection>
              <ProgressText>
                <LoadingSpinner size="small" />
                {analysis.status}
              </ProgressText>
              
              <ProgressBar
                progress={analysis.progress}
                showPercentage={true}
                color="#3b82f6"
                height="16px"
              />
            </ProgressSection>
          )}

          {analysis.error && (
            <ErrorMessage>
              Analysis failed: {analysis.error}
              <div style={{ marginTop: '12px' }}>
                <Button
                  variant="secondary"
                  size="small"
                  onClick={reset}
                >
                  Try Again
                </Button>
              </div>
            </ErrorMessage>
          )}
        </AnalysisSection>
      </HomeContainer>
    </MainLayout>
  );
};

export default HomePage;