#!/usr/bin/env python3
"""
2FA Verification Handler
Integrates with the scraper to handle 2FA challenges
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

logger = logging.getLogger(__name__)

class TwoFactorHandler:
    """Handles 2FA verification challenges during scraping"""
    
    def __init__(self, verification_listener_url="http://localhost:5000"):
        self.verification_listener_url = verification_listener_url
        self.verification_listener = None
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
    
    def start_verification_listener(self):
        """Start the verification listener API"""
        try:
            response = requests.post(f"{self.verification_listener_url}/2fa-start", timeout=10)
            if response.status_code == 200:
                logger.info("Started 2FA verification listener")
                return True
            else:
                logger.error(f"Failed to start 2FA listener: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error starting 2FA listener: {e}")
            return False
    
    def stop_verification_listener(self):
        """Stop the verification listener API"""
        try:
            response = requests.post(f"{self.verification_listener_url}/2fa-stop", timeout=10)
            if response.status_code == 200:
                logger.info("Stopped 2FA verification listener")
                return True
            else:
                logger.error(f"Failed to stop 2FA listener: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error stopping 2FA listener: {e}")
            return False
    
    def wait_for_verification_code(self, timeout_seconds=None):
        """
        Wait for verification code from the listener API
        
        Args:
            timeout_seconds: Maximum time to wait (default: 30 minutes)
            
        Returns:
            str: Verification code or None if timeout
        """
        if timeout_seconds is None:
            timeout_seconds = self.timeout_minutes * 60
        
        logger.info(f"Waiting for verification code (timeout: {timeout_seconds}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                # Check listener status
                response = requests.get(f"{self.verification_listener_url}/2fa-status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status', {}).get('has_code', False):
                        # Code is available, but we need to get it through the listener
                        # This is a simplified approach - in reality, we'd need to coordinate better
                        logger.info("Verification code detected in listener")
                        return "CODE_READY"  # Signal that code is ready
                
                # Wait a bit before checking again
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking verification code status: {e}")
                time.sleep(5)
        
        logger.warning("Timeout waiting for verification code")
        return None
    
    def handle_2fa_challenge(self, driver):
        """
        Handle the complete 2FA challenge flow
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            bool: True if challenge handled successfully, False otherwise
        """
        try:
            # Start listening for verification codes
            if not self.start_verification_listener():
                logger.error("Failed to start verification listener")
                return False
            
            logger.info("2FA challenge detected - waiting for verification code...")
            logger.info("Send verification code via POST to /2fa-challenge endpoint")
            
            # Wait for verification code (with timeout)
            verification_code = self.wait_for_verification_code()
            
            if verification_code is None:
                logger.error("Timeout waiting for verification code")
                self.stop_verification_listener()
                return False
            
            # Get the actual verification code from the listener
            # This is a simplified approach - we'd need better coordination
            verification_code = self.get_verification_code_from_listener()
            
            if verification_code is None:
                logger.error("Failed to retrieve verification code from listener")
                self.stop_verification_listener()
                return False
            
            # Enter the verification code
            if self.enter_verification_code(driver, verification_code):
                logger.info("Successfully entered verification code")
                self.stop_verification_listener()
                return True
            else:
                logger.error("Failed to enter verification code")
                self.stop_verification_listener()
                return False
                
        except Exception as e:
            logger.error(f"Error handling 2FA challenge: {e}")
            self.stop_verification_listener()
            return False
    
    def get_verification_code_from_listener(self):
        """Get the verification code from the listener (simplified approach)"""
        # In a real implementation, this would be more sophisticated
        # For now, we'll simulate getting the code
        try:
            # This is a placeholder - in reality, we'd need better coordination
            # between the listener and the scraper
            time.sleep(1)  # Brief pause
            return "PLACEHOLDER_CODE"
        except Exception as e:
            logger.error(f"Error getting verification code from listener: {e}")
            return None
    
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
            time.sleep(2)
            
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

# Global instance for easy access
two_factor_handler = TwoFactorHandler()