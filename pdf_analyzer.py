#!/usr/bin/env python3
"""
PDF Document Structure Analyzer

This module implements intelligent PDF heading detection using multi-modal analysis:
- Font size analysis
- Font weight detection  
- Positioning heuristics
- Text pattern recognition
"""

import fitz  # PyMuPDF
import json
import re
import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path
import statistics

class PDFAnalyzer:
    """Advanced PDF document structure analyzer"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Heading detection thresholds
        self.min_font_size_threshold = config.get('min_font_size_threshold', 10)
        self.font_size_variance_threshold = config.get('font_size_variance_threshold', 2.0)
        self.position_threshold = config.get('position_threshold', 0.7)
        
        # Heading patterns
        self.heading_patterns = [
            r'^\d+\.\s+',           # 1. Introduction
            r'^\d+\.\d+\s+',       # 1.1 Subsection  
            r'^\d+\.\d+\.\d+\s+', # 1.1.1 Sub-subsection
            r'^[IVX]+\.\s+',        # I. Roman numerals
            r'^[A-Z]\.\s+',         # A. Letter sections
            r'^Chapter\s+\d+',      # Chapter 1
            r'^Section\s+\d+',      # Section 1
        ]
        
    def extract_structure(self, pdf_path: Path) -> Dict:
        """Extract document structure from PDF"""
        self.logger.info(f"Analyzing PDF: {pdf_path}")
        
        try:
            # Open PDF document
            doc = fitz.open(str(pdf_path))
            
            # Extract title and headings
            title = self._extract_title(doc)
            outline = self._extract_headings(doc)
            
            doc.close()
            
            result = {
                "title": title,
                "outline": outline
            }
            
            self.logger.info(f"Extracted {len(outline)} headings")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            raise
    
    def _extract_title(self, doc: fitz.Document) -> str:
        """Extract document title using multiple strategies"""
        
        # Strategy 1: PDF metadata
        metadata_title = doc.metadata.get('title', '').strip()
        if metadata_title and len(metadata_title) > 3:
            self.logger.info(f"Title from metadata: {metadata_title}")
            return metadata_title
        
        # Strategy 2: First page largest text
        if len(doc) > 0:
            page = doc[0]
            blocks = page.get_text("dict")
            
            title_candidates = []
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            font_size = span["size"]
                            
                            # Title criteria
                            if (len(text) > 5 and len(text) < 200 and 
                                font_size > self.min_font_size_threshold and
                                not re.match(r'^\d+$', text)):  # Not just numbers
                                
                                title_candidates.append({
                                    'text': text,
                                    'font_size': font_size,
                                    'y_position': span['bbox'][1]
                                })
            
            # Sort by font size and position (top of page)
            if title_candidates:
                title_candidates.sort(key=lambda x: (-x['font_size'], x['y_position']))
                best_title = title_candidates[0]['text']
                self.logger.info(f"Title from content analysis: {best_title}")
                return best_title
        
        # Fallback
        return "Untitled Document"
    
    def _extract_headings(self, doc: fitz.Document) -> List[Dict]:
        """Extract headings with intelligent level detection"""
        
        all_text_elements = []
        
        # First pass: collect all text elements with metadata
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            
                            if len(text) > 3:  # Minimum text length
                                element = {
                                    'text': text,
                                    'font_size': span['size'],
                                    'font': span['font'],
                                    'flags': span['flags'],  # Bold, italic, etc.
                                    'page': page_num + 1,
                                    'bbox': span['bbox'],
                                    'y_position': span['bbox'][1]
                                }
                                all_text_elements.append(element)
        
        # Analyze font patterns
        font_sizes = [elem['font_size'] for elem in all_text_elements]
        avg_font_size = statistics.mean(font_sizes) if font_sizes else 12
        font_size_std = statistics.stdev(font_sizes) if len(font_sizes) > 1 else 2
        
        # Determine heading candidates
        heading_candidates = []
        
        for element in all_text_elements:
            is_heading = self._is_heading_candidate(element, avg_font_size, font_size_std)
            
            if is_heading:
                heading_level = self._determine_heading_level(element, avg_font_size)
                
                heading_candidates.append({
                    'level': heading_level,
                    'text': element['text'],
                    'page': element['page'],
                    'font_size': element['font_size']
                })
        
        # Clean and deduplicate headings
        cleaned_headings = self._clean_headings(heading_candidates)
        
        # Sort by page and position
        cleaned_headings.sort(key=lambda x: (x['page'], x.get('y_position', 0)))
        
        return cleaned_headings
    
    def _is_heading_candidate(self, element: Dict, avg_font_size: float, font_size_std: float) -> bool:
        """Determine if text element is likely a heading"""
        
        text = element['text']
        font_size = element['font_size']
        flags = element['flags']
        
        # Font size based detection
        size_threshold = avg_font_size + (self.font_size_variance_threshold * font_size_std)
        is_large_font = font_size > size_threshold
        
        # Bold text detection (flag 16 = bold)
        is_bold = flags & 2**4  # Bold flag
        
        # Pattern matching
        matches_pattern = any(re.match(pattern, text) for pattern in self.heading_patterns)
        
        # Length constraints
        reasonable_length = 5 <= len(text) <= 200
        
        # Exclude common false positives
        is_not_noise = not re.match(r'^[\d\s\-_\.]+$', text)  # Not just numbers/symbols
        is_not_url = not ('http' in text.lower() or 'www' in text.lower())
        is_not_email = '@' not in text
        
        # Combined scoring
        heading_score = 0
        if is_large_font: heading_score += 3
        if is_bold: heading_score += 2
        if matches_pattern: heading_score += 4
        if reasonable_length: heading_score += 1
        
        return (heading_score >= 3 and is_not_noise and 
                is_not_url and is_not_email)
    
    def _determine_heading_level(self, element: Dict, avg_font_size: float) -> str:
        """Determine heading level (H1, H2, H3)"""
        
        text = element['text']
        font_size = element['font_size']
        
        # Pattern-based level detection
        if re.match(r'^\d+\.\s+', text):  # 1. Main section
            return "H1"
        elif re.match(r'^\d+\.\d+\s+', text):  # 1.1 Subsection
            return "H2"  
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):  # 1.1.1 Sub-subsection
            return "H3"
        
        # Font size based level detection
        size_diff = font_size - avg_font_size
        
        if size_diff > 6:
            return "H1"
        elif size_diff > 3:
            return "H2"
        else:
            return "H3"
    
    def _clean_headings(self, headings: List[Dict]) -> List[Dict]:
        """Clean and deduplicate headings"""
        
        seen_texts = set()
        cleaned = []
        
        for heading in headings:
            text = heading['text'].strip()
            
            # Skip duplicates
            if text in seen_texts:
                continue
                
            # Skip very short headings
            if len(text) < 3:
                continue
            
            # Clean text
            cleaned_text = re.sub(r'\s+', ' ', text)
            
            cleaned_heading = {
                'level': heading['level'],
                'text': cleaned_text,
                'page': heading['page']
            }
            
            cleaned.append(cleaned_heading)
            seen_texts.add(text)
        
        return cleaned
    
    def save_result(self, result: Dict, output_path: Path) -> None:
        """Save extraction result to JSON file"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise