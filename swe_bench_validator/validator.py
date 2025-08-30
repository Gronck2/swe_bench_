"""
Core SWE-bench data point validator implementation.

Uses the official SWE-bench evaluation harness to validate data points.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# SWE-bench imports - REAL evaluation harness
from swebench.harness.run_evaluation import main as run_evaluation

from .config import ValidationConfig, DEFAULT_CONFIG
from .utils import load_data_point, convert_to_prediction_format, parse_test_list

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of validating a single data point."""
    
    def __init__(self, instance_id: str, success: bool, error_message: str = None, 
                 details: Dict[str, Any] = None):
        self.instance_id = instance_id
        self.success = success
        self.error_message = error_message
        self.details = details or {}
    
    def __str__(self):
        status = "PASSED" if self.success else "FAILED"
        if self.error_message:
            return f"{self.instance_id}: {status} - {self.error_message}"
        return f"{self.instance_id}: {status}"


class SWEBenchValidator:
    """
    SWE-bench data point validator using official evaluation harness.
    
    This validator:
    1. Loads data points from JSON files
    2. Converts them to SWE-bench prediction format
    3. Uses swebench.harness.run_evaluation to test patches
    4. Validates that FAIL_TO_PASS and PASS_TO_PASS tests work correctly
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize validator.
        
        Args:
            config: Validation configuration (uses default if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure directories exist
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        self.config.results_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_single_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single data point file using SWE-bench evaluation harness.
        
        Args:
            file_path: Path to the data point JSON file
            
        Returns:
            ValidationResult object
        """
        self.logger.info(f"Validating data point: {file_path}")
        
        try:
            # Step 1: Load data point
            data_point = load_data_point(file_path)
            instance_id = data_point["instance_id"]
            
            self.logger.info(f"Loaded instance: {instance_id}")
            
            # Step 2: Parse test lists
            fail_to_pass_tests = parse_test_list(data_point["FAIL_TO_PASS"])
            pass_to_pass_tests = parse_test_list(data_point["PASS_TO_PASS"])
            
            self.logger.info(f"Tests - FAIL_TO_PASS: {len(fail_to_pass_tests)}, PASS_TO_PASS: {len(pass_to_pass_tests)}")
            
            # Step 3: Convert to prediction format
            prediction = convert_to_prediction_format(data_point)
            
            # Step 4: Run SWE-bench evaluation harness
            result = self._run_swebench_evaluation(instance_id, prediction)
            
            return result
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ValidationResult(
                instance_id=file_path.stem,
                success=False,
                error_message=error_msg
            )
    
    def _run_swebench_evaluation(self, instance_id: str, prediction: Dict[str, Any]) -> ValidationResult:
        """
        Run SWE-bench evaluation harness for a single instance.
        
        This is the REAL implementation that uses swebench.harness.run_evaluation
        
        Args:
            instance_id: SWE-bench instance identifier
            prediction: Prediction in SWE-bench format
            
        Returns:
            ValidationResult object
        """
        self.logger.info(f"Running SWE-bench evaluation for {instance_id}")
        
        try:
            # Create temporary predictions file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                json.dump(prediction, f)
                f.write('\n')
                predictions_path = f.name
            
            # Get timeout for this instance
            timeout = self.config.get_timeout_for_instance(instance_id)
            
            # Run the REAL SWE-bench evaluation harness
            self.logger.info(f"Calling swebench.harness.run_evaluation with timeout={timeout}")
            
            # This is the ACTUAL call to SWE-bench evaluation harness - NO SIMULATION!
            run_evaluation(
                dataset_name=self.config.dataset_name,
                split=self.config.split,
                instance_ids=[instance_id],
                predictions_path=predictions_path,
                max_workers=self.config.max_workers,
                force_rebuild=True,  # Force rebuild to test different patches
                cache_level="none",
                clean=True,
                open_file_limit=100,
                run_id=f"validation_{instance_id}_{hash(prediction['model_patch']) % 10000}",
                timeout=timeout,
                namespace=None,
                rewrite_reports=False,
                modal=False,
                report_dir=str(self.config.results_dir)
            )
            
            # Parse results from evaluation
            # SWE-bench creates files like "gold.validation_{instance_id}_{hash}.json"
            import glob
            results_pattern = f"gold.validation_{instance_id}_*.json"
            results_files = glob.glob(results_pattern)
            
            if not results_files:
                # Fallback to simple pattern
                results_file = Path(f"gold.validation_{instance_id}.json")
            else:
                # Use the most recent file
                results_file = Path(sorted(results_files)[-1])
            
            if results_file.exists():
                with open(results_file, 'r') as f:
                    evaluation_results = json.load(f)
                
                # Determine success based on SWE-bench results
                resolved_ids = evaluation_results.get("resolved_ids", [])
                resolved = instance_id in resolved_ids
                
                if resolved:
                    return ValidationResult(
                        instance_id=instance_id,
                        success=True,
                        details=evaluation_results
                    )
                else:
                    # Create detailed error message based on SWE-bench results
                    error_details = []
                    resolved_count = evaluation_results.get("resolved_instances", 0)
                    unresolved_count = evaluation_results.get("unresolved_instances", 0)
                    
                    if resolved_count == 0 and unresolved_count > 0:
                        error_details.append("Patch did not resolve the issue")
                        error_details.append("This means either:")
                        error_details.append("  • FAIL_TO_PASS tests still fail after applying the patch")
                        error_details.append("  • PASS_TO_PASS tests now fail due to the patch")
                        error_details.append("  • Patch failed to apply to the repository")
                    
                    error_message = "\n".join(error_details) if error_details else "Instance not resolved"
                    
                    return ValidationResult(
                        instance_id=instance_id,
                        success=False,
                        error_message=error_message,
                        details=evaluation_results
                    )
            else:
                return ValidationResult(
                    instance_id=instance_id,
                    success=False,
                    error_message=f"Results file not found: {results_file}"
                )
                
        except Exception as e:
            error_str = str(e)
            
            # Create detailed error message based on error type
            if "prediction IDs not found in dataset" in error_str:
                error_msg = f"Instance ID '{instance_id}' not found in SWE-bench dataset.\n\n"
                error_msg += "This error occurs when:\n"
                error_msg += "  • The instance_id doesn't exist in the official SWE-bench dataset\n"
                error_msg += "  • There's a typo in the instance_id field\n"
                error_msg += "  • You're using a custom instance_id not from SWE-bench\n\n"
                error_msg += "Solution:\n"
                error_msg += "  • Use an existing instance_id from SWE-bench dataset\n"
                error_msg += "  • Check the instance_id spelling and format\n"
                error_msg += f"  • Original error: {error_str}"
            elif "timeout" in error_str.lower():
                error_msg = f"SWE-bench evaluation timed out after {self.config.get_timeout_for_instance(instance_id)}s.\n\n"
                error_msg += "This error occurs when:\n"
                error_msg += "  • Tests take too long to execute\n"
                error_msg += "  • Docker container becomes unresponsive\n"
                error_msg += "  • Repository has complex dependencies\n\n"
                error_msg += "Solution:\n"
                error_msg += "  • Increase timeout with --timeout option\n"
                error_msg += "  • Check Docker resources (CPU, memory)\n"
                error_msg += f"  • Original error: {error_str}"
            else:
                error_msg = f"SWE-bench evaluation failed.\n\n"
                error_msg += "Common causes:\n"
                error_msg += "  • Docker not running or not accessible\n"
                error_msg += "  • Insufficient system resources (RAM, disk space)\n"
                error_msg += "  • Network issues downloading dependencies\n"
                error_msg += "  • Malformed patch that cannot be applied\n\n"
                error_msg += f"Technical details: {error_str}"
            
            self.logger.error(error_msg)
            
            return ValidationResult(
                instance_id=instance_id,
                success=False,
                error_message=error_msg
            )
        finally:
            # Clean up temporary predictions file
            try:
                Path(predictions_path).unlink()
            except:
                pass