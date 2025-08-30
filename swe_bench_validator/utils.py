"""
Utility functions for SWE-bench validator.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)


def load_data_point(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a SWE-bench data point from JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the data point
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        ValueError: If required fields are missing
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data point file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    
    # Validate required fields according to SWE-bench format
    required_fields = [
        'instance_id', 'repo', 'base_commit', 'patch',
        'FAIL_TO_PASS', 'PASS_TO_PASS'
    ]
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        error_msg = f"Invalid SWE-bench data point in {file_path}:\n"
        error_msg += f"Missing required fields: {missing_fields}\n\n"
        error_msg += "Required fields for SWE-bench data points:\n"
        for field in required_fields:
            if field in missing_fields:
                error_msg += f"  ❌ {field} - MISSING\n"
            else:
                error_msg += f"  ✅ {field} - present\n"
        error_msg += "\nPlease ensure your data point includes all required fields."
        raise ValueError(error_msg)
    
    return data


def convert_to_prediction_format(data_point: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a SWE-bench data point to prediction format for evaluation harness.
    
    The prediction format is what the evaluation harness expects:
    {
        "instance_id": "...",
        "model_patch": "...",  # The patch to test (golden patch for validation)
        "model_name_or_path": "gold"
    }
    
    Args:
        data_point: SWE-bench data point dictionary
        
    Returns:
        Dictionary in prediction format
    """
    return {
        "instance_id": data_point["instance_id"],
        "model_patch": data_point["patch"],  # Use golden patch for validation
        "model_name_or_path": "gold"
    }


def parse_test_list(test_string: Union[str, List[str]]) -> List[str]:
    """
    Parse test list from string or list format.
    
    Args:
        test_string: Test specification as string or list
        
    Returns:
        List of test identifiers
    """
    if isinstance(test_string, list):
        return test_string
    
    if isinstance(test_string, str):
        # Handle JSON string format like '["test1", "test2"]'
        if test_string.startswith('[') and test_string.endswith(']'):
            try:
                return json.loads(test_string)
            except json.JSONDecodeError:
                pass
        
        # Handle comma-separated format
        return [test.strip() for test in test_string.split(',') if test.strip()]
    
    return []


def setup_logging(verbose: bool = False, log_file: Path = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
