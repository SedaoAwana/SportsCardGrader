import React from 'react';
import styled, { css } from 'styled-components';
import { ButtonProps } from '../../types';

const StyledButton = styled.button<ButtonProps>`
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  ${({ size = 'medium' }) => {
    switch (size) {
      case 'small':
        return css`
          padding: 8px 16px;
          font-size: 14px;
          min-height: 36px;
        `;
      case 'large':
        return css`
          padding: 16px 32px;
          font-size: 18px;
          min-height: 52px;
        `;
      default:
        return css`
          padding: 12px 24px;
          font-size: 16px;
          min-height: 44px;
        `;
    }
  }}

  ${({ variant = 'primary' }) => {
    switch (variant) {
      case 'secondary':
        return css`
          background-color: #f3f4f6;
          color: #374151;
          border: 1px solid #d1d5db;
          
          &:hover:not(:disabled) {
            background-color: #e5e7eb;
            border-color: #9ca3af;
          }
        `;
      case 'danger':
        return css`
          background-color: #ef4444;
          color: white;
          
          &:hover:not(:disabled) {
            background-color: #dc2626;
          }
        `;
      default:
        return css`
          background-color: #3b82f6;
          color: white;
          
          &:hover:not(:disabled) {
            background-color: #2563eb;
          }
        `;
    }
  }}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

export const Button: React.FC<ButtonProps> = ({ children, ...props }) => {
  return <StyledButton {...props}>{children}</StyledButton>;
};

export default Button;