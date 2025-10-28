import React from 'react';
import styled, { keyframes, css } from 'styled-components';
import { LoadingSpinnerProps } from '../../types';

const spin = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const SpinnerContainer = styled.div<LoadingSpinnerProps>`
  display: inline-block;
  
  ${({ size = 'medium' }) => {
    switch (size) {
      case 'small':
        return css`
          width: 16px;
          height: 16px;
        `;
      case 'large':
        return css`
          width: 48px;
          height: 48px;
        `;
      default:
        return css`
          width: 24px;
          height: 24px;
        `;
    }
  }}
`;

const Spinner = styled.div<LoadingSpinnerProps>`
  width: 100%;
  height: 100%;
  border: 2px solid #f3f4f6;
  border-top: 2px solid ${({ color = '#3b82f6' }) => color};
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`;

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = (props) => {
  return (
    <SpinnerContainer {...props}>
      <Spinner {...props} />
    </SpinnerContainer>
  );
};

export default LoadingSpinner;