"""
Command Line Interface for Sports Card Grader
"""

import argparse
import os
import sys
import json
from pathlib import Path

from .card_analyzer import CardAnalyzer
from .grading_system import GradingSystem


def print_analysis_summary(report: dict):
    """Print a formatted summary of the analysis."""
    print("\n" + "="*60)
    print("🏆 SPORTS CARD GRADING ANALYSIS REPORT")
    print("="*60)
    
    print(f"\n📊 OVERALL GRADE: {report['predicted_grade']}/10 ({report['grade_description']})")
    print(f"📈 Overall Score: {report['overall_score']}/100")
    print(f"🔍 Confidence Level: {report['confidence_level']}")
    
    print(f"\n📋 COMPONENT BREAKDOWN:")
    print("-" * 40)
    for component, details in report['component_breakdown'].items():
        print(f"{component.title():>12}: {details['score']:5.1f}/100 "
              f"(Grade: {details['grade']}/10, Weight: {details['weight']*100:3.0f}%)")
    
    if report['strengths']:
        print(f"\n✅ STRENGTHS: {', '.join(report['strengths']).title()}")
    
    if report['weaknesses']:
        print(f"\n⚠️  AREAS FOR IMPROVEMENT: {', '.join(report['weaknesses']).title()}")
    
    print(f"\n💡 SUGGESTIONS:")
    for suggestion in report['improvement_suggestions']:
        print(f"   • {suggestion}")
    
    print("\n" + "="*60)


def print_detailed_analysis(analysis_results: dict):
    """Print detailed technical analysis results."""
    print("\n" + "="*60)
    print("🔬 DETAILED TECHNICAL ANALYSIS")
    print("="*60)
    
    for component, results in analysis_results.items():
        print(f"\n{component.upper()} ANALYSIS:")
        print(f"  Score: {results['score']:.2f}/100")
        
        if 'details' in results and isinstance(results['details'], dict):
            print("  Technical Details:")
            for key, value in results['details'].items():
                if isinstance(value, (int, float)):
                    print(f"    {key}: {value:.2f}")
                else:
                    print(f"    {key}: {value}")


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
        
        if detailed:
            print_detailed_analysis(analysis_results)
        
        if grading_company:
            print(f"\n🏢 {grading_company} STANDARDS COMPARISON:")
            print(f"   Meets Gem Mint Standard: {'✅ Yes' if company_comparison['meets_gem_mint'] else '❌ No'}")
            print(f"   Meets Mint Standard: {'✅ Yes' if company_comparison['meets_mint'] else '❌ No'}")
    
    return report


def analyze_directory(directory_path: str, detailed: bool = False, 
                     output_format: str = "text", grading_company: str = "PSA"):
    """Analyze all images in a directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    for file_path in Path(directory_path).rglob('*'):
        if file_path.suffix.lower() in image_extensions:
            image_files.append(str(file_path))
    
    if not image_files:
        print(f"No image files found in {directory_path}")
        return
    
    print(f"📁 Found {len(image_files)} image(s) to analyze")
    
    results = []
    for image_path in image_files:
        try:
            result = analyze_image(image_path, detailed, output_format, grading_company)
            results.append(result)
            print()  # Add spacing between analyses
        except Exception as e:
            print(f"❌ Error analyzing {image_path}: {e}")
    
    if output_format == "json":
        return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sports Card Grader - Analyze card quality for grading prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sports-card-grader analyze card.jpg
  sports-card-grader analyze card.jpg --detailed
  sports-card-grader analyze /path/to/cards/ --directory
  sports-card-grader analyze card.jpg --output json --company BGS
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
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        try:
            if args.directory:
                results = analyze_directory(args.path, args.detailed, 
                                          args.output, args.company)
            else:
                results = analyze_image(args.path, args.detailed, 
                                      args.output, args.company)
            
            if args.output == 'json':
                print(json.dumps(results, indent=2))
                
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'version':
        from . import __version__
        print(f"Sports Card Grader v{__version__}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()