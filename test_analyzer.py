#!/usr/bin/env python3
"""
Unit tests for Adobe Hackathon Round 1A PDF Analyzer
"""

import pytest
import sys
from pathlib import Path
import tempfile
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from pdf_analyzer import PDFAnalyzer
from utils import load_config, validate_json_output

class TestPDFAnalyzer:
    """Test cases for PDF analyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance with test config"""
        config = {
            'min_font_size_threshold': 10,
            'font_size_variance_threshold': 2.0,
            'position_threshold': 0.7,
            'max_heading_length': 200,
            'min_heading_length': 3
        }
        return PDFAnalyzer(config)
    
    def test_heading_level_determination(self, analyzer):
        """Test heading level classification logic"""
        
        # Test pattern-based classification
        element1 = {'text': '1. Introduction', 'font_size': 14}
        assert analyzer._determine_heading_level(element1, 12) == "H1"
        
        element2 = {'text': '1.1 Subsection', 'font_size': 13}
        assert analyzer._determine_heading_level(element2, 12) == "H2"
        
        element3 = {'text': '1.1.1 Sub-subsection', 'font_size': 12}
        assert analyzer._determine_heading_level(element3, 12) == "H3"
    
    def test_heading_candidate_detection(self, analyzer):
        """Test heading candidate identification"""
        
        # Test large font element
        element1 = {
            'text': 'Chapter 1: Introduction',
            'font_size': 18,
            'flags': 16,  # Bold flag
            'bbox': [0, 100, 200, 120]
        }
        assert analyzer._is_heading_candidate(element1, 12, 2) == True
        
        # Test regular text element  
        element2 = {
            'text': 'This is regular paragraph text.',
            'font_size': 11,
            'flags': 0,
            'bbox': [0, 200, 400, 220]
        }
        assert analyzer._is_heading_candidate(element2, 12, 2) == False
    
    def test_heading_cleaning(self, analyzer):
        """Test heading deduplication and cleaning"""
        
        headings = [
            {'level': 'H1', 'text': 'Introduction', 'page': 1},
            {'level': 'H1', 'text': 'Introduction', 'page': 1},  # Duplicate
            {'level': 'H2', 'text': 'Overview   ', 'page': 2},  # Extra spaces
            {'level': 'H3', 'text': 'AA', 'page': 3},  # Too short
        ]
        
        cleaned = analyzer._clean_headings(headings)
        
        assert len(cleaned) == 2  # Duplicate and short heading removed
        assert cleaned[0]['text'] == 'Introduction'
        assert cleaned[1]['text'] == 'Overview'  # Spaces cleaned

class TestUtils:
    """Test utility functions"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        
        # Test default config when file doesn't exist
        config = load_config(Path("nonexistent.yaml"))
        assert 'min_font_size_threshold' in config
        assert config['min_font_size_threshold'] == 10
    
    def test_json_validation(self):
        """Test output JSON validation"""
        
        # Valid JSON structure
        valid_result = {
            "title": "Test Document",
            "outline": [
                {"level": "H1", "text": "Introduction", "page": 1},
                {"level": "H2", "text": "Overview", "page": 2}
            ]
        }
        assert validate_json_output(valid_result) == True
        
        # Invalid JSON structure
        invalid_result = {
            "title": "Test Document",
            "outline": [
                {"level": "H4", "text": "Invalid Level", "page": 1}  # H4 not allowed
            ]
        }
        assert validate_json_output(invalid_result) == False

class TestIntegration:
    """Integration test cases"""
    
    def test_json_output_format(self):
        """Test that output matches required JSON format"""
        
        # Mock result structure
        result = {
            "title": "Understanding AI",
            "outline": [
                {"level": "H1", "text": "Introduction", "page": 1},
                {"level": "H2", "text": "What is AI?", "page": 2},
                {"level": "H3", "text": "History of AI", "page": 3}
            ]
        }
        
        # Validate structure
        assert "title" in result
        assert "outline" in result
        assert isinstance(result["outline"], list)
        
        # Validate heading structure
        for heading in result["outline"]:
            assert "level" in heading
            assert "text" in heading  
            assert "page" in heading
            assert heading["level"] in ["H1", "H2", "H3"]
            assert isinstance(heading["page"], int)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])