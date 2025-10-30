#!/usr/bin/env python3
"""
Sports Card Grader - Comprehensive Usage Examples with Debug Support
"""

import os
import sys
import json

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sports_card_grader import (
    CardAnalyzer, GradingSystem,
    configure_debug, get_logger,
    timed_operation
)

# Initialize logger
logger = get_logger(__name__)


def example_1_basic_analysis():
    """Example 1: Basic card analysis with timing"""
    print("="*60)
    print("EXAMPLE 1: Basic Card Analysis")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    card_path = os.path.join(current_dir, "sample_images", "mint_condition_card.jpg")
    
    with timed_operation("basic_analysis", logger):
        if analyzer.load_image(card_path):
            analysis = analyzer.analyze_all()
            report = grader.generate_detailed_report(analysis)
            
            print(f"Card: {os.path.basename(card_path)}")
            print(f"Predicted Grade: PSA {report['predicted_grade']}/10")
            print(f"Overall Score: {report['overall_score']}/100")
            print(f"Grade Description: {report['grade_description']}")
    print()


def example_2_custom_weights():
    """Example 2: Custom grading weights (emphasizing corners)"""
    print("="*60)
    print("EXAMPLE 2: Custom Grading Weights")
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
    
    card_path = os.path.join(current_dir, "sample_images", "poor_corner_damage.jpg")
    
    if analyzer.load_image(card_path):
        analysis = analyzer.analyze_all()
        
        report_standard = grader_standard.generate_detailed_report(analysis)
        report_custom = grader_custom.generate_detailed_report(analysis)
        
        print(f"Card: {os.path.basename(card_path)}")
        print(f"Standard Weights Grade: PSA {report_standard['predicted_grade']}/10 ({report_standard['overall_score']:.1f}/100)")
        print(f"Custom Weights Grade: PSA {report_custom['predicted_grade']}/10 ({report_custom['overall_score']:.1f}/100)")
        print("(Custom weights emphasize corner quality more)")
    print()


def parse_grade_for_sorting(grade_str: str) -> float:
    """Parse grade string to float for sorting, returning 0 if invalid."""
    try:
        return float(grade_str)
    except (ValueError, TypeError):
        return 0.0


def example_3_batch_analysis():
    """Example 3: Batch analysis with performance tracking"""
    print("="*60)
    print("EXAMPLE 3: Batch Analysis with Performance Tracking")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    sample_dir = os.path.join(current_dir, "sample_images")
    
    if not os.path.exists(sample_dir):
        print(f"Sample directory not found: {sample_dir}")
        return
    
    card_files = [f for f in os.listdir(sample_dir) if f.endswith('.jpg')]
    
    results = []
    
    with timed_operation("batch_analysis", logger):
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
    
    # Sort by grade (highest first), then by score
    results.sort(key=lambda x: (parse_grade_for_sorting(x['grade']), x['score']), reverse=True)
    
    print("\nBATCH ANALYSIS RESULTS:")
    print("-" * 50)
    for result in results:
        print(f"{result['card']:30} PSA {result['grade']}/10 ({result['score']:5.1f}/100) {result['description']}")
    print()


def example_4_json_output():
    """Example 4: JSON output for API integration"""
    print("="*60)
    print("EXAMPLE 4: JSON Output for Integration")
    print("="*60)
    
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    card_path = os.path.join(current_dir, "sample_images", "regular_card.jpg")
    
    if analyzer.load_image(card_path):
        analysis = analyzer.analyze_all()
        report = grader.generate_detailed_report(analysis)
        
        # Create JSON output
        json_output = {
            "card_path": os.path.basename(card_path),
            "predicted_grade": report['predicted_grade'],
            "overall_score": report['overall_score'],
            "grade_description": report['grade_description'],
            "component_scores": {k: v['score'] for k, v in report['component_breakdown'].items()},
            "strengths": report.get('strengths', []),
            "weaknesses": report.get('weaknesses', [])
        }
        
        print("JSON Output:")
        print(json.dumps(json_output, indent=2))
    print()


def main():
    """Run all examples"""
    import logging
    
    # Configure debug mode
    configure_debug(
        enabled=True,
        trace_enabled=False,  # Set to True to see function tracing
        performance_tracking=True,
        log_level=logging.INFO
    )
    
    print("🏆 SPORTS CARD GRADER - USAGE EXAMPLES")
    print("=" * 60)
    print("Demonstrating various ways to use the Sports Card Grader")
    print()
    
    try:
        example_1_basic_analysis()
        example_2_custom_weights()
        example_3_batch_analysis()
        example_4_json_output()
        
        print("="*60)
        print("✅ All examples completed successfully!")
        print("\nTo run with detailed tracing, use test_demo.py --debug")
        print("To run the CLI interface, use:")
        print("  python -m sports_card_grader.cli analyze <image_path>")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"❌ Error running examples: {e}")


if __name__ == "__main__":
    main()