# Sports Card Grader

A comprehensive tool for analyzing sports cards to predict grading scores across multiple quality criteria.

## Features

- **Edge Analysis**: Evaluates the quality and sharpness of card edges
- **Corner Assessment**: Analyzes corner sharpness and potential damage
- **Surface Quality**: Detects scratches, wear, and print quality issues
- **Centering Evaluation**: Measures card alignment and border uniformity
- **Grade Prediction**: Combines all factors to predict numerical grades (1-10 scale)
- **Multiple Grading Standards**: Supports PSA and BGS grading company standards

## Installation

```bash
# Clone the repository
git clone https://github.com/SedaoAwana/SportsCardGrader.git
cd SportsCardGrader

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Dependencies

- **OpenCV** (opencv-python): For advanced image processing and computer vision
- **NumPy**: For numerical computations
- **Pillow**: For basic image handling

## Usage

### Command Line Interface

```bash
# Analyze a single card image
sports-card-grader analyze card.jpg

# Analyze with detailed technical output
sports-card-grader analyze card.jpg --detailed

# Analyze all images in a directory
sports-card-grader analyze /path/to/cards/ --directory

# Output results in JSON format
sports-card-grader analyze card.jpg --output json

# Use different grading company standards
sports-card-grader analyze card.jpg --company BGS
```

### Python API

```python
from sports_card_grader import CardAnalyzer, GradingSystem

# Initialize analyzer and grading system
analyzer = CardAnalyzer()
grader = GradingSystem()

# Load and analyze a card image
analyzer.load_image("path/to/card.jpg")
analysis_results = analyzer.analyze_all()

# Generate grading report
report = grader.generate_detailed_report(analysis_results)

print(f"Predicted Grade: {report['predicted_grade']}/10")
print(f"Overall Score: {report['overall_score']}/100")
```

## Analysis Components

### 1. Edge Quality (25% weight)
- Detects edge smoothness and sharpness
- Identifies potential wear or damage
- Analyzes card boundary integrity

### 2. Corner Assessment (30% weight)
- Evaluates corner sharpness using Harris corner detection
- Measures gradient strength around corners
- Detects rounding or damage

### 3. Surface Analysis (30% weight)
- Identifies scratches and surface defects
- Analyzes texture uniformity
- Evaluates print quality and clarity

### 4. Centering Evaluation (15% weight)
- Measures card alignment within borders
- Analyzes border uniformity
- Detects off-center or miscut issues

## Grading Scale

| Grade | Score Range | Description |
|-------|-------------|-------------|
| 10    | 95-100      | Gem Mint    |
| 9     | 85-94       | Mint        |
| 8     | 75-84       | Near Mint-Mint |
| 7     | 65-74       | Near Mint   |
| 6     | 55-64       | Excellent-Near Mint |
| 5     | 45-54       | Excellent   |
| 4     | 35-44       | Very Good-Excellent |
| 3     | 25-34       | Very Good   |
| 2     | 15-24       | Good        |
| 1     | 0-14        | Poor        |

## Sample Output

```
🏆 SPORTS CARD GRADING ANALYSIS REPORT
====================================

📊 OVERALL GRADE: 9/10 (Mint)
📈 Overall Score: 87.5/100
🔍 Confidence Level: High

📋 COMPONENT BREAKDOWN:
--------------------------------
       Edges:  85.0/100 (Grade: 9/10, Weight:  25%)
     Corners:  92.0/100 (Grade: 9/10, Weight:  30%)
     Surface:  88.0/100 (Grade: 9/10, Weight:  30%)
   Centering:  82.0/100 (Grade: 8/10, Weight:  15%)

✅ STRENGTHS: Corners
⚠️  AREAS FOR IMPROVEMENT: Centering

💡 SUGGESTIONS:
   • Card shows excellent quality across all criteria

🏢 PSA STANDARDS COMPARISON:
   Meets Gem Mint Standard: ❌ No
   Meets Mint Standard: ✅ Yes
```

## Technical Implementation

The system uses computer vision techniques including:

- **Canny Edge Detection** for edge analysis
- **Harris Corner Detection** for corner evaluation
- **Morphological Operations** for surface defect detection
- **Contour Analysis** for shape and centering assessment
- **Gradient Analysis** for sharpness measurement

## Development Status

- ✅ Core analysis algorithms implemented
- ✅ Grading system with weighted scoring
- ✅ CLI interface
- ✅ Multiple output formats
- ✅ Grading company standards support
- ✅ Comprehensive error handling
- ✅ **Debugging protocols with tracing and causality tracking**
- ⚠️ Currently includes fallback implementation for environments without OpenCV

## Debugging Features

The Sports Card Grader includes comprehensive debugging capabilities:

### Active Tracing
- Function entry/exit logging with the `@trace_function` decorator
- Automatic timing information for performance analysis
- Request ID tracking for causality across function calls

### Usage Examples

```python
from sports_card_grader import configure_debug, get_logger
import logging

# Enable debug mode with full tracing
configure_debug(
    enabled=True,
    trace_enabled=True,
    performance_tracking=True,
    log_level=logging.DEBUG
)

# Use logger with request ID tracking
logger = get_logger(__name__)
logger.info("Starting analysis")
```

### Wolf Fence Algorithm
Binary search debugging to isolate issues:

```python
from sports_card_grader import WolfFenceDebugger

debugger = WolfFenceDebugger()
debugger.checkpoint("Step 1", lambda: condition_check(), {"data": value})
debugger.checkpoint("Step 2", lambda: another_check())
debugger.summary()  # Shows which checkpoint failed first
```

### Test with Debug Mode

```bash
# Run tests with full debug output
python test_demo.py --debug

# Run examples with performance tracking
python examples.py
```

### API Debug Endpoints

- `GET /api/debug/stats` - System statistics and analysis metrics
- `POST /api/debug/configure` - Enable/disable debug mode
- `GET /api/analysis/{id}/debug` - Detailed debug info for specific analysis

## Future Enhancements

- Machine learning models for improved accuracy
- Web interface for easy access
- Batch processing capabilities
- Historical grade tracking
- Integration with grading company APIs
- Mobile app development

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool provides predictions based on image analysis and should not be considered a guarantee of professional grading results. Actual grades from professional grading companies may vary based on factors not detectable through image analysis alone.
