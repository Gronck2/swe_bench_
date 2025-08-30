# SWE-bench Data Point Validator - Usage Guide

## Overview

This guide provides comprehensive instructions for using the SWE-bench Data Point Validator to ensure the quality and correctness of SWE-bench data points.

## Installation and Setup

### Prerequisites
- **Python 3.10+**
- **Docker** (for SWE-bench evaluation)
- **UV package manager**
- **120GB+ free disk space**
- **16GB+ RAM** (recommended)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd swe_bench_

# Install dependencies
uv sync --all-extras

# Verify installation
uv run swe-bench-validator --help
```

## Command Line Usage

### Basic Commands

#### Validate Single File
```bash
# Basic validation
uv run swe-bench-validator validate-file data_points/astropy__astropy-11693.json

# With custom timeout (in seconds)
uv run swe-bench-validator validate-file data_points/example.json --timeout 3600

# With verbose logging
uv run swe-bench-validator --verbose validate-file data_points/example.json
```

#### Validate Directory
```bash
# Validate all JSON files in directory
uv run swe-bench-validator validate-directory data_points/

# With custom pattern
uv run swe-bench-validator validate-directory data_points/ --pattern "astropy*.json"

# With custom timeout
uv run swe-bench-validator validate-directory data_points/ --timeout 2400
```

## Data Point Format

SWE-bench data points must include these required fields:

```json
{
  "instance_id": "astropy__astropy-11693",
  "repo": "astropy/astropy",
  "base_commit": "3832210580d516365ddae1a62071001faf94d416",
  "patch": "diff --git a/astropy/wcs/wcsapi/fitswcs.py...",
  "FAIL_TO_PASS": "[\"astropy/wcs/wcsapi/tests/test_fitswcs.py::test_non_convergence_warning\"]",
  "PASS_TO_PASS": "[\"astropy/wcs/wcsapi/tests/test_fitswcs.py::test_empty\", ...]"
}
```

### Field Descriptions

- **instance_id**: Must exist in official SWE-bench dataset
- **repo**: GitHub repository (owner/name format)
- **base_commit**: Git commit hash before the fix
- **patch**: Git diff patch that fixes the issue
- **FAIL_TO_PASS**: Tests that should pass after applying patch
- **PASS_TO_PASS**: Tests that should continue passing

## Validation Process

### What the Validator Does

1. **Load Data Point**: Parse JSON and validate structure
2. **Convert Format**: Transform to SWE-bench prediction format
3. **Run Evaluation**: Execute real SWE-bench evaluation harness
4. **Docker Execution**: 
   - Build Docker images with repository environment
   - Apply patch to codebase
   - Run FAIL_TO_PASS and PASS_TO_PASS tests
   - Collect results
5. **Report Results**: Determine if patch successfully resolves issue

### Success Criteria

A data point passes validation when:
- ✅ Patch applies successfully to repository
- ✅ All FAIL_TO_PASS tests pass after patch application  
- ✅ All PASS_TO_PASS tests continue to pass
- ✅ No Docker or system errors occur

### Failure Scenarios

A data point fails validation when:
- ❌ Instance ID not found in SWE-bench dataset
- ❌ Missing required JSON fields
- ❌ Patch fails to apply to repository
- ❌ FAIL_TO_PASS tests still fail after patch
- ❌ PASS_TO_PASS tests now fail due to patch
- ❌ Docker or system errors during evaluation

## GitHub Actions Integration

### Automatic Validation

When you create a pull request that modifies files in `data_points/`:

1. **Detection**: GitHub Actions detects changed JSON files
2. **Validation**: Runs SWE-bench evaluation on changed files only
3. **Status Check**: Sets green ✅ or red ❌ status on PR
4. **PR Comment**: Posts detailed validation results
5. **Artifacts**: Uploads validation logs and reports

### Example Workflow

```yaml
# Triggered automatically on PR
name: Validate SWE-bench Data Points
on:
  pull_request:
    paths: ['data_points/**']

# Validates only changed files
# Posts results as PR comment
# Sets status check for merge protection
```

## Troubleshooting

### Common Issues

#### 1. Instance ID Not Found
```
Error: Instance ID 'custom__custom-123' not found in SWE-bench dataset
```
**Solution**: Use an existing instance_id from the official SWE-bench dataset.

#### 2. Missing Required Fields
```
Error: Missing required fields: ['patch']
```
**Solution**: Ensure your JSON includes all required fields.

#### 3. Docker Issues
```
Error: Docker not running or not accessible
```
**Solution**: Start Docker and ensure it's accessible to your user.

#### 4. Timeout Errors
```
Error: SWE-bench evaluation timed out after 1800s
```
**Solution**: Increase timeout with `--timeout 3600` option.

#### 5. Resource Issues
```
Error: Insufficient system resources
```
**Solution**: Ensure you have 120GB+ disk space and 16GB+ RAM available.

### Debug Mode

Enable verbose logging for debugging:
```bash
uv run swe-bench-validator --verbose --log-file debug.log validate-file data_points/example.json
```

## Performance Considerations

### Execution Time
- **Single validation**: 3-15 minutes per data point
- **Depends on**: Repository size, test complexity, system resources
- **Docker overhead**: Image building and container startup

### Resource Usage
- **Disk**: ~5-10GB per repository for Docker images
- **Memory**: 2-4GB per validation process
- **CPU**: Multi-core recommended for parallel operations

### Optimization Tips
- Use `validate-directory` for batch processing
- Ensure Docker has sufficient resources allocated
- Consider running validations during off-peak hours
- Use SSD storage for better Docker performance

## Examples

### Successful Validation
```bash
$ uv run swe-bench-validator validate-file data_points/astropy__astropy-11693.json

Validating data point: data_points/astropy__astropy-11693.json
Using SWE-bench evaluation harness...
[Docker images building...]
[Tests running...]
✅ PASSED: astropy__astropy-11693
```

### Failed Validation
```bash
$ uv run swe-bench-validator validate-file data_points/invalid-example.json

Validating data point: data_points/invalid-example.json
Using SWE-bench evaluation harness...
❌ FAILED: invalid-example
   Error: Instance ID 'invalid-example' not found in SWE-bench dataset.
   
   This error occurs when:
     • The instance_id doesn't exist in the official SWE-bench dataset
     • There's a typo in the instance_id field
   
   Solution:
     • Use an existing instance_id from SWE-bench dataset
     • Check the instance_id spelling and format
```

## Integration with Development Workflow

### Pre-commit Hook
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
uv run swe-bench-validator validate-directory data_points/
```

### CI/CD Pipeline
```yaml
- name: Validate SWE-bench data points
  run: uv run swe-bench-validator validate-directory data_points/
```

### Development Testing
```bash
# Quick validation during development
uv run swe-bench-validator validate-file data_points/new-datapoint.json

# Batch validation before commit
uv run swe-bench-validator validate-directory data_points/
```
