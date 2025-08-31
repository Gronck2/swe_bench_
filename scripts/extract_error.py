#!/usr/bin/env python3
"""
Extract and format error message from validation result JSON.
"""
import json
import sys

def extract_error(result_file):
    """Extract error message with smart truncation."""
    try:
        with open(result_file) as f:
            data = json.load(f)
            error = data.get('error', 'Unknown error')
            
            if not error or not error.strip():
                return 'Validation failed - check logs for details'
            
            error = error.strip()
            
            # Cut at logical breakpoints for better readability
            breakpoints = [
                'Solution:',           # Cut before solution section
                'Technical details:',  # Cut before technical details  
                'Original error:',     # Cut before original error
            ]
            
            for bp in breakpoints:
                if bp in error:
                    result = error.split(bp)[0].strip()
                    return result
            
            # Special handling for "This error occurs when:" - include explanation
            if 'This error occurs when:' in error:
                parts = error.split('This error occurs when:')
                main_error = parts[0].strip()
                explanation = parts[1].split('Solution:')[0].strip()
                return f"{main_error} This error occurs when: {explanation}"
            
            # No breakpoint found, use first line only
            first_line = error.split('\n')[0]
            if len(first_line) <= 120:
                return first_line
            else:
                return first_line[:120] + '...'
                
    except Exception as e:
        return f'Error reading result file: {e}'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: extract_error.py <result_file>')
        sys.exit(1)
    
    print(extract_error(sys.argv[1]))
