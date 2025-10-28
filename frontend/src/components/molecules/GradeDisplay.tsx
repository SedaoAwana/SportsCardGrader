import React from 'react';
import styled from 'styled-components';
import { GradeDisplayProps } from '../../types';
import { formatGrade, formatScore, getGradeColor, getConfidenceColor } from '../../utils';
import { Card } from '../atoms';

const GradeContainer = styled(Card)`
  padding: 24px;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
`;

const GradeNumber = styled.div<{ color: string }>`
  font-size: 64px;
  font-weight: 800;
  line-height: 1;
  color: ${({ color }) => color};
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const GradeDescription = styled.div`
  font-size: 20px;
  font-weight: 600;
  margin-top: 8px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
`;

const ScoreContainer = styled.div`
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ScoreItem = styled.div`
  text-align: center;
`;

const ScoreLabel = styled.div`
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ScoreValue = styled.div`
  font-size: 18px;
  font-weight: 600;
`;

const ConfidenceBadge = styled.span<{ color: string }>`
  background-color: ${({ color }) => color};
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
`;

export const GradeDisplay: React.FC<GradeDisplayProps> = ({
  grade,
  description,
  score,
  confidenceLevel
}) => {
  const gradeColor = getGradeColor(grade);
  const confidenceColor = getConfidenceColor(confidenceLevel);

  return (
    <GradeContainer elevated>
      <GradeNumber color={gradeColor}>
        {formatGrade(grade)}
      </GradeNumber>
      
      <GradeDescription>
        {description}
      </GradeDescription>
      
      <ScoreContainer>
        <ScoreItem>
          <ScoreLabel>Overall Score</ScoreLabel>
          <ScoreValue>{formatScore(score)}</ScoreValue>
        </ScoreItem>
        
        <ScoreItem>
          <ScoreLabel>Confidence</ScoreLabel>
          <ConfidenceBadge color={confidenceColor}>
            {confidenceLevel}
          </ConfidenceBadge>
        </ScoreItem>
      </ScoreContainer>
    </GradeContainer>
  );
};

export default GradeDisplay;