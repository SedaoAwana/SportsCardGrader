"""
Debug Utilities - Comprehensive debugging and tracing support

Implements:
- Active Tracing: Detailed function call tracing with entry/exit logging
- Causality Tracking: Request IDs to track operations across the call stack
- Performance Monitoring: Timing information for performance analysis
"""

import logging
import time
import functools
import uuid
import traceback
from typing import Any, Callable, Dict, Optional
from contextlib import contextmanager
import sys


# Global debug configuration
_debug_config = {
    "enabled": False,
    "trace_enabled": False,
    "performance_tracking": False,
    "log_level": logging.INFO,
    "request_id": None
}


def configure_debug(
    enabled: bool = True,
    trace_enabled: bool = True,
    performance_tracking: bool = True,
    log_level: int = logging.DEBUG
):
    """
    Configure debugging settings globally.
    
    Args:
        enabled: Enable/disable debug features
        trace_enabled: Enable function call tracing
        performance_tracking: Enable performance timing
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    _debug_config["enabled"] = enabled
    _debug_config["trace_enabled"] = trace_enabled
    _debug_config["performance_tracking"] = performance_tracking
    _debug_config["log_level"] = log_level
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with debug support and request ID tracking.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Add custom filter for request ID
    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            req_id = _debug_config.get("request_id")
            record.request_id = req_id[:8] if req_id else "N/A"
            return True
    
    logger.addFilter(RequestIdFilter())
    return logger


def generate_request_id() -> str:
    """Generate a unique request ID for causality tracking."""
    return str(uuid.uuid4())


def set_request_id(request_id: str):
    """Set the current request ID for causality tracking."""
    _debug_config["request_id"] = request_id


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return _debug_config.get("request_id")


@contextmanager
def request_context(request_id: Optional[str] = None):
    """
    Context manager for request-scoped operations with causality tracking.
    
    Usage:
        with request_context() as req_id:
            # All operations here share the same request ID
            do_something()
    """
    old_request_id = _debug_config.get("request_id")
    new_request_id = request_id or generate_request_id()
    
    try:
        set_request_id(new_request_id)
        yield new_request_id
    finally:
        _debug_config["request_id"] = old_request_id


def trace_function(func: Callable) -> Callable:
    """
    Decorator for active function tracing.
    Logs function entry, exit, and execution time.
    
    Usage:
        @trace_function
        def my_function(arg1, arg2):
            return result
    """
    logger = get_logger(func.__module__)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not _debug_config.get("trace_enabled"):
            return func(*args, **kwargs)
        
        # Log function entry
        func_name = f"{func.__module__}.{func.__name__}"
        args_repr = [repr(a) for a in args[:3]]  # Limit to first 3 args
        kwargs_repr = [f"{k}={v!r}" for k, v in list(kwargs.items())[:3]]
        signature = ", ".join(args_repr + kwargs_repr)
        if len(args) > 3 or len(kwargs) > 3:
            signature += ", ..."
        
        logger.debug(f"→ ENTER {func_name}({signature})")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Log function exit with timing
            if _debug_config.get("performance_tracking"):
                logger.debug(f"← EXIT {func_name} [⏱️  {elapsed:.4f}s] → {type(result).__name__}")
            else:
                logger.debug(f"← EXIT {func_name} → {type(result).__name__}")
            
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"✗ ERROR in {func_name} [⏱️  {elapsed:.4f}s]: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            raise
    
    return wrapper


@contextmanager
def timed_operation(operation_name: str, logger: Optional[logging.Logger] = None):
    """
    Context manager for timing operations.
    
    Usage:
        with timed_operation("image_analysis"):
            analyze_image()
    """
    if logger is None:
        logger = get_logger(__name__)
    
    if not _debug_config.get("performance_tracking"):
        yield
        return
    
    logger.info(f"⏱️  Starting: {operation_name}")
    start_time = time.time()
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"✓ Completed: {operation_name} in {elapsed:.4f}s")


class DebugContext:
    """
    Context for collecting debug information throughout an operation.
    Useful for tracking state and decisions made during processing.
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.request_id = get_request_id() or generate_request_id()
        self.start_time = time.time()
        self.events = []
        self.metadata = {}
        
    def add_event(self, event: str, details: Optional[Dict[str, Any]] = None):
        """Add a debug event."""
        self.events.append({
            "timestamp": time.time() - self.start_time,
            "event": event,
            "details": details or {}
        })
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata about the operation."""
        self.metadata[key] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the debug context."""
        return {
            "operation": self.operation_name,
            "request_id": self.request_id,
            "total_time": time.time() - self.start_time,
            "events": self.events,
            "metadata": self.metadata
        }
    
    def log_summary(self, logger: Optional[logging.Logger] = None):
        """Log the debug summary."""
        if logger is None:
            logger = get_logger(__name__)
        
        summary = self.get_summary()
        logger.info(f"Debug Summary for {self.operation_name}:")
        logger.info(f"  Request ID: {summary['request_id']}")
        logger.info(f"  Total Time: {summary['total_time']:.4f}s")
        logger.info(f"  Events: {len(summary['events'])}")
        
        for event in summary['events']:
            logger.debug(f"  [{event['timestamp']:.4f}s] {event['event']}")


