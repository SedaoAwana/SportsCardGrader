import React from 'react';
import styled from 'styled-components';
import { Header } from '../organisms';

const LayoutContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f9fafb;
`;

const MainContent = styled.main`
  flex: 1;
  padding: 32px 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
`;

const Footer = styled.footer`
  background-color: #374151;
  color: white;
  padding: 24px;
  text-align: center;
`;

const FooterContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

const FooterText = styled.p`
  margin: 0 0 8px 0;
  font-size: 14px;
  opacity: 0.9;
`;

const FooterNote = styled.p`
  margin: 0;
  font-size: 12px;
  opacity: 0.7;
`;

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <LayoutContainer>
      <Header />
      
      <MainContent>
        {children}
      </MainContent>
      
      <Footer>
        <FooterContent>
          <FooterText>
            © 2024 SportsCardGrader. Powered by advanced computer vision technology.
          </FooterText>
          <FooterNote>
            This tool provides predictions based on image analysis and should not be considered 
            a guarantee of professional grading results.
          </FooterNote>
        </FooterContent>
      </Footer>
    </LayoutContainer>
  );
};

export default MainLayout;