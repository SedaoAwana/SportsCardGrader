import React from 'react';
import styled from 'styled-components';
import { Trophy, Target, Star, AlertCircle } from 'lucide-react';
import { AnalysisResultsProps } from '../../types';
import { Button } from '../atoms';
import { GradeDisplay, ComponentBreakdown } from '../molecules';

const ResultsContainer = styled.div`
  display: grid;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const HeaderSection = styled.div`
  text-align: center;
  margin-bottom: 32px;
`;

const Title = styled.h1`
  font-size: 32px;
  font-weight: 800;
  color: #1f2937;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
`;

const Subtitle = styled.p`
  font-size: 16px;
  color: #6b7280;
  margin: 0;
`;

const MainContent = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const DetailsSection = styled.div`
  display: grid;
  gap: 24px;
`;

const DetailsCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
`;

const DetailsTitle = styled.h3`
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ListItem = styled.li`
  margin-bottom: 8px;
  color: #374151;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const StrengthsList = styled.ul`
  margin: 0;
  padding-left: 20px;
  color: #059669;
`;

const WeaknessesList = styled.ul`
  margin: 0;
  padding-left: 20px;
  color: #dc2626;
`;

const SuggestionsList = styled.ul`
  margin: 0;
  padding-left: 20px;
  color: #374151;
`;

const CenteringInfo = styled.div`
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
`;

const CenteringText = styled.div`
  font-size: 14px;
  color: #374151;
  margin-bottom: 4px;
`;

const ComplianceIndicator = styled.span<{ compliant: boolean }>`
  color: ${({ compliant }) => compliant ? '#059669' : '#dc2626'};
  font-weight: 600;
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
  }
`;

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({
  result,
  onStartNewAnalysis
}) => {
  return (
    <ResultsContainer>
      <HeaderSection>
        <Title>
          <Trophy size={32} color="#f59e0b" />
          Analysis Complete
        </Title>
        <Subtitle>
          Your card has been analyzed using professional grading standards
        </Subtitle>
      </HeaderSection>

      <MainContent>
        <GradeDisplay
          grade={result.predicted_grade}
          description={result.grade_description}
          score={result.overall_score}
          confidenceLevel={result.confidence_level}
        />

        <ComponentBreakdown breakdown={result.component_breakdown} />
      </MainContent>

      <DetailsSection>
        {result.strengths.length > 0 && (
          <DetailsCard>
            <DetailsTitle>
              <Star size={20} color="#059669" />
              Card Strengths
            </DetailsTitle>
            <StrengthsList>
              {result.strengths.map((strength, index) => (
                <ListItem key={index}>{strength}</ListItem>
              ))}
            </StrengthsList>
          </DetailsCard>
        )}

        {result.weaknesses.length > 0 && (
          <DetailsCard>
            <DetailsTitle>
              <AlertCircle size={20} color="#dc2626" />
              Areas Limiting Grade
            </DetailsTitle>
            <WeaknessesList>
              {result.weaknesses.map((weakness, index) => (
                <ListItem key={index}>{weakness}</ListItem>
              ))}
            </WeaknessesList>
          </DetailsCard>
        )}

        {result.improvement_suggestions.length > 0 && (
          <DetailsCard>
            <DetailsTitle>
              <Target size={20} color="#3b82f6" />
              PSA Grading Insights
            </DetailsTitle>
            <SuggestionsList>
              {result.improvement_suggestions.map((suggestion, index) => (
                <ListItem key={index}>{suggestion}</ListItem>
              ))}
            </SuggestionsList>
          </DetailsCard>
        )}

        {result.centering_evaluation && (
          <DetailsCard>
            <DetailsTitle>
              <Target size={20} color="#6b7280" />
              Centering Analysis
            </DetailsTitle>
            <CenteringText>
              <strong>Estimated Ratio:</strong> {result.centering_evaluation.estimated_centering_ratio}
            </CenteringText>
            <CenteringText>
              <strong>Required for Grade {result.predicted_grade}:</strong> {result.centering_evaluation.required_for_grade} or better
            </CenteringText>
            <CenteringInfo>
              <CenteringText>
                <strong>Meets PSA Standard:</strong>{' '}
                <ComplianceIndicator compliant={result.centering_evaluation.meets_psa_standard}>
                  {result.centering_evaluation.meets_psa_standard ? 'Yes ✓' : 'No ✗'}
                </ComplianceIndicator>
              </CenteringText>
            </CenteringInfo>
          </DetailsCard>
        )}

        {result.psa_compliance && (
          <DetailsCard>
            <DetailsTitle>
              <Trophy size={20} color="#f59e0b" />
              PSA Compliance
            </DetailsTitle>
            <CenteringText>
              <strong>Overall Compliant:</strong>{' '}
              <ComplianceIndicator compliant={result.psa_compliance.overall_compliant}>
                {result.psa_compliance.overall_compliant ? 'Yes ✓' : 'No ✗'}
              </ComplianceIndicator>
            </CenteringText>
            <CenteringText>
              <strong>Summary:</strong> {result.psa_compliance.compliance_summary}
            </CenteringText>
          </DetailsCard>
        )}
      </DetailsSection>

      <ActionButtons>
        <Button
          variant="primary"
          size="large"
          onClick={onStartNewAnalysis}
        >
          Analyze Another Card
        </Button>
        
        <Button
          variant="secondary"
          size="large"
          onClick={() => window.print()}
        >
          Print Results
        </Button>
      </ActionButtons>
    </ResultsContainer>
  );
};

export default AnalysisResults;