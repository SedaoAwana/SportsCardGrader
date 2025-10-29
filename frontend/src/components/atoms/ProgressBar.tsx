import React from 'react';
import styled from 'styled-components';
import { ProgressBarProps } from '../../types';

const ProgressContainer = styled.div<{ height: string }>`
  width: 100%;
  background-color: #f3f4f6;
  border-radius: 8px;
  overflow: hidden;
  height: ${({ height }) => height};
`;

const ProgressFill = styled.div<{ progress: number; color: string }>`
  height: 100%;
  background-color: ${({ color }) => color};
  transition: width 0.3s ease;
  width: ${({ progress }) => Math.min(Math.max(progress, 0), 100)}%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
`;

const PercentageText = styled.span`
  color: white;
  font-size: 12px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
`;

const ExternalPercentage = styled.div`
  margin-top: 4px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
`;

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  showPercentage = true,
  color = '#3b82f6',
  height = '8px'
}) => {
  const percentage = Math.round(Math.min(Math.max(progress, 0), 100));
  
  return (
    <div>
      <ProgressContainer height={height}>
        <ProgressFill progress={percentage} color={color}>
          {showPercentage && height !== '8px' && percentage > 20 && (
            <PercentageText>{percentage}%</PercentageText>
          )}
        </ProgressFill>
      </ProgressContainer>
      {showPercentage && height === '8px' && (
        <ExternalPercentage>{percentage}%</ExternalPercentage>
      )}
    </div>
  );
};

export default ProgressBar;