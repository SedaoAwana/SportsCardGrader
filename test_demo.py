#!/usr/bin/env python3
"""
Simple test script for Sports Card Grader
"""

import sys
import os

# Add the package to Python path
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sports_card_grader import CardAnalyzer, GradingSystem


def test_card_analysis():
    """Test the card analysis system with sample files."""
    
    print("🏆 SPORTS CARD GRADER - DEMONSTRATION")
    print("=" * 50)
    
    # Initialize components
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    # Test files
    sample_dir = "/home/runner/work/SportsCardGrader/SportsCardGrader/sample_images"
    test_files = [
        "mint_condition_card.jpg",
        "poor_corner_damage.jpg", 
        "surface_scratch_card.jpg",
        "offcenter_miscut.jpg",
        "gem_mint_perfect.jpg",
        "regular_card.jpg"
    ]
    
    for test_file in test_files:
        file_path = os.path.join(sample_dir, test_file)
        
        print(f"\n📋 Analyzing: {test_file}")
        print("-" * 40)
        
        # Load and analyze
        if analyzer.load_image(file_path):
            analysis_results = analyzer.analyze_all()
            report = grader.generate_detailed_report(analysis_results)
            
            # Print results
            print(f"Overall Grade: {report['predicted_grade']}/10 ({report['grade_description']})")
            print(f"Overall Score: {report['overall_score']:.1f}/100")
            print(f"Confidence: {report['confidence_level']}")
            
            print("\nComponent Scores:")
            for component, details in report['component_breakdown'].items():
                print(f"  {component.title():>10}: {details['score']:5.1f}/100 (Grade: {details['grade']}/10)")
            
            if report['improvement_suggestions']:
                print(f"\nSuggestions: {report['improvement_suggestions'][0]}")
        else:
            print("❌ Failed to load image")
    
    print(f"\n{'=' * 50}")
    print("✅ Demonstration complete!")
    print("\nNOTE: This is a simplified demonstration version.")
    print("The full implementation would use OpenCV for actual image analysis.")


if __name__ == "__main__":
    test_card_analysis()