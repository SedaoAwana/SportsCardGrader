import React from 'react';
import styled from 'styled-components';
import { Eye, Cpu, Target, Award } from 'lucide-react';
import { MainLayout } from '../templates';
import { Card } from '../atoms';

const AboutContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const HeroSection = styled.div`
  text-align: center;
  margin-bottom: 48px;
`;

const Title = styled.h1`
  font-size: 36px;
  font-weight: 800;
  color: #1f2937;
  margin: 0 0 16px 0;
`;

const Subtitle = styled.p`
  font-size: 18px;
  color: #6b7280;
  margin: 0;
`;

const Section = styled(Card)`
  padding: 32px;
  margin-bottom: 32px;
`;

const SectionTitle = styled.h2`
  font-size: 24px;
  font-weight: 700;
  color: #374151;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const SectionContent = styled.div`
  color: #4b5563;
  line-height: 1.6;
`;

const FeatureList = styled.ul`
  margin: 16px 0;
  padding-left: 24px;
`;

const FeatureItem = styled.li`
  margin-bottom: 8px;
`;

const GradingTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
`;

const TableHeader = styled.th`
  background-color: #f9fafb;
  padding: 12px;
  text-align: left;
  border: 1px solid #e5e7eb;
  font-weight: 600;
`;

const TableCell = styled.td`
  padding: 12px;
  border: 1px solid #e5e7eb;
`;

const GradeCell = styled(TableCell)<{ grade: number }>`
  font-weight: 600;
  color: ${({ grade }) => {
    if (grade >= 9) return '#10b981';
    if (grade >= 7) return '#f59e0b';
    if (grade >= 5) return '#f97316';
    return '#ef4444';
  }};
`;

export const AboutPage: React.FC = () => {
  return (
    <MainLayout>
      <AboutContainer>
        <HeroSection>
          <Title>About SportsCardGrader</Title>
          <Subtitle>
            Professional-grade sports card analysis powered by advanced computer vision
          </Subtitle>
        </HeroSection>

        <Section elevated>
          <SectionTitle>
            <Eye size={24} color="#3b82f6" />
            How It Works
          </SectionTitle>
          <SectionContent>
            <p>
              Our advanced computer vision system analyzes your sports card images using the same criteria 
              that professional grading companies like PSA use to evaluate card quality.
            </p>
            <FeatureList>
              <FeatureItem><strong>Edge Analysis:</strong> Evaluates edge sharpness and detects wear or damage</FeatureItem>
              <FeatureItem><strong>Corner Assessment:</strong> Analyzes corner sharpness and potential rounding</FeatureItem>
              <FeatureItem><strong>Surface Quality:</strong> Detects scratches, wear, and print quality issues</FeatureItem>
              <FeatureItem><strong>Centering Evaluation:</strong> Measures card alignment and border uniformity</FeatureItem>
            </FeatureList>
            <p>
              Each component is weighted according to professional grading standards, and the results are 
              combined to produce an overall grade prediction with detailed explanations.
            </p>
          </SectionContent>
        </Section>

        <Section elevated>
          <SectionTitle>
            <Cpu size={24} color="#10b981" />
            Technology Stack
          </SectionTitle>
          <SectionContent>
            <p>
              Our system combines multiple cutting-edge technologies to deliver accurate card analysis:
            </p>
            <FeatureList>
              <FeatureItem><strong>OpenCV:</strong> Advanced computer vision for image processing</FeatureItem>
              <FeatureItem><strong>Canny Edge Detection:</strong> For precise edge quality analysis</FeatureItem>
              <FeatureItem><strong>Harris Corner Detection:</strong> For corner sharpness evaluation</FeatureItem>
              <FeatureItem><strong>Morphological Operations:</strong> For surface defect detection</FeatureItem>
              <FeatureItem><strong>Contour Analysis:</strong> For shape and centering assessment</FeatureItem>
            </FeatureList>
            <p>
              The frontend is built with React and TypeScript using atomic design principles, 
              ensuring a responsive and user-friendly experience across all devices.
            </p>
          </SectionContent>
        </Section>

        <Section elevated>
          <SectionTitle>
            <Target size={24} color="#f59e0b" />
            Grading Standards
          </SectionTitle>
          <SectionContent>
            <p>
              Our analysis follows PSA (Professional Sports Authenticator) grading standards, 
              the most widely recognized grading company in the sports card industry.
            </p>
            
            <GradingTable>
              <thead>
                <tr>
                  <TableHeader>Grade</TableHeader>
                  <TableHeader>Label</TableHeader>
                  <TableHeader>Score Range</TableHeader>
                  <TableHeader>Description</TableHeader>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <GradeCell grade={10}>10</GradeCell>
                  <TableCell>Gem Mint</TableCell>
                  <TableCell>95-100</TableCell>
                  <TableCell>Virtually perfect card</TableCell>
                </tr>
                <tr>
                  <GradeCell grade={9}>9</GradeCell>
                  <TableCell>Mint</TableCell>
                  <TableCell>87-94</TableCell>
                  <TableCell>Superb condition with minor flaws</TableCell>
                </tr>
                <tr>
                  <GradeCell grade={8}>8</GradeCell>
                  <TableCell>Near Mint-Mint</TableCell>
                  <TableCell>78-86</TableCell>
                  <TableCell>High-end card with slight imperfections</TableCell>
                </tr>
                <tr>
                  <GradeCell grade={7}>7</GradeCell>
                  <TableCell>Near Mint</TableCell>
                  <TableCell>68-77</TableCell>
                  <TableCell>Slight surface wear visible</TableCell>
                </tr>
                <tr>
                  <GradeCell grade={6}>6</GradeCell>
                  <TableCell>Excellent-Near Mint</TableCell>
                  <TableCell>58-67</TableCell>
                  <TableCell>Visible wear but appealing</TableCell>
                </tr>
                <tr>
                  <GradeCell grade={5}>5</GradeCell>
                  <TableCell>Excellent</TableCell>
                  <TableCell>45-57</TableCell>
                  <TableCell>Light wear throughout</TableCell>
                </tr>
              </tbody>
            </GradingTable>
          </SectionContent>
        </Section>

        <Section elevated>
          <SectionTitle>
            <Award size={24} color="#dc2626" />
            Important Disclaimer
          </SectionTitle>
          <SectionContent>
            <p>
              <strong>This tool provides predictions based on image analysis and should not be considered 
              a guarantee of professional grading results.</strong>
            </p>
            <p>
              Actual grades from professional grading companies may vary based on factors not detectable 
              through image analysis alone, including:
            </p>
            <FeatureList>
              <FeatureItem>Print defects that require physical inspection</FeatureItem>
              <FeatureItem>Surface texture and gloss that may not be visible in photos</FeatureItem>
              <FeatureItem>Subtle warping or bending</FeatureItem>
              <FeatureItem>Authentication concerns</FeatureItem>
              <FeatureItem>Grader subjectivity and company standards</FeatureItem>
            </FeatureList>
            <p>
              Use this tool as a helpful reference for understanding your card's condition, 
              but always consult professional grading services for official authentication and grading.
            </p>
          </SectionContent>
        </Section>
      </AboutContainer>
    </MainLayout>
  );
};

export default AboutPage;