#!/usr/bin/env python3
"""
Utility functions for Adobe Hackathon Round 1A
"""

import yaml
import logging
import sys
from pathlib import Path
from typing import Dict, Any

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party library log levels
    logging.getLogger('fitz').setLevel(logging.WARNING)

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        else:
            # Default configuration
            return {
                'min_font_size_threshold': 10,
                'font_size_variance_threshold': 2.0,
                'position_threshold': 0.7,
                'max_heading_length': 200,
                'min_heading_length': 3
            }
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading config: {e}")
        # Return default config
        return {
            'min_font_size_threshold': 10,
            'font_size_variance_threshold': 2.0,
            'position_threshold': 0.7,
            'max_heading_length': 200,
            'min_heading_length': 3
        }

def validate_json_output(result: Dict) -> bool:
    """Validate output JSON structure matches requirements"""
    
    required_keys = ['title', 'outline']
    
    # Check top-level structure
    for key in required_keys:
        if key not in result:
            return False
    
    # Validate title
    if not isinstance(result['title'], str):
        return False
    
    # Validate outline structure
    if not isinstance(result['outline'], list):
        return False
    
    for heading in result['outline']:
        if not isinstance(heading, dict):
            return False
        
        required_heading_keys = ['level', 'text', 'page']
        for key in required_heading_keys:
            if key not in heading:
                return False
        
        # Validate heading level format
        if heading['level'] not in ['H1', 'H2', 'H3']:
            return False
        
        # Validate page number
        if not isinstance(heading['page'], int) or heading['page'] < 1:
            return False
    
    return True