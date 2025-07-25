#!/usr/bin/env python3
"""
File Processor for TD SYNNEX Price Files
Handles .eml parsing, .txt extraction, and file validation
"""

import re
import email
import logging
from email.message import EmailMessage
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import io

logger = logging.getLogger(__name__)

class FileProcessor:
    """Processor for TD SYNNEX price files and email attachments"""
    
    def __init__(self, customer_number: str = '701601', pattern: str = r'(\d{6})-(\d{4})-(\d{4})\.txt'):
        self.customer_number = customer_number
        self.filename_pattern = re.compile(pattern)
        
        # File validation settings
        self.max_file_size = 512 * 1024 * 1024  # 512MB limit for Copilot Studio
        self.min_file_size = 1024  # 1KB minimum
        
        logger.info(f"🔧 FileProcessor initialized for customer: {customer_number}")
        logger.info(f"🔧 Filename pattern: {pattern}")
    
    def process_file(self, filename: str, content: bytes) -> Optional[bytes]:
        """
        Process a file (either .txt or .eml) and return cleaned content
        
        Args:
            filename: Name of the file
            content: Raw file content as bytes
            
        Returns:
            Processed content as bytes if successful, None otherwise
        """
        logger.info(f"🔄 Processing file: {filename} ({len(content)} bytes)")
        
        # Validate file size
        if not self._validate_file_size(filename, content):
            return None
        
        try:
            if filename.lower().endswith('.eml'):
                return self._process_eml_file(filename, content)
            elif filename.lower().endswith('.txt'):
                return self._process_txt_file(filename, content)
            else:
                logger.warning(f"⚠️ Unsupported file type: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing file {filename}: {e}")
            return None
    
    def _validate_file_size(self, filename: str, content: bytes) -> bool:
        """
        Validate file size is within acceptable limits
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            True if size is valid, False otherwise
        """
        size = len(content)
        
        if size > self.max_file_size:
            logger.error(f"❌ File {filename} is too large: {size} bytes (max: {self.max_file_size})")
            return False
        
        if size < self.min_file_size:
            logger.error(f"❌ File {filename} is too small: {size} bytes (min: {self.min_file_size})")
            return False
        
        logger.info(f"✅ File size validation passed: {size} bytes")
        return True
    
    def _process_eml_file(self, filename: str, content: bytes) -> Optional[bytes]:
        """
        Process .eml file and extract TD SYNNEX .txt attachment
        
        Args:
            filename: Name of the .eml file
            content: Raw .eml content
            
        Returns:
            Content of extracted .txt file, None if not found
        """
        logger.info(f"📧 Processing .eml file: {filename}")
        
        try:
            # Parse the email message
            msg = email.message_from_bytes(content)
            
            logger.info(f"📧 Email subject: {msg.get('Subject', 'No subject')}")
            logger.info(f"📧 Email from: {msg.get('From', 'Unknown sender')}")
            logger.info(f"📧 Email date: {msg.get('Date', 'Unknown date')}")
            
            # Look for attachments
            txt_attachments = []
            
            for part in msg.walk():
                # Skip non-attachment parts
                if part.get_content_disposition() != 'attachment':
                    continue
                
                attachment_filename = part.get_filename()
                if not attachment_filename:
                    continue
                
                logger.info(f"📎 Found attachment: {attachment_filename}")
                
                # Check if this is a TD SYNNEX price file
                if self._is_valid_td_synnex_filename(attachment_filename):
                    try:
                        attachment_content = part.get_payload(decode=True)
                        if attachment_content:
                            txt_attachments.append({
                                'filename': attachment_filename,
                                'content': attachment_content,
                                'size': len(attachment_content)
                            })
                            logger.info(f"✅ Extracted TD SYNNEX file: {attachment_filename} ({len(attachment_content)} bytes)")
                    except Exception as e:
                        logger.error(f"❌ Error extracting attachment {attachment_filename}: {e}")
            
            if not txt_attachments:
                logger.warning("⚠️ No TD SYNNEX price file attachments found in .eml")
                return None
            
            # Return the most recent attachment (by filename date pattern)
            latest_attachment = self._get_latest_attachment(txt_attachments)
            
            logger.info(f"✅ Using latest attachment: {latest_attachment['filename']}")
            return self._process_txt_content(latest_attachment['content'])
            
        except Exception as e:
            logger.error(f"❌ Error parsing .eml file: {e}")
            return None
    
    def _process_txt_file(self, filename: str, content: bytes) -> Optional[bytes]:
        """
        Process .txt file content
        
        Args:
            filename: Name of the .txt file
            content: Raw .txt content
            
        Returns:
            Processed content, None if invalid
        """
        logger.info(f"📄 Processing .txt file: {filename}")
        
        # Validate filename pattern
        if not self._is_valid_td_synnex_filename(filename):
            logger.error(f"❌ Invalid TD SYNNEX filename pattern: {filename}")
            return None
        
        return self._process_txt_content(content)
    
    def _process_txt_content(self, content: bytes) -> bytes:
        """
        Process and clean .txt file content
        
        Args:
            content: Raw .txt content
            
        Returns:
            Cleaned content
        """
        try:
            # Try to decode as UTF-8 first
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1 encoding
                text = content.decode('latin-1')
                logger.info("📝 Used latin-1 encoding for text file")
            except UnicodeDecodeError:
                # Last resort: ignore decode errors
                text = content.decode('utf-8', errors='ignore')
                logger.warning("⚠️ Some characters may have been lost during decoding")
        
        # Basic cleaning
        lines = text.splitlines()
        
        # Remove empty lines at the beginning and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        # Log some statistics
        logger.info(f"📊 File statistics:")
        logger.info(f"   Lines: {len(lines)}")
        logger.info(f"   Characters: {len(text)}")
        logger.info(f"   Size: {len(content)} bytes")
        
        # Preview first few lines (without logging sensitive data)
        if lines:
            logger.info(f"📝 First line preview: {lines[0][:100]}{'...' if len(lines[0]) > 100 else ''}")
        
        # Return cleaned content as bytes
        cleaned_text = '\n'.join(lines)
        return cleaned_text.encode('utf-8')
    
    def _is_valid_td_synnex_filename(self, filename: str) -> bool:
        """
        Check if filename matches TD SYNNEX price file pattern
        
        Args:
            filename: Name of the file
            
        Returns:
            True if valid TD SYNNEX filename, False otherwise
        """
        if not filename.lower().endswith('.txt'):
            return False
        
        match = self.filename_pattern.match(filename)
        if not match:
            logger.debug(f"❌ Filename doesn't match pattern: {filename}")
            return False
        
        # Extract components - format: 701601-0721-1627.txt
        customer_num, mmdd, unique_id = match.groups()
        
        # Validate customer number matches expected
        if customer_num != self.customer_number:
            logger.debug(f"❌ Customer number mismatch: expected {self.customer_number}, got {customer_num}")
            return False
        
        # Validate MMDD format (month + day)
        if len(mmdd) != 4:
            logger.debug(f"❌ Invalid MMDD format: {mmdd}")
            return False
        
        month = int(mmdd[:2])  # First 2 digits
        day = int(mmdd[2:])    # Last 2 digits
        
        if month < 1 or month > 12:
            logger.debug(f"❌ Invalid month: {month}")
            return False
        
        if day < 1 or day > 31:
            logger.debug(f"❌ Invalid day: {day}")
            return False
        
        logger.debug(f"✅ Valid TD SYNNEX filename: {filename}")
        return True
    
    def _get_latest_attachment(self, attachments: List[Dict]) -> Dict:
        """
        Get the most recent attachment based on filename date
        
        Args:
            attachments: List of attachment dictionaries
            
        Returns:
            Dictionary of the latest attachment
        """
        def extract_date_from_filename(filename: str) -> Tuple[int, int, int, int]:
            """Extract year, month, day from filename for sorting"""
            match = self.filename_pattern.match(filename)
            if match:
                customer_num, mmdd, unique_id = match.groups()
                # Extract month and day from MMDD format
                month = int(mmdd[:2])
                day = int(mmdd[2:])
                # Assume current year for sorting (can be improved)
                current_year = datetime.now().year
                return (current_year, month, day, int(unique_id))
            return (0, 0, 0, 0)
        
        # Sort by date extracted from filename (newest first)
        sorted_attachments = sorted(
            attachments,
            key=lambda x: extract_date_from_filename(x['filename']),
            reverse=True
        )
        
        return sorted_attachments[0]
    
    def parse_filename_info(self, filename: str) -> Optional[Dict]:
        """
        Parse information from TD SYNNEX filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with parsed info, None if invalid
        """
        match = self.filename_pattern.match(filename)
        if not match:
            return None
        
        customer_num, mmdd, unique_id = match.groups()
        
        # Extract month and day from MMDD format
        month = int(mmdd[:2])
        day = int(mmdd[2:])
        
        return {
            'customer_number': customer_num,
            'month': month,
            'day': day,
            'unique_id': unique_id,
            'date_string': f"{month:02d}-{day:02d}",
            'mmdd': mmdd,
            'full_pattern': f"{customer_num}-{mmdd}-{unique_id}"
        }
    
    def validate_file_content(self, content: bytes) -> Dict:
        """
        Validate and analyze file content
        
        Args:
            content: File content to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': False,
            'size_bytes': len(content),
            'encoding': 'unknown',
            'line_count': 0,
            'has_data': False,
            'errors': []
        }
        
        # Check size
        if len(content) == 0:
            validation_result['errors'].append('File is empty')
            return validation_result
        
        # Try to decode and analyze
        try:
            text = content.decode('utf-8')
            validation_result['encoding'] = 'utf-8'
        except UnicodeDecodeError:
            try:
                text = content.decode('latin-1')
                validation_result['encoding'] = 'latin-1'
            except UnicodeDecodeError:
                validation_result['errors'].append('Unable to decode file content')
                return validation_result
        
        # Analyze content
        lines = text.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        
        validation_result['line_count'] = len(lines)
        validation_result['non_empty_lines'] = len(non_empty_lines)
        validation_result['has_data'] = len(non_empty_lines) > 0
        
        # Check if it looks like price data
        if self._looks_like_price_data(text):
            validation_result['content_type'] = 'price_data'
        else:
            validation_result['content_type'] = 'unknown'
            validation_result['errors'].append('Content does not appear to be price data')
        
        # Set overall validity
        validation_result['valid'] = (
            len(validation_result['errors']) == 0 and
            validation_result['has_data'] and
            validation_result['size_bytes'] <= self.max_file_size
        )
        
        return validation_result
    
    def _looks_like_price_data(self, text: str) -> bool:
        """
        Check if text content looks like price/inventory data
        
        Args:
            text: Text content to analyze
            
        Returns:
            True if content appears to be price data
        """
        # Look for common price data indicators
        price_indicators = [
            'price', 'cost', 'msrp', 'list', 'net',
            'qty', 'quantity', 'stock', 'inventory',
            'part', 'sku', 'model', 'product',
            'manufacturer', 'vendor', 'brand'
        ]
        
        text_lower = text.lower()
        
        # Check for common delimiters (CSV, TSV, pipe-separated)
        has_delimiters = any(char in text for char in [',', '\t', '|'])
        
        # Check for price indicators
        has_price_indicators = sum(1 for indicator in price_indicators if indicator in text_lower) >= 3
        
        # Check for numeric data (prices, quantities)
        has_numbers = bool(re.search(r'\d+\.?\d*', text))
        
        return has_delimiters and has_price_indicators and has_numbers