#!/usr/bin/env python3
"""
Extract and format error message from validation result JSON.
"""
import json
import sys

def extract_error(result_file):
    """Extract error message with simple, readable formatting."""
    try:
        with open(result_file) as f:
            data = json.load(f)
            error = data.get('error', 'Unknown error')
            
            if not error or not error.strip():
                return 'Validation failed - check logs for details'
            
            error = error.strip()
            
            # Create simple, readable error messages
            if 'not found in SWE-bench dataset' in error:
                return 'Instance ID not found in SWE-bench dataset'
            
            elif 'Missing required fields' in error:
                # Extract which fields are missing
                if "['patch']" in error:
                    return 'Missing required field: patch'
                elif 'Missing required fields:' in error:
                    import re
                    match = re.search(r"Missing required fields: (\[.*?\])", error)
                    if match:
                        fields = match.group(1)
                        return f'Missing required fields: {fields}'
                return 'Missing required fields'
            
            elif 'Patch did not resolve the issue' in error:
                return 'Patch did not resolve the issue (tests still failing)'
            
            elif 'timeout' in error.lower():
                return 'Validation timed out'
            
            elif 'docker' in error.lower():
                return 'Docker execution error'
            
            else:
                # Fallback: use first sentence or line
                first_line = error.split('\n')[0]
                if '. ' in first_line:
                    first_sentence = first_line.split('. ')[0] + '.'
                    return first_sentence if len(first_sentence) <= 100 else first_line[:80] + '...'
                else:
                    return first_line[:80] + ('...' if len(first_line) > 80 else '')
                
    except Exception as e:
        return f'Error reading result file'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: extract_error.py <result_file>')
        sys.exit(1)
    
    print(extract_error(sys.argv[1]))
