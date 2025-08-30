"""
Configuration settings for SWE-bench validator.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ValidationConfig:
    """Configuration for validation process."""
    
    # Timeout settings (in seconds)
    default_timeout: int = 1800  # 30 minutes
    timeout_overrides: Optional[Dict[str, int]] = None
    
    # Resource limits
    max_workers: int = 1  # Conservative default for stability
    
    # Directories
    temp_dir: Path = Path("/tmp/swebench-validation")
    log_dir: Path = Path("logs")
    results_dir: Path = Path("results")
    
    # SWE-bench settings
    dataset_name: str = "princeton-nlp/SWE-bench"
    split: str = "test"
    
    def __post_init__(self):
        if self.timeout_overrides is None:
            self.timeout_overrides = {
                # Repositories that typically need more time
                "django": 2400,  # 40 minutes
                "scikit-learn": 3000,  # 50 minutes
                "matplotlib": 2100,  # 35 minutes
            }
        
        # Ensure directories exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def get_timeout_for_instance(self, instance_id: str) -> int:
        """Get timeout for specific instance based on repository."""
        repo = instance_id.split("__")[0] if "__" in instance_id else "default"
        return self.timeout_overrides.get(repo, self.default_timeout)


# Default configuration instance
DEFAULT_CONFIG = ValidationConfig()
