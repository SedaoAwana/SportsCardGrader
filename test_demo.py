#!/usr/bin/env python3
"""
Sports Card Grader - Comprehensive test and demonstration with debugging
"""

import sys
import os

# Add the package to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sports_card_grader import (
    CardAnalyzer, GradingSystem,
    configure_debug, get_logger, 
    request_context, DebugContext,
    WolfFenceDebugger
)

# Initialize logger
logger = get_logger(__name__)


def test_card_analysis(debug_mode: bool = False):
    """Test the card analysis system with sample files."""
    
    # Configure debug mode
    if debug_mode:
        import logging
        configure_debug(
            enabled=True,
            trace_enabled=True,
            performance_tracking=True,
            log_level=logging.DEBUG
        )
        logger.info("Debug mode enabled")
    else:
        import logging
        configure_debug(
            enabled=True,
            trace_enabled=False,
            performance_tracking=True,
            log_level=logging.INFO
        )
    
    print("🏆 SPORTS CARD GRADER - DEMONSTRATION")
    print("=" * 50)
    
    # Use request context for causality tracking
    with request_context() as req_id:
        logger.info(f"Starting test session with request ID: {req_id}")
        
        # Initialize components
        analyzer = CardAnalyzer()
        grader = GradingSystem()
        
        # Create Wolf Fence debugger for systematic testing
        wolf_fence = WolfFenceDebugger(logger)
        
        # Test files
        sample_dir = os.path.join(current_dir, "sample_images")
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
            
            # Create debug context for this analysis
            debug_ctx = DebugContext(f"analyze_{test_file}")
            debug_ctx.set_metadata("file", test_file)
            
            # Wolf fence checkpoint: file exists
            wolf_fence.checkpoint(
                f"File exists: {test_file}",
                lambda: os.path.exists(file_path),
                {"path": file_path}
            )
            
            # Load and analyze
            debug_ctx.add_event("Loading image")
            if analyzer.load_image(file_path):
                debug_ctx.add_event("Image loaded successfully")
                
                # Wolf fence checkpoint: image loaded
                wolf_fence.checkpoint(
                    f"Image loaded: {test_file}",
                    lambda: analyzer.image is not None if hasattr(analyzer, 'image') else analyzer.image_path is not None
                )
                
                debug_ctx.add_event("Starting analysis")
                analysis_results = analyzer.analyze_all()
                debug_ctx.add_event("Analysis complete")
                
                # Wolf fence checkpoint: analysis produced results
                wolf_fence.checkpoint(
                    f"Analysis complete: {test_file}",
                    lambda: len(analysis_results) > 0,
                    {"num_components": len(analysis_results)}
                )
                
                debug_ctx.add_event("Generating report")
                report = grader.generate_detailed_report(analysis_results)
                debug_ctx.add_event("Report generated")
                
                # Wolf fence checkpoint: report generated
                wolf_fence.checkpoint(
                    f"Report generated: {test_file}",
                    lambda: 'predicted_grade' in report and 'overall_score' in report
                )
                
                # Print results
                print(f"Overall Grade: {report['predicted_grade']}/10 ({report['grade_description']})")
                print(f"Overall Score: {report['overall_score']:.1f}/100")
                print(f"Confidence: {report['confidence_level']}")
                
                print("\nComponent Scores:")
                for component, details in report['component_breakdown'].items():
                    print(f"  {component.title():>10}: {details['score']:5.1f}/100 (Grade: {details['grade']}/10)")
                
                if report['improvement_suggestions']:
                    print(f"\nSuggestions: {report['improvement_suggestions'][0]}")
                
                debug_ctx.add_event("Results displayed")
            else:
                print("❌ Failed to load image")
                debug_ctx.add_event("Image load failed", {"error": "Failed to load"})
            
            # Log debug summary if in debug mode
            if debug_mode:
                debug_ctx.log_summary(logger)
        
        print(f"\n{'=' * 50}")
        print("✅ Demonstration complete!")
        
        # Print Wolf Fence summary
        if debug_mode:
            print("\n" + "=" * 50)
            wolf_fence.summary()
        
        logger.info("Test session completed successfully")


def run_with_debug():
    """Run tests with full debug output."""
    print("Running with DEBUG mode enabled...")
    print("This will show detailed tracing and performance information.\n")
    test_card_analysis(debug_mode=True)


def run_normal():
    """Run tests with normal output."""
    test_card_analysis(debug_mode=False)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Sports Card Grader")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with detailed tracing')
    args = parser.parse_args()
    
    if args.debug:
        run_with_debug()
    else:
        run_normal()