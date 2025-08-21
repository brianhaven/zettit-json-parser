#!/usr/bin/env python3
"""
Temporary script to collapse multi-line JSON objects to single lines
Input: deathstar.markets_raw.json (multi-line formatted)
Output: deathstar.markets_raw_collapsed.json (single-line formatted)
"""

import json
import re

def collapse_json_file(input_file, output_file):
    """Collapse multi-line JSON objects to single lines"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove the outer array brackets and split by object boundaries
    # First, remove leading/trailing whitespace and array brackets
    content = content.strip()
    if content.startswith('['):
        content = content[1:]
    if content.endswith(']'):
        content = content[:-1]
    
    # Split into individual JSON objects by finding },\n{ patterns
    objects = []
    current_obj = ""
    brace_count = 0
    in_string = False
    escape_next = False
    
    for char in content:
        if escape_next:
            current_obj += char
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            current_obj += char
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                
        current_obj += char
        
        # When we complete an object (brace_count == 0 and we have content)
        if brace_count == 0 and current_obj.strip() and not in_string:
            # Clean up the object string
            obj_str = current_obj.strip().rstrip(',').strip()
            if obj_str:
                try:
                    # Parse and re-serialize to ensure valid JSON and collapse to single line
                    obj = json.loads(obj_str)
                    objects.append(json.dumps(obj, separators=(',', ':')))
                except json.JSONDecodeError:
                    # Skip invalid JSON objects
                    pass
            current_obj = ""
    
    # Handle the last object if any
    if current_obj.strip():
        obj_str = current_obj.strip().rstrip(',').strip()
        if obj_str:
            try:
                obj = json.loads(obj_str)
                objects.append(json.dumps(obj, separators=(',', ':')))
            except json.JSONDecodeError:
                pass
    
    # Write collapsed objects to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, obj in enumerate(objects):
            f.write(obj)
            if i < len(objects) - 1:  # Add comma except for last item
                f.write(',')
            f.write('\n')
    
    print(f"Processed {len(objects)} JSON objects")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

if __name__ == "__main__":
    input_file = "/home/ec2-user/zettit/services/json-parser/resources/deathstar.markets_raw.json"
    output_file = "/home/ec2-user/zettit/services/json-parser/resources/deathstar.markets_raw_collapsed.json"
    
    collapse_json_file(input_file, output_file)