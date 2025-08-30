# SWE-bench Data Point Validator

A validation system for SWE-bench data points that uses the official evaluation harness to ensure patches correctly fix the specified issues.

## Features

- **Real SWE-bench Integration**: Uses `swebench.harness.run_evaluation` for validation
- **GitHub Actions**: Automatically validates changed data points in pull requests  
- **CLI Interface**: Command-line tools for manual validation
- **Docker Support**: Leverages SWE-bench's Docker-based evaluation system
- **Detailed Error Messages**: Clear, actionable error reporting

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd swe_bench_

# Install dependencies using UV
uv sync --all-extras
```

### Basic Usage

```bash
# Validate a single data point
uv run swe-bench-validator validate-file data_points/astropy__astropy-11693.json

# Validate all data points in directory
uv run swe-bench-validator validate-directory data_points/

# Show help
uv run swe-bench-validator --help
```

## How It Works

1. **Load Data Point**: Parse JSON file and validate required fields
2. **Convert Format**: Transform to SWE-bench prediction format using golden patch
3. **Run Evaluation**: Execute `swebench.harness.run_evaluation` with Docker containers
4. **Check Results**: Verify that:
   - Patch applies successfully
   - All `FAIL_TO_PASS` tests pass after applying patch
   - All `PASS_TO_PASS` tests continue to pass
5. **Report Results**: Generate detailed validation report

## GitHub Actions Integration

The workflow automatically:

1. **Detects Changes**: Identifies modified `data_points/**/*.json` files
2. **Runs Validation**: Validates only changed files for performance
3. **Reports Status**: Sets green/red status checks on PRs
4. **Comments Results**: Posts detailed validation results as PR comments
5. **Uploads Artifacts**: Saves validation reports for later analysis

### Example PR Comment

```
🧪 SWE-bench Data Point Validation Results

📊 Summary
- Total files validated: 2
- Passed: 1 ✅  
- Failed: 1 ❌
- Success rate: 50%

📋 Detailed Results
✅ data_points/astropy__astropy-11693.json: PASSED
❌ data_points/astropy__astropy-11693-fail.json: FAILED
  - Error: Instance ID not found in SWE-bench dataset
```

## Examples

### Valid Data Point
`data_points/astropy__astropy-11693.json` contains a correct patch that:
- Handles `NoConvergence` exceptions properly
- Issues warnings instead of raising errors
- Makes `FAIL_TO_PASS` tests pass
- Keeps `PASS_TO_PASS` tests passing

### Invalid Data Point  
`data_points/astropy__astropy-11693-fail.json` contains issues that cause validation to fail:
- Uses non-existent `instance_id` not in SWE-bench dataset
- Would fail SWE-bench evaluation if `instance_id` existed

## Requirements

- **Python 3.10+** with UV package manager
- **Docker** (for SWE-bench evaluation)
- **120GB+ free disk space** (for Docker images)
- **16GB+ RAM** (recommended for evaluation)
- **SWE-bench library** (≥4.0.4)

## Adding New Data Points

To add new SWE-bench data points to the repository:

### 1. Create Data Point File
```bash
# Download from SWE-bench using the downloader
scripts/download_swe_bench.sh --instance_id "django__django-12345"

# Or manually create JSON file with required fields:
{
  "instance_id": "repo__repo-issue",
  "repo": "owner/repository", 
  "base_commit": "commit_hash",
  "patch": "diff --git a/...",
  "FAIL_TO_PASS": "[\"test_that_should_pass\"]",
  "PASS_TO_PASS": "[\"test1\", \"test2\", ...]"
}
```

### 2. Validate Before Committing
```bash
# Test your data point locally
uv run swe-bench-validator validate-file data_points/your-new-file.json

# Ensure it passes validation
echo $?  # Should be 0 for success
```

### 3. Create Pull Request
- Add your file to `data_points/` directory
- Create PR - GitHub Actions will automatically validate
- Fix any validation failures before merging
- Green ✅ status check means validation passed

### 4. Validation Process
When you create a PR:
1. GitHub Actions detects changed files in `data_points/`
2. Runs SWE-bench evaluation harness on changed files
3. Posts validation results as PR comment
4. Sets status check (green ✅ or red ❌)

## Project Structure

```
swe_bench_/
├── data_points/                    # SWE-bench data points
├── swe_bench_validator/           # Core validation engine
│   ├── validator.py               # Main validation logic
│   ├── cli.py                     # Command-line interface  
│   ├── config.py                  # Configuration settings
│   └── utils.py                   # Utility functions
├── .github/workflows/             # GitHub Actions
├── scripts/                       # Helper scripts
├── swe-bench-docker-architecture.md  # Docker documentation
└── pyproject.toml                 # Project configuration
```

## Contributing

1. Fork the repository
2. Add new data points to `data_points/` directory
3. Ensure data points follow the required JSON format
4. Test locally with `uv run swe-bench-validator validate-file your-file.json`
5. Create pull request
6. GitHub Actions will automatically validate changes
7. Fix any validation failures before merging

## License

This project is part of the SWE-bench ecosystem and follows the same licensing terms.