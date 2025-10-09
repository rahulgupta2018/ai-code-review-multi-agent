"""
Sample Python module for code analysis testing.
This module contains various code quality issues for demonstration.
"""

import os
import sys
import json
import time
import requests
from typing import List, Dict, Optional, Any


class DataProcessor:
    """A class that processes various types of data with some quality issues."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.data = []
        self.processed_data = {}
        self.errors = []
        
    def load_config(self):
        """Load configuration file"""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        else:
            return {"default": True, "timeout": 30, "retries": 3}
    
    def process_data(self, input_data):
        """Process input data with various transformations"""
        # This function has high complexity and multiple issues
        results = []
        
        for item in input_data:
            if isinstance(item, dict):
                if 'id' in item and 'value' in item:
                    if item['value'] is not None:
                        if isinstance(item['value'], (int, float)):
                            if item['value'] > 0:
                                processed_item = {
                                    'id': item['id'],
                                    'processed_value': item['value'] * 2,
                                    'timestamp': time.time(),
                                    'status': 'processed'
                                }
                                results.append(processed_item)
                            else:
                                self.errors.append(f"Invalid value for item {item['id']}: {item['value']}")
                        else:
                            try:
                                numeric_value = float(item['value'])
                                if numeric_value > 0:
                                    processed_item = {
                                        'id': item['id'],
                                        'processed_value': numeric_value * 2,
                                        'timestamp': time.time(),
                                        'status': 'converted_and_processed'
                                    }
                                    results.append(processed_item)
                                else:
                                    self.errors.append(f"Invalid converted value for item {item['id']}: {numeric_value}")
                            except ValueError:
                                self.errors.append(f"Cannot convert value for item {item['id']}: {item['value']}")
                    else:
                        self.errors.append(f"Null value for item {item['id']}")
                else:
                    self.errors.append(f"Missing required fields in item: {item}")
            else:
                self.errors.append(f"Invalid item type: {type(item)}")
        
        return results
    
    def fetch_external_data(self, url: str, retries: int = 3):
        """Fetch data from external API with retry logic"""
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                else:
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise Exception(f"Failed to fetch data after {retries} attempts. Status: {response.status_code}")
            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception(f"Network error after {retries} attempts: {e}")
    
    def validate_data(self, data):
        # Function without docstring and with duplicated validation logic
        valid_items = []
        
        for item in data:
            if isinstance(item, dict):
                if 'id' in item and 'value' in item:
                    if item['value'] is not None:
                        if isinstance(item['value'], (int, float)):
                            if item['value'] > 0:
                                valid_items.append(item)
        
        return valid_items
    
    def another_validation_method(self, data):
        # Duplicate validation logic - code duplication issue
        validated = []
        
        for item in data:
            if isinstance(item, dict):
                if 'id' in item and 'value' in item:
                    if item['value'] is not None:
                        if isinstance(item['value'], (int, float)):
                            if item['value'] > 0:
                                validated.append(item)
        
        return validated
    
    def save_results(self, results, output_path):
        """Save processing results to file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            print(f"Error saving results: {e}")
            raise


def utility_function_with_long_line_that_exceeds_reasonable_character_limits_and_should_be_broken_down_for_better_readability(param1, param2, param3, param4, param5):
    """This function has an unnecessarily long name and line that should be refactored."""
    return param1 + param2 + param3 + param4 + param5


# Global variable that should be avoided
GLOBAL_COUNTER = 0

def increment_global_counter():
    global GLOBAL_COUNTER
    GLOBAL_COUNTER += 1
    return GLOBAL_COUNTER


# Function with too many parameters
def complex_calculation(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p):
    """Function with too many parameters - should use a config object instead."""
    return (a + b + c + d) * (e + f + g + h) / (i + j + k + l) - (m + n + o + p)


if __name__ == "__main__":
    processor = DataProcessor("config.json")
    
    sample_data = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": -5},
        {"id": 4, "value": "30"},
        {"id": 5, "value": None},
    ]
    
    results = processor.process_data(sample_data)
    print(f"Processed {len(results)} items")
    print(f"Errors: {len(processor.errors)}")