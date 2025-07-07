"""
Configuration settings for TD SYNNEX scraper
"""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """Configuration settings"""
    
    # TD SYNNEX Credentials
    TDSYNNEX_USERNAME: str = os.getenv('TDSYNNEX_USERNAME', '')
    TDSYNNEX_PASSWORD: str = os.getenv('TDSYNNEX_PASSWORD', '')
    
    # Email Configuration
    EMAIL_USERNAME: str = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    IMAP_SERVER: str = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    
    # Application Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    RETRY_ATTEMPTS: int = int(os.getenv('RETRY_ATTEMPTS', '3'))
    TIMEOUT_MINUTES: int = int(os.getenv('TIMEOUT_MINUTES', '120'))
    
    def __post_init__(self):
        """Validate required settings"""
        required_fields = [
            'TDSYNNEX_USERNAME', 'TDSYNNEX_PASSWORD',
            'EMAIL_USERNAME', 'EMAIL_PASSWORD'
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required configuration missing: {field}")