# Detailed Implementation Plan for SWE-bench Data Point Validator

## Task Overview

Need to create a validation system for SWE-bench data points that will verify the correctness of patches using the official SWE-bench evaluation harness. The system must integrate with GitHub Actions for automatic validation when changes occur in the `data_points/` folder.

## Stage 1: SWE-bench Docker Architecture Documentation

### 1.1 Docker Architecture Research
- [x] Study official SWE-bench Docker documentation
- [x] Analyze 3-layer Docker image system:
  - Base images (base images with system dependencies)
  - Environment images (images with project dependencies)  
  - Instance images (images for specific test cases)
- [x] Understand image building process and dependency installation

### 1.2 Documentation Creation
- [x] Create `swe-bench-docker-architecture.md` file
- [x] Describe Docker system architecture
- [x] Document test execution process
- [x] Add concrete execution examples
- [x] Describe integration points with validator

**Deliverable**: `swe-bench-docker-architecture.md` (100-300 lines)

## Stage 2: SWE-bench Validator Implementation

### 2.1 Validator Architecture
- [x] Create `swe_bench_validator/` module
- [x] Module structure:
  - `__init__.py` - public API
  - `validator.py` - main validation logic
  - `cli.py` - command line interface
  - `utils.py` - utility functions
  - `config.py` - validation configuration

### 2.2 Core Functionality
- [x] **Data points loading**: Reading JSON files from `data_points/` folder
- [x] **Prediction format conversion**: Converting to SWE-bench predictions format
- [x] **Evaluation harness execution**: Using `swebench.harness.run_evaluation`
- [x] **Results validation**: Checking that `FAIL_TO_PASS` and `PASS_TO_PASS` tests pass

### 2.3 Error Handling and Timeouts
- [x] **Structural errors**: Invalid JSON, missing fields
- [x] **Execution errors**: Docker errors, test failures
- [x] **Timeouts**: Configurable timeouts for different data point types
- [x] **Detailed error messages**: Clear and actionable messages

### 2.4 CLI Interface
- [x] Command for validating specific file
- [x] Command for validating entire folder
- [x] Command for validating only changed files
- [x] Options for configuring timeouts and detail level

**Deliverable**: Working Python validator with CLI interface

## Stage 3: GitHub Action Workflow

### 3.1 Workflow File Creation
- [x] Create `.github/workflows/validate-datapoints.yml`
- [x] Configure triggers:
  - Push to `data_points/**`
  - Pull requests affecting `data_points/**`

### 3.2 Performance Optimization
- [x] **Change detection**: Identifying only changed/new files
- [x] **Parallel validation**: If possible, validate files in parallel
- [x] **Caching**: Caching Docker images and dependencies

### 3.3 Reporting and Status
- [x] **Status checks**: Green/red status for PR
- [x] **Detailed logs**: Comprehensive error information
- [x] **PR comments**: Automatic comments with results

**Deliverable**: `.github/workflows/validate-datapoints.yml`

## Stage 4: Project Integration

### 4.1 Project Configuration Updates
- [x] Add validator dependencies to `pyproject.toml`
- [x] Update package structure in `setuptools.packages.find`
- [x] Add dev dependencies for testing

### 4.2 User Documentation
- [x] Update `README.md` with usage instructions
- [x] Add validator usage examples
- [x] Document process for adding new data points

**Deliverable**: Updated project configuration and documentation

## Stage 5: Testing and Demonstration

### 5.1 Local Testing
- [x] Test validator on existing data points
- [x] Ensure valid point (`astropy__astropy-11693.json`) passes validation
- [x] Ensure invalid point (`astropy__astropy-11693-fail.json`) fails validation

### 5.2 Public Repository Creation
- [x] Create new public repository with implementation
- [x] Transfer all code and configuration
- [x] Set up GitHub Actions in new repository

### 5.3 Test Pull Requests Creation
- [x] **PR #1 (valid)**: 
  - Add valid data point
  - Show green status checks
  - Demonstrate successful validation
- [x] **PR #2 (invalid)**:
  - Add invalid data point  
  - Show red status checks
  - Demonstrate clear error messages

**Deliverable**: Public repository with two demonstration PRs

## Technical Requirements

### Languages and Tools
- **Python 3.10+** with UV package manager
- **SWE-bench library** for evaluation harness
- **Docker** for test execution
- **GitHub Actions** for CI/CD

### Dependencies
- `swebench>=4.0.4` - official SWE-bench library
- `click` - for CLI interface
- `rich` - for beautiful output
- `pytest` - for testing (dev dependency)

### Performance and Reliability
- **Timeouts**: Configurable timeouts to prevent hanging
- **Error Handling**: Graceful handling of Docker errors and test failures
- **Optimization**: Validation of only changed files in CI/CD

## Success Criteria

1. **Documentation**: Complete and clear Docker architecture documentation
2. **Functionality**: Validator correctly identifies valid and invalid data points
3. **Integration**: GitHub Action works automatically on changes
4. **Demonstration**: Two PRs show system working in real conditions
5. **Code Quality**: Clean, well-structured and documented code

## Time Estimates

- **Stage 1** (Documentation): 1.5 hours
- **Stage 2** (Validator): 2.5 hours  
- **Stage 3** (GitHub Action): 1 hour
- **Stage 4** (Integration): 0.5 hours
- **Stage 5** (Testing): 1 hour

**Total time**: ~6 hours (matches assignment estimate)

## Execution Order

1. Start with Docker architecture documentation for system understanding
2. Implement core validator with CLI interface
3. Create and test GitHub Action locally
4. Integrate all components and update documentation
5. Create public repository and demonstration PRs

This plan ensures a systematic approach to solving the task with clear deliverables and success criteria at each stage.
