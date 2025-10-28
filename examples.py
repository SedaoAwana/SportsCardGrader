#!/usr/bin/env python3
"""
Sports Card Grader - Comprehensive Usage Examples
"""

import os
import sys
import json

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sports_card_grader import CardAnalyzer, GradingSystem


def example_1_basic_analysis():
    """Example 1: Basic card analysis"""
    print("="*60)
    print("EXAMPLE 1: Basic Card Analysis")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    # Analyze a sample card
    card_path = "sample_images/mint_condition_card.jpg"
    if analyzer.load_image(card_path):
        analysis = analyzer.analyze_all()
        report = grader.generate_detailed_report(analysis)
        
        print(f"Card: {os.path.basename(card_path)}")
        print(f"Predicted Grade: PSA {report['predicted_grade']}/10")
        print(f"Overall Score: {report['overall_score']}/100")
        print(f"Grade Description: {report['grade_description']}")
        print()


def example_2_detailed_analysis():
    """Example 2: Detailed component analysis"""
    print("="*60)
    print("EXAMPLE 2: Detailed Component Analysis")
    print("="*60)
    
    analyzer = CardAnalyzer()
    
    card_path = "sample_images/surface_scratch_card.jpg"
    if analyzer.load_image(card_path):
        # Get individual component analyses
        edges = analyzer.analyze_edges()
        corners = analyzer.analyze_corners()
        surface = analyzer.analyze_surface()
        centering = analyzer.analyze_centering()
        
        print(f"Card: {os.path.basename(card_path)}")
        print(f"Edges Score: {edges['score']:.1f}/100")
        print(f"Corners Score: {corners['score']:.1f}/100") 
        print(f"Surface Score: {surface['score']:.1f}/100")
        print(f"Centering Score: {centering['score']:.1f}/100")
        print()


def example_3_custom_weights():
    """Example 3: Custom grading weights"""
    print("="*60)
    print("EXAMPLE 3: Custom Grading Weights")
    print("="*60)
    
    analyzer = CardAnalyzer()
    
    # Create custom weights (emphasizing corners more)
    custom_weights = {
        "edges": 0.20,      # 20%
        "corners": 0.40,    # 40% (increased from 30%)
        "surface": 0.25,    # 25%
        "centering": 0.15   # 15%
    }
    
    grader_custom = GradingSystem(custom_weights)
    grader_standard = GradingSystem()  # Standard weights
    
    card_path = "sample_images/poor_corner_damage.jpg"
    if analyzer.load_image(card_path):
        analysis = analyzer.analyze_all()
        
        report_standard = grader_standard.generate_detailed_report(analysis)
        report_custom = grader_custom.generate_detailed_report(analysis)
        
        print(f"Card: {os.path.basename(card_path)}")
        print(f"Standard Weights Grade: PSA {report_standard['predicted_grade']}/10 ({report_standard['overall_score']:.1f}/100)")
        print(f"Custom Weights Grade: PSA {report_custom['predicted_grade']}/10 ({report_custom['overall_score']:.1f}/100)")
        print("(Custom weights emphasize corner quality more)")
        print()


def example_4_batch_analysis():
    """Example 4: Batch analysis of multiple cards"""
    print("="*60)
    print("EXAMPLE 4: Batch Analysis")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    sample_dir = "sample_images"
    card_files = [f for f in os.listdir(sample_dir) if f.endswith('.jpg')]
    
    results = []
    for card_file in card_files:
        card_path = os.path.join(sample_dir, card_file)
        if analyzer.load_image(card_path):
            analysis = analyzer.analyze_all()
            report = grader.generate_detailed_report(analysis)
            
            results.append({
                "card": card_file,
                "grade": report['predicted_grade'],
                "score": report['overall_score'],
                "description": report['grade_description']
            })
    
    # Sort by grade (highest first)
    results.sort(key=lambda x: float(x['grade']), reverse=True)
    
    print("BATCH ANALYSIS RESULTS:")
    print("-" * 40)
    for result in results:
        print(f"{result['card']:25} PSA {result['grade']}/10 ({result['score']:5.1f}/100) {result['description']}")
    print()


def example_5_psa_compliance_check():
    """Example 5: PSA compliance detailed check"""
    print("="*60)
    print("EXAMPLE 5: PSA Compliance Analysis")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    card_path = "sample_images/gem_mint_perfect.jpg"
    if analyzer.load_image(card_path):
        analysis = analyzer.analyze_all()
        report = grader.generate_detailed_report(analysis)
        
        print(f"Card: {os.path.basename(card_path)}")
        print(f"Predicted Grade: PSA {report['predicted_grade']}/10")
        
        # Check PSA compliance
        if 'psa_compliance' in report:
            compliance = report['psa_compliance']
            print(f"\nPSA Compliance: {compliance['compliance_summary']}")
            
            print("\nComponent Compliance Details:")
            for component, check in compliance['component_compliance'].items():
                status = "✅ PASS" if check['compliant'] else "❌ FAIL"
                print(f"  {component.title()}: {status} - {check['message']}")
        
        # Check centering specifically
        if 'centering_evaluation' in report:
            centering = report['centering_evaluation']
            print(f"\nCentering Details:")
            print(f"  Estimated Ratio: {centering['estimated_centering_ratio']}")
            print(f"  Required: {centering['required_for_grade']} or better")
            print(f"  Meets Standard: {'✅ Yes' if centering['meets_psa_standard'] else '❌ No'}")
        print()


def example_6_json_output():
    """Example 6: JSON output for integration"""
    print("="*60)
    print("EXAMPLE 6: JSON Output for Integration")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    card_path = "sample_images/regular_card.jpg"
    if analyzer.load_image(card_path):
        analysis = analyzer.analyze_all()
        report = grader.generate_detailed_report(analysis)
        
        # Create JSON output
        json_output = {
            "card_path": card_path,
            "analysis_timestamp": "2024-10-28T19:30:00Z",
            "analysis_results": analysis,
            "grading_report": report
        }
        
        print("JSON Output (truncated for display):")
        print(json.dumps({
            "predicted_grade": report['predicted_grade'],
            "overall_score": report['overall_score'],
            "grade_description": report['grade_description'],
            "component_scores": {k: v['score'] for k, v in report['component_breakdown'].items()}
        }, indent=2))
        print()


def main():
    """Run all examples"""
    print("🏆 SPORTS CARD GRADER - USAGE EXAMPLES")
    print("=" * 60)
    print("This script demonstrates various ways to use the Sports Card Grader")
    print()
    
    try:
        example_1_basic_analysis()
        example_2_detailed_analysis()
        example_3_custom_weights()
        example_4_batch_analysis()
        example_5_psa_compliance_check()
        example_6_json_output()
        
        print("="*60)
        print("✅ All examples completed successfully!")
        print("\nTo run the CLI interface:")
        print("  python sports_card_cli.py analyze sample_images/mint_condition_card.jpg")
        print("  python sports_card_cli.py demo")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")


if __name__ == "__main__":
    main()