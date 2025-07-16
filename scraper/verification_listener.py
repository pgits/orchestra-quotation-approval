#!/usr/bin/env python3
"""
2FA Verification Listener API
Provides an endpoint to receive verification codes for 2FA challenges
"""

import json
import time
import threading
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class VerificationListener:
    """Handles 2FA verification code listening and storage"""
    
    def __init__(self):
        self.verification_code = None
        self.waiting_for_code = False
        self.code_received_time = None
        self.timeout_duration = 30 * 60  # 30 minutes in seconds
        self.lock = threading.Lock()
    
    def start_waiting(self):
        """Start waiting for verification code"""
        with self.lock:
            self.verification_code = None
            self.waiting_for_code = True
            self.code_received_time = None
            logger.info("Started waiting for 2FA verification code")
    
    def stop_waiting(self):
        """Stop waiting for verification code"""
        with self.lock:
            self.waiting_for_code = False
            self.verification_code = None
            self.code_received_time = None
            logger.info("Stopped waiting for 2FA verification code")
    
    def set_verification_code(self, code):
        """Set the verification code when received"""
        with self.lock:
            if self.waiting_for_code:
                self.verification_code = code
                self.code_received_time = datetime.now()
                logger.info(f"Received verification code: {code}")
                return True
            else:
                logger.warning(f"Received verification code but not waiting: {code}")
                return False
    
    def get_verification_code(self, timeout_seconds=None):
        """
        Wait for and return verification code
        
        Args:
            timeout_seconds: Maximum time to wait (default: 30 minutes)
            
        Returns:
            str: Verification code or None if timeout
        """
        if timeout_seconds is None:
            timeout_seconds = self.timeout_duration
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            with self.lock:
                if self.verification_code is not None:
                    code = self.verification_code
                    self.verification_code = None
                    self.waiting_for_code = False
                    logger.info(f"Returning verification code: {code}")
                    return code
            
            # Sleep for a short time to avoid busy waiting
            time.sleep(0.5)
        
        logger.warning("Timeout waiting for verification code")
        self.stop_waiting()
        return None
    
    def is_waiting(self):
        """Check if currently waiting for verification code"""
        with self.lock:
            return self.waiting_for_code
    
    def get_status(self):
        """Get current status"""
        with self.lock:
            return {
                "waiting_for_code": self.waiting_for_code,
                "has_code": self.verification_code is not None,
                "code_received_time": self.code_received_time.isoformat() if self.code_received_time else None
            }

# Global instance
verification_listener = VerificationListener()

@app.route('/2fa-challenge', methods=['POST'])
def handle_2fa_challenge():
    """
    Handle 2FA challenge verification code submission
    
    Expected JSON: {"verificationId": "12345"}
    """
    try:
        # Parse JSON request
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "success": False
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'verificationId' not in data:
            return jsonify({
                "error": "Missing required field: verificationId",
                "success": False
            }), 400
        
        verification_id = data['verificationId']
        
        # Validate verification ID
        if not verification_id or not isinstance(verification_id, str):
            return jsonify({
                "error": "verificationId must be a non-empty string",
                "success": False
            }), 400
        
        # Set the verification code
        code_accepted = verification_listener.set_verification_code(verification_id)
        
        if code_accepted:
            response = {
                "success": True,
                "message": "Verification code received successfully",
                "verificationId": verification_id,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"2FA challenge API: Code accepted - {verification_id}")
        else:
            response = {
                "success": False,
                "message": "Not currently waiting for verification code",
                "verificationId": verification_id,
                "timestamp": datetime.now().isoformat()
            }
            logger.warning(f"2FA challenge API: Code rejected - {verification_id}")
        
        return jsonify(response), 200 if code_accepted else 409
        
    except Exception as e:
        logger.error(f"Error handling 2FA challenge: {e}")
        return jsonify({
            "error": "Internal server error",
            "success": False
        }), 500

@app.route('/2fa-status', methods=['GET'])
def get_2fa_status():
    """Get current 2FA listener status"""
    try:
        status = verification_listener.get_status()
        return jsonify({
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting 2FA status: {e}")
        return jsonify({
            "error": "Internal server error",
            "success": False
        }), 500

@app.route('/2fa-start', methods=['POST'])
def start_2fa_listening():
    """Start listening for 2FA verification codes"""
    try:
        verification_listener.start_waiting()
        return jsonify({
            "success": True,
            "message": "Started listening for 2FA verification code",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error starting 2FA listening: {e}")
        return jsonify({
            "error": "Internal server error",
            "success": False
        }), 500

@app.route('/2fa-stop', methods=['POST'])
def stop_2fa_listening():
    """Stop listening for 2FA verification codes"""
    try:
        verification_listener.stop_waiting()
        return jsonify({
            "success": True,
            "message": "Stopped listening for 2FA verification code",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error stopping 2FA listening: {e}")
        return jsonify({
            "error": "Internal server error",
            "success": False
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "2FA Verification Listener",
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    logger.info("Starting 2FA Verification Listener API")
    app.run(host='0.0.0.0', port=5000, debug=False)