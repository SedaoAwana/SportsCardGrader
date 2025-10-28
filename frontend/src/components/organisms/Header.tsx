import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { Trophy, Home, Info, Settings } from 'lucide-react';

const HeaderContainer = styled.header`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const HeaderContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Logo = styled(Link)`
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: white;
  font-size: 24px;
  font-weight: 800;
  
  &:hover {
    opacity: 0.9;
  }
`;

const Navigation = styled.nav`
  display: flex;
  align-items: center;
  gap: 24px;
  
  @media (max-width: 768px) {
    gap: 16px;
  }
`;

const NavLink = styled(Link)<{ active: boolean }>`
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: white;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s ease;
  opacity: ${({ active }) => active ? 1 : 0.8};
  background-color: ${({ active }) => active ? 'rgba(255, 255, 255, 0.1)' : 'transparent'};
  
  &:hover {
    opacity: 1;
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  @media (max-width: 768px) {
    span {
      display: none;
    }
  }
`;

const MobileNavText = styled.span`
  @media (max-width: 768px) {
    display: none;
  }
`;

export const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <HeaderContainer>
      <HeaderContent>
        <Logo to="/">
          <Trophy size={28} />
          <span>SportsCardGrader</span>
        </Logo>
        
        <Navigation>
          <NavLink to="/" active={isActive('/')}>
            <Home size={18} />
            <MobileNavText>Home</MobileNavText>
          </NavLink>
          
          <NavLink to="/about" active={isActive('/about')}>
            <Info size={18} />
            <MobileNavText>About</MobileNavText>
          </NavLink>
          
          <NavLink to="/debug" active={isActive('/debug')}>
            <Settings size={18} />
            <MobileNavText>Debug</MobileNavText>
          </NavLink>
        </Navigation>
      </HeaderContent>
    </HeaderContainer>
  );
};

export default Header;