#!/usr/bin/env python3
"""
Sports Card Grader CLI - Direct executable script
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add current directory to path to import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import our modules with fallback handling
try:
    from sports_card_grader import CardAnalyzer, GradingSystem
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def print_analysis_summary(report: dict):
    """Print a formatted summary of the analysis with PSA standards."""
    print("\n" + "="*70)
    print("🏆 SPORTS CARD GRADING ANALYSIS REPORT (PSA Standards)")
    print("="*70)
    
    print(f"\n📊 PREDICTED PSA GRADE: {report['predicted_grade']}/10 ({report['grade_description']})")
    print(f"📈 Overall Score: {report['overall_score']}/100")
    print(f"🔍 Confidence Level: {report['confidence_level']}")
    
    # Display detailed PSA description
    if 'detailed_description' in report and report['detailed_description']:
        print(f"\n📖 PSA GRADE DESCRIPTION:")
        print(f"   {report['detailed_description']}")
    
    print(f"\n📋 COMPONENT BREAKDOWN:")
    print("-" * 50)
    for component, details in report['component_breakdown'].items():
        compliance_icon = "✅" if report.get('psa_compliance', {}).get('component_compliance', {}).get(component, {}).get('compliant', False) else "⚠️"
        print(f"{compliance_icon} {component.title():>12}: {details['score']:5.1f}/100 "
              f"(Grade: {details['grade']}/10, Weight: {details['weight']*100:3.0f}%)")
    
    # Display centering evaluation
    if 'centering_evaluation' in report:
        centering = report['centering_evaluation']
        centering_icon = "✅" if centering['meets_psa_standard'] else "❌"
        print(f"\n🎯 CENTERING ANALYSIS:")
        print(f"   {centering_icon} Estimated Ratio: {centering['estimated_centering_ratio']}")
        print(f"   Required for PSA {report['predicted_grade']}: {centering['required_for_grade']} or better")
    
    # Display PSA compliance summary
    if 'psa_compliance' in report:
        compliance = report['psa_compliance']
        compliance_icon = "✅" if compliance['overall_compliant'] else "⚠️"
        print(f"\n{compliance_icon} PSA COMPLIANCE: {compliance['compliance_summary']}")
    
    if report['strengths']:
        print(f"\n✅ CARD STRENGTHS: {', '.join(report['strengths']).title()}")
    
    if report['weaknesses']:
        print(f"\n⚠️  AREAS LIMITING GRADE: {', '.join(report['weaknesses']).title()}")
    
    print(f"\n💡 PSA GRADING INSIGHTS:")
    for suggestion in report['improvement_suggestions']:
        print(f"   • {suggestion}")
    
    print("\n" + "="*70)


def analyze_image(image_path: str, detailed: bool = False, 
                 output_format: str = "text", grading_company: str = "PSA") -> dict:
    """Analyze a single image and return results."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Initialize analyzer and grading system
    analyzer = CardAnalyzer()
    grader = GradingSystem()
    
    # Load and analyze image
    if not analyzer.load_image(image_path):
        raise ValueError(f"Failed to load image: {image_path}")
    
    print(f"🔍 Analyzing image: {os.path.basename(image_path)}")
    print("📊 Running analysis components...")
    
    # Perform analysis
    analysis_results = analyzer.analyze_all()
    
    # Generate grading report
    report = grader.generate_detailed_report(analysis_results)
    
    # Add company-specific comparison
    company_comparison = grader.compare_to_standards(analysis_results, grading_company)
    report['company_comparison'] = company_comparison
    
    # Output results
    if output_format == "json":
        return {
            "image_path": image_path,
            "analysis_results": analysis_results,
            "grading_report": report
        }
    else:
        print_analysis_summary(report)
        
        if grading_company and 'company_comparison' in report:
            comp = report['company_comparison']
            print(f"\n🏢 {grading_company} STANDARDS VERIFICATION:")
            print(f"   Meets Gem Mint (10) Standard: {'✅ Yes' if comp['meets_gem_mint'] else '❌ No'}")
            print(f"   Meets Mint (9) Standard: {'✅ Yes' if comp['meets_mint'] else '❌ No'}")
            
            # Show specific standards applied
            if 'standards_applied' in comp:
                standards = comp['standards_applied']
                print(f"   Gem Mint Threshold: {standards.get('gem_mint_threshold', 'N/A')}/100")
                print(f"   Mint Threshold: {standards.get('mint_threshold', 'N/A')}/100")
    
    return report


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sports Card Grader - Analyze card quality for grading prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sports_card_cli.py analyze sample_images/mint_condition_card.jpg
  python sports_card_cli.py analyze sample_images/gem_mint_perfect.jpg --detailed
  python sports_card_cli.py analyze sample_images/ --directory
  python sports_card_cli.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze sports card images')
    analyze_parser.add_argument('path', help='Path to image file or directory')
    analyze_parser.add_argument('--detailed', '-d', action='store_true',
                               help='Show detailed technical analysis')
    analyze_parser.add_argument('--directory', action='store_true',
                               help='Analyze all images in directory')
    analyze_parser.add_argument('--output', '-o', choices=['text', 'json'], 
                               default='text', help='Output format')
    analyze_parser.add_argument('--company', '-c', choices=['PSA', 'BGS'], 
                               default='PSA', help='Grading company standards')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demonstration with sample cards')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        try:
            if args.directory:
                # Analyze directory
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
                image_files = []
                
                for file_path in Path(args.path).rglob('*'):
                    if file_path.suffix.lower() in image_extensions:
                        image_files.append(str(file_path))
                
                if not image_files:
                    print(f"No image files found in {args.path}")
                    return
                
                print(f"📁 Found {len(image_files)} image(s) to analyze")
                
                results = []
                for image_path in image_files:
                    try:
                        result = analyze_image(image_path, args.detailed, args.output, args.company)
                        results.append(result)
                        print()  # Add spacing between analyses
                    except Exception as e:
                        print(f"❌ Error analyzing {image_path}: {e}")
                
                if args.output == 'json':
                    print(json.dumps(results, indent=2))
            else:
                # Analyze single file
                result = analyze_image(args.path, args.detailed, args.output, args.company)
                
                if args.output == 'json':
                    print(json.dumps(result, indent=2))
                
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'demo':
        # Run the demonstration
        print("🏆 SPORTS CARD GRADER - DEMONSTRATION")
        print("=" * 50)
        print("Running analysis on sample cards...")
        
        sample_dir = os.path.join(current_dir, "sample_images")
        if os.path.exists(sample_dir):
            try:
                analyze_image(os.path.join(sample_dir, "gem_mint_perfect.jpg"), output_format="text", grading_company="PSA")
                print("\n" + "="*50)
                print("✅ Demo complete! Try analyzing your own images:")
                print("   python sports_card_cli.py analyze your_card.jpg")
            except Exception as e:
                print(f"Demo error: {e}")
        else:
            print("❌ Sample images not found. Please ensure sample_images directory exists.")
    
    elif args.command == 'version':
        try:
            from sports_card_grader import __version__
            print(f"Sports Card Grader v{__version__}")
        except ImportError:
            print("Sports Card Grader v1.0.0")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()