import React from 'react';
import styled from 'styled-components';
import { ComponentBreakdownProps } from '../../types';
import { formatScore, getGradeColor } from '../../utils';
import { Card, ProgressBar } from '../atoms';

const BreakdownContainer = styled(Card)`
  padding: 24px;
`;

const Title = styled.h3`
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #374151;
`;

const ComponentItem = styled.div`
  margin-bottom: 20px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const ComponentHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const ComponentName = styled.span`
  font-weight: 600;
  color: #374151;
  text-transform: capitalize;
`;

const ComponentStats = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
`;

const GradeBox = styled.span<{ color: string }>`
  background-color: ${({ color }) => color};
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
`;

const ScoreText = styled.span`
  color: #6b7280;
`;

const WeightText = styled.span`
  color: #9ca3af;
  font-size: 12px;
`;

export const ComponentBreakdown: React.FC<ComponentBreakdownProps> = ({
  breakdown
}) => {
  const components = [
    { key: 'edges', label: 'Edges', data: breakdown.edges },
    { key: 'corners', label: 'Corners', data: breakdown.corners },
    { key: 'surface', label: 'Surface', data: breakdown.surface },
    { key: 'centering', label: 'Centering', data: breakdown.centering },
  ];

  return (
    <BreakdownContainer elevated>
      <Title>Component Analysis</Title>
      
      {components.map(({ key, label, data }) => {
        const gradeColor = getGradeColor(data.grade);
        
        return (
          <ComponentItem key={key}>
            <ComponentHeader>
              <ComponentName>{label}</ComponentName>
              <ComponentStats>
                <GradeBox color={gradeColor}>
                  {data.grade}/10
                </GradeBox>
                <ScoreText>
                  {formatScore(data.score)}
                </ScoreText>
                <WeightText>
                  ({Math.round(data.weight * 100)}% weight)
                </WeightText>
              </ComponentStats>
            </ComponentHeader>
            
            <ProgressBar
              progress={data.score}
              color={gradeColor}
              showPercentage={false}
              height="12px"
            />
          </ComponentItem>
        );
      })}
    </BreakdownContainer>
  );
};

export default ComponentBreakdown;