def debug_checkpoint(message: str, data: Optional[Dict[str, Any]] = None):
    """
    Log a debug checkpoint with optional data.
    Useful for tracking progress through complex operations.
    
    Args:
        message: Checkpoint message
        data: Optional data to include
    """
    if not _debug_config.get("enabled"):
        return
    
    logger = get_logger("checkpoint")
    log_msg = f"🔍 CHECKPOINT: {message}"
    
    if data:
        log_msg += f" | Data: {data}"
    
    logger.debug(log_msg)


def log_error_context(error: Exception, context: Dict[str, Any], logger: Optional[logging.Logger] = None):
    """
    Log detailed error context for debugging.
    
    Args:
        error: The exception that occurred
        context: Dictionary with contextual information
        logger: Optional logger instance
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.error(f"Error occurred: {type(error).__name__}: {error}")
    logger.error("Error Context:")
    for key, value in context.items():
        logger.error(f"  {key}: {value}")
    
    if _debug_config.get("enabled"):
        logger.debug(f"Full Traceback:\n{traceback.format_exc()}")


# Wolf Fence Algorithm implementation for binary search debugging
class WolfFenceDebugger:
    """
    Wolf Fence Algorithm for debugging - Binary search approach to find bugs.
    
    Divide the code into sections and test each section to narrow down
    where the problem is occurring.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger(__name__)
        self.checkpoints = []
    
    def checkpoint(self, name: str, condition: Callable[[], bool], data: Optional[Dict] = None):
        """
        Add a checkpoint that tests a condition.
        
        Args:
            name: Name of the checkpoint
            condition: Function that returns True if state is valid
            data: Optional debug data
        """
        try:
            is_valid = condition()
            status = "✓ PASS" if is_valid else "✗ FAIL"
            self.logger.info(f"{status} Checkpoint '{name}'")
            
            if data:
                self.logger.debug(f"  Data: {data}")
            
            self.checkpoints.append({
                "name": name,
                "passed": is_valid,
                "data": data
            })
            
            if not is_valid:
                self.logger.warning(f"⚠️  Problem detected at checkpoint: {name}")
                
            return is_valid
        except Exception as e:
            self.logger.error(f"✗ ERROR at checkpoint '{name}': {e}")
            self.checkpoints.append({
                "name": name,
                "passed": False,
                "error": str(e),
                "data": data
            })
            return False
    
    def get_first_failure(self) -> Optional[Dict]:
        """Get the first checkpoint that failed."""
        for checkpoint in self.checkpoints:
            if not checkpoint.get("passed", False):
                return checkpoint
        return None
    
    def summary(self):
        """Print a summary of all checkpoints."""
        self.logger.info("Wolf Fence Debug Summary:")
        for i, checkpoint in enumerate(self.checkpoints, 1):
            status = "✓" if checkpoint.get("passed", False) else "✗"
            self.logger.info(f"  {i}. {status} {checkpoint['name']}")
        
        first_failure = self.get_first_failure()
        if first_failure:
            self.logger.warning(f"First failure at: {first_failure['name']}")
