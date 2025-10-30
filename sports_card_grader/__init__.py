"""
Sports Card Grader - Analyze card quality for grading prediction
"""

__version__ = "1.0.0"
__author__ = "Sports Card Grader Team"

# Import grading system (no external dependencies)
from .grading_system import GradingSystem

# Import debug utilities
from .debug_utils import (
    configure_debug,
    get_logger,
    trace_function,
    timed_operation,
    request_context,
    DebugContext,
    debug_checkpoint,
    WolfFenceDebugger,
    set_request_id,
    get_request_id
)

# Try to import full analyzer, fall back to simple analyzer
try:
    from .card_analyzer import CardAnalyzer
    __all__ = ["CardAnalyzer", "GradingSystem", "configure_debug", "get_logger", 
               "trace_function", "timed_operation", "request_context", "DebugContext",
               "debug_checkpoint", "WolfFenceDebugger"]
except ImportError:
    from .simple_analyzer import SimpleCardAnalyzer as CardAnalyzer
    __all__ = ["CardAnalyzer", "GradingSystem", "configure_debug", "get_logger",
               "trace_function", "timed_operation", "request_context", "DebugContext", 
               "debug_checkpoint", "WolfFenceDebugger"]