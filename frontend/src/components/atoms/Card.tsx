import React from 'react';
import styled, { css } from 'styled-components';
import { CardProps } from '../../types';

const StyledCard = styled.div<CardProps>`
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;

  ${({ elevated }) =>
    elevated &&
    css`
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      
      &:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
      }
    `}

  ${({ onClick }) =>
    onClick &&
    css`
      cursor: pointer;
      
      &:hover {
        border-color: #d1d5db;
      }
    `}
`;

export const Card: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <StyledCard className={className} {...props}>
      {children}
    </StyledCard>
  );
};

export default Card;