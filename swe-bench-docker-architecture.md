# SWE-bench Docker Architecture Documentation

## Overview

SWE-bench uses a sophisticated 3-layer Docker architecture to ensure reproducible and isolated evaluation of code patches. This system allows for efficient testing of patches against real-world software engineering tasks while maintaining complete isolation between different evaluation runs.

## 3-Layer Docker Architecture

### Layer 1: Base Images
**Purpose**: Provide fundamental system dependencies and runtime environments

Base images (`build_base_images`) contain:
- **Operating System**: Ubuntu/Debian base with essential system libraries
- **System Dependencies**: Core packages like `git`, `curl`, `wget`, build tools
- **Programming Language Runtimes**: Python, Java, Node.js, etc. (version-specific)
- **Package Managers**: `pip`, `npm`, `maven`, etc.
- **Docker Utilities**: Tools for container management

**Building Process**:
```python
from swebench import build_base_images
import docker

client = docker.from_env()
build_base_images(client, dataset, force_rebuild=False)
```

**Characteristics**:
- Built infrequently (only when system dependencies change)
- Shared across multiple repositories and instances
- Cached for performance optimization

### Layer 2: Environment Images
**Purpose**: Install repository-specific dependencies and development tools

Environment images (`build_env_images`) extend base images with:
- **Repository Dependencies**: All packages from `requirements.txt`, `setup.py`, `pyproject.toml`
- **Development Tools**: Testing frameworks (pytest, unittest), linters, formatters
- **Build Dependencies**: Compilation tools, headers, libraries for specific repositories
- **Environment Configuration**: Repository-specific PATH, environment variables

**Building Process**:
```python
from swebench import build_env_images
import docker

client = docker.from_env()
build_env_images(client, dataset, force_rebuild=False, max_workers=4)
```

**Dependency Installation Process**:
1. **Repository Cloning**: Clone repository at specific base commit
2. **Dependency Resolution**: Parse dependency files and install packages
3. **Development Setup**: Install testing and development dependencies
4. **Environment Verification**: Run basic import and setup tests

**Characteristics**:
- Built per repository and version combination
- Contains all dependencies but no instance-specific patches
- Cached and reused across multiple test instances

### Layer 3: Instance Images
**Purpose**: Apply specific patches and prepare for test execution

Instance images (`build_instance_images`) extend environment images with:
- **Patch Application**: Apply the specific code changes being tested
- **Test Configuration**: Set up test data, configuration files
- **Instance Metadata**: Information about the specific test case
- **Execution Scripts**: Pre-configured commands for running tests

**Building Process**:
```python
from swebench import build_instance_images
import docker

client = docker.from_env()
build_instance_images(dataset, client, force_rebuild=False, max_workers=4)
```

**Characteristics**:
- Built for each individual test instance
- Contains applied patches and test-specific setup
- Ephemeral - typically removed after evaluation

## Test Execution Flow

### 1. Image Preparation
```python
# Ensure all required images exist
build_base_images(client, dataset)
build_env_images(client, dataset, max_workers=4)
build_instance_images(dataset, client, max_workers=4)
```

### 2. Container Initialization
```bash
# Start evaluation container
docker run --rm \
  -v /tmp/swe-results:/results \
  -e TIMEOUT=1800 \
  -e INSTANCE_ID=astropy__astropy-11693 \
  swebench/instance:astropy-11693
```

### 3. Patch Application and Verification
Inside the container:
```bash
# Navigate to repository
cd /opt/swe-bench/repository

# Verify patch is applied
git status --porcelain

# Check that patch changes are present
git diff HEAD~1
```

### 4. Test Execution
```bash
# Run FAIL_TO_PASS tests (should pass after patch)
python -m pytest astropy/wcs/wcsapi/tests/test_fitswcs.py::test_non_convergence_warning -xvs
FAIL_TO_PASS_RESULT=$?

# Run PASS_TO_PASS tests (should continue passing)
python -m pytest astropy/wcs/wcsapi/tests/test_fitswcs.py::test_empty -xvs
PASS_TO_PASS_RESULT=$?
```

### 5. Result Collection
```bash
# Save test results
echo "FAIL_TO_PASS: $FAIL_TO_PASS_RESULT" > /results/test_results.txt
echo "PASS_TO_PASS: $PASS_TO_PASS_RESULT" >> /results/test_results.txt
```

## Integration Points with Validator

### 1. Data Point Loading
The validator integrates with Docker system by:
- Loading JSON data points from `data_points/` directory
- Extracting patch, test information, and repository metadata
- Converting to SWE-bench prediction format

