#!/usr/bin/env python3
"""
Integrated 2FA Verification Handler
Combines the listener and handler into a single integrated solution
"""

import re
import time
import requests
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from verification_listener import VerificationListener

logger = logging.getLogger(__name__)

class IntegratedTwoFactorHandler:
    """Integrated 2FA handler with built-in verification listener"""
    
    def __init__(self):
        self.verification_listener = VerificationListener()
        self.timeout_minutes = 30
    
    def detect_2fa_challenge(self, driver):
        """
        Detect if the current page is a 2FA challenge page
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            bool: True if 2FA challenge detected, False otherwise
        """
        try:
            # Get current page source
            page_source = driver.page_source
            
            # Check for 2FA challenge indicators
            indicators = [
                "verification code has been sent to your email",
                "Enter verification code:",
                "newLocCodeValidation.html",
                "verification-code",
                "ipCode",
                "validateForm",
                "Resend verification code"
            ]
            
            # Check if any indicators are present
            for indicator in indicators:
                if indicator.lower() in page_source.lower():
                    logger.info(f"2FA challenge detected: Found indicator '{indicator}'")
                    return True
            
            # Check for specific form action
            if 'action="/ecx/newLocCodeValidation.html"' in page_source:
                logger.info("2FA challenge detected: Found validation form")
                return True
            
            # Check for verification code input field
            try:
                verification_input = driver.find_element(By.ID, "ipCode")
                if verification_input:
                    logger.info("2FA challenge detected: Found verification code input field")
                    return True
            except NoSuchElementException:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting 2FA challenge: {e}")
            return False
    
    def handle_2fa_challenge(self, driver):
        """
        Handle the complete 2FA challenge flow
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            bool: True if challenge handled successfully, False otherwise
        """
        try:
            logger.info("2FA challenge detected - starting verification process")
            
            # Start listening for verification codes
            self.verification_listener.start_waiting()
            
            # Log instructions for sending verification code
            logger.info("=" * 60)
            logger.info("2FA CHALLENGE DETECTED")
            logger.info("Waiting for verification code...")
            logger.info("Send verification code using:")
            logger.info("curl -X POST http://localhost:5000/2fa-challenge \\")
            logger.info("  -H 'Content-Type: application/json' \\")
            logger.info("  -d '{\"verificationId\": \"YOUR_CODE_HERE\"}'")
            logger.info("=" * 60)
            
            # Wait for verification code (with 30 minute timeout)
            verification_code = self.verification_listener.get_verification_code(
                timeout_seconds=self.timeout_minutes * 60
            )
            
            if verification_code is None:
                logger.error("Timeout waiting for verification code (30 minutes)")
                return False
            
            # Enter the verification code
            if self.enter_verification_code(driver, verification_code):
                logger.info("Successfully entered verification code")
                return True
            else:
                logger.error("Failed to enter verification code")
                return False
                
        except Exception as e:
            logger.error(f"Error handling 2FA challenge: {e}")
            self.verification_listener.stop_waiting()
            return False
    
    def enter_verification_code(self, driver, verification_code):
        """
        Enter the verification code into the form
        
        Args:
            driver: Selenium WebDriver instance
            verification_code: The verification code to enter
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the verification code input field
            wait = WebDriverWait(driver, 10)
            
            # Look for the verification code input field
            verification_input = wait.until(
                EC.presence_of_element_located((By.ID, "ipCode"))
            )
            
            # Clear any existing text and enter the verification code
            verification_input.clear()
            verification_input.send_keys(verification_code)
            
            logger.info(f"Entered verification code: {verification_code}")
            
            # Find and click the submit button
            submit_button = driver.find_element(By.ID, "enterButton")
            submit_button.click()
            
            logger.info("Clicked submit button for verification code")
            
            # Wait a moment for the form to submit
            time.sleep(3)
            
            # Check if we're still on the verification page (indicating error)
            if self.detect_2fa_challenge(driver):
                logger.error("Still on 2FA challenge page after submitting code")
                return False
            
            logger.info("Successfully submitted verification code")
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for verification code input field")
            return False
        except NoSuchElementException:
            logger.error("Could not find verification code input field or submit button")
            return False
        except Exception as e:
            logger.error(f"Error entering verification code: {e}")
            return False
    
    def get_listener_instance(self):
        """Get the verification listener instance for API integration"""
        return self.verification_listener

# Global instance for easy access
integrated_2fa_handler = IntegratedTwoFactorHandler()