#!/bin/bash

# Test script to simulate GitHub Actions workflow logic locally
# This helps verify the workflow will work correctly

set -e

echo "🧪 Testing GitHub Actions Workflow Logic"
echo "========================================"

# Change to project root
cd "$(dirname "$0")/.."

echo ""
echo "📋 1. Testing changed files detection"
echo "------------------------------------"

# Simulate git diff for changed files
CHANGED_FILES=$(git status --porcelain data_points/ | grep -E '\.(json)$' | awk '{print $2}' || echo "")

if [[ -n "$CHANGED_FILES" ]]; then
    echo "Found changed files:"
    for file in $CHANGED_FILES; do
        echo "  📄 $file"
    done
    FILE_COUNT=$(echo $CHANGED_FILES | wc -w)
else
    echo "  ℹ️ No changed data point files found"
    FILE_COUNT=0
fi

echo "File count: $FILE_COUNT"

echo ""
echo "📋 2. Testing validation logic"
echo "-----------------------------"

if [[ $FILE_COUNT -gt 0 ]]; then
    echo "🧪 Validating $FILE_COUNT changed data point files"
    
    # Create results directory
    mkdir -p validation_results
    
    # Initialize counters
    TOTAL=0
    PASSED=0
    FAILED=0
    
    # Validate each file
    for file in $CHANGED_FILES; do
        echo ""
        echo "📋 Validating: $file"
        TOTAL=$((TOTAL + 1))
        
        # Create individual result file name
        RESULT_FILE="validation_results/$(basename "$file" .json)_result.json"
        
        # Run validation and capture output
        if uv run swe-bench-validator validate-file "$file" 2>&1 | tee "validation_results/$(basename "$file" .json)_output.log"; then
            echo "✅ PASSED: $file"
            PASSED=$((PASSED + 1))
            echo '{"status": "PASSED", "file": "'$file'", "error": null}' > "$RESULT_FILE"
        else
            echo "❌ FAILED: $file"
            FAILED=$((FAILED + 1))
            # Extract error message from output
            ERROR_MSG=$(tail -10 "validation_results/$(basename "$file" .json)_output.log" | grep "Error:" | head -1 || echo "Validation failed")
            echo '{"status": "FAILED", "file": "'$file'", "error": "'"$ERROR_MSG"'"}' > "$RESULT_FILE"
        fi
    done
    
    echo ""
    echo "📊 Summary:"
    echo "   Total: $TOTAL"
    echo "   Passed: $PASSED"
    echo "   Failed: $FAILED"
    echo "   Success Rate: $(( PASSED * 100 / TOTAL ))%"
    
    # Create summary report (like in GitHub Actions)
    echo "## 🧪 SWE-bench Data Point Validation Results" > validation_summary.md
    echo "" >> validation_summary.md
    echo "### 📊 Summary" >> validation_summary.md
    echo "- **Total files validated:** $TOTAL" >> validation_summary.md
    echo "- **Passed:** $PASSED ✅" >> validation_summary.md
    echo "- **Failed:** $FAILED ❌" >> validation_summary.md
    echo "- **Success rate:** $(( PASSED * 100 / TOTAL ))%" >> validation_summary.md
    echo "" >> validation_summary.md
    
    # Add detailed results
    echo "### 📋 Detailed Results" >> validation_summary.md
    echo "" >> validation_summary.md
    
    for file in $CHANGED_FILES; do
        RESULT_FILE="validation_results/$(basename "$file" .json)_result.json"
        if [[ -f "$RESULT_FILE" ]]; then
            STATUS=$(python3 -c "import json; data=json.load(open('$RESULT_FILE')); print(data['status'])")
            if [[ "$STATUS" == "PASSED" ]]; then
                echo "✅ **$file**: PASSED" >> validation_summary.md
            else
                echo "❌ **$file**: FAILED" >> validation_summary.md
                ERROR=$(python3 -c "import json; data=json.load(open('$RESULT_FILE')); print(data.get('error', 'Unknown error'))")
                echo "   - Error: $ERROR" >> validation_summary.md
            fi
        else
            echo "❓ **$file**: No result available" >> validation_summary.md
        fi
    done
    
    echo ""
    echo "📄 Generated validation_summary.md:"
    cat validation_summary.md
    
    # Exit with error if any validation failed (like in GitHub Actions)
    if [[ $FAILED -gt 0 ]]; then
        echo ""
        echo "❌ Workflow would FAIL (exit code 1) due to validation failures"
        exit 1
    else
        echo ""
        echo "✅ Workflow would SUCCEED (exit code 0)"
    fi
else
    echo "ℹ️ No changed files to validate - workflow would skip validation step"
fi

echo ""
echo "🎉 GitHub Actions workflow logic test completed!"
echo "=============================================="