### 2. Docker Image Management
```python
def ensure_docker_images(instance_data):
    """Ensure required Docker images are available."""
    import docker
    from swebench import build_base_images, build_env_images, build_instance_images
    
    client = docker.from_env()
    dataset = [instance_data]
    
    # Build images in order
    build_base_images(client, dataset)
    build_env_images(client, dataset, max_workers=1)
    build_instance_images(dataset, client, max_workers=1)
```

### 3. Evaluation Execution
```python
from swebench.harness.run_evaluation import main as run_evaluation

def validate_data_point(data_point_path):
    """Validate data point using SWE-bench evaluation harness."""
    # Load and convert data point
    instance = load_instance(data_point_path)
    prediction = convert_to_prediction(instance)
    
    # Create predictions file
    predictions_file = "temp_predictions.jsonl"
    with open(predictions_file, 'w') as f:
        json.dump(prediction, f)
        f.write('\n')
    
    # Run evaluation using Docker system
    results = run_evaluation(
        dataset_name="princeton-nlp/SWE-bench",
        split="test",
        instance_ids=[instance["instance_id"]],
        predictions_path=predictions_file,
        max_workers=1,
        run_id=f"validation_{instance['instance_id']}"
    )
    
    return analyze_results(results)
```

### 4. Result Interpretation
The validator interprets Docker execution results:
- **RESOLVED**: All FAIL_TO_PASS tests pass, all PASS_TO_PASS tests continue passing
- **UNRESOLVED**: Some tests fail or patch doesn't apply correctly
- **ERROR**: Docker or system-level errors during evaluation

## Concrete Execution Examples

### Example 1: Successful Validation (astropy__astropy-11693)

```python
# Data point with correct patch
instance = {
    "instance_id": "astropy__astropy-11693",
    "repo": "astropy/astropy",
    "base_commit": "3832210580d516365ddae1a62071001faf94d416",
    "patch": "diff --git a/astropy/wcs/wcsapi/fitswcs.py...",
    "FAIL_TO_PASS": ["astropy/wcs/wcsapi/tests/test_fitswcs.py::test_non_convergence_warning"],
    "PASS_TO_PASS": ["astropy/wcs/wcsapi/tests/test_fitswcs.py::test_empty", ...]
}

# Prediction format
prediction = {
    "instance_id": "astropy__astropy-11693",
    "model_patch": instance["patch"],
    "model_name_or_path": "gold"
}

# Expected result
{
    "instance_id": "astropy__astropy-11693",
    "resolved": True,
    "test_results": {
        "FAIL_TO_PASS": {"passed": 1, "failed": 0},
        "PASS_TO_PASS": {"passed": 27, "failed": 0}
    }
}
```

### Example 2: Failed Validation (astropy__astropy-11693-fail)

```python
# Data point with incorrect patch
instance = {
    "instance_id": "astropy__astropy-11693-fail",
    "patch": "diff --git a/astropy/wcs/wcsapi/fitswcs.py...\n+            raise e  # Still raises exception"
}

# Expected result
{
    "instance_id": "astropy__astropy-11693-fail",
    "resolved": False,
    "test_results": {
        "FAIL_TO_PASS": {"passed": 0, "failed": 1},
        "PASS_TO_PASS": {"passed": 27, "failed": 0}
    },
    "error": "FAIL_TO_PASS tests still failing after patch application"
}
```

## Resource Management

### Docker Resource Requirements
- **CPU**: Minimum 4 cores, recommended 8+ cores
- **Memory**: Minimum 8GB RAM, recommended 16GB+ RAM  
- **Storage**: 120GB+ free disk space for images and containers
- **Network**: Internet access for pulling base images

### Cleanup and Maintenance
```python
def cleanup_docker_resources():
    """Clean up Docker resources after evaluation."""
    import docker
    
    client = docker.from_env()
    
    # Remove stopped containers
    client.containers.prune()
    
    # Remove unused images
    client.images.prune(filters={"dangling": False})
    
    # Remove unused volumes
    client.volumes.prune()
```

## Performance Optimization

### Image Caching Strategy
- **Base Images**: Long-term caching (weeks/months)
- **Environment Images**: Medium-term caching (days/weeks)
- **Instance Images**: Short-term caching (hours/days)

### Parallel Processing
- Multiple instances can be evaluated simultaneously
- Resource-aware scheduling based on available CPU/memory
- Queue management for high-throughput scenarios

This Docker architecture ensures reliable, reproducible, and scalable evaluation of SWE-bench data points while maintaining the isolation and consistency required for accurate benchmarking.
