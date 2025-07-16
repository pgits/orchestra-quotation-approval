#!/usr/bin/env python3
"""
Standalone 2FA Verification API Server
Runs the verification listener API as a standalone service
"""

import sys
import os
import signal
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from verification_listener import VerificationListener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global verification listener instance
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

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    verification_listener.stop_waiting()
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting 2FA Verification Listener API")
    logger.info("Available endpoints:")
    logger.info("  POST /2fa-challenge - Submit verification code")
    logger.info("  GET  /2fa-status    - Check listener status")
    logger.info("  POST /2fa-start     - Start listening")
    logger.info("  POST /2fa-stop      - Stop listening")
    logger.info("  GET  /health        - Health check")
    
    try:
        # Try multiple ports in case default is in use
        ports_to_try = [5001, 5002, 5003, 5000]
        
        for port in ports_to_try:
            try:
                logger.info(f"Trying to start server on port {port}...")
                app.run(host='0.0.0.0', port=port, debug=False)
                break
            except OSError as e:
                if "Address already in use" in str(e):
                    logger.warning(f"Port {port} is already in use, trying next port...")
                    continue
                else:
                    raise
        else:
            logger.error("Could not find an available port to start the server")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)