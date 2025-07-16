#!/usr/bin/env python3
"""
Health Server
Provides health check endpoint for Azure Container Instance
"""

import json
import logging
from flask import Flask, jsonify
from threading import Thread

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, main_service):
        self.main_service = main_service
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                status = self.main_service.get_health_status()
                return jsonify(status), 200 if status['status'] == 'healthy' else 503
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e)
                }), 503
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Detailed status endpoint"""
            try:
                status = self.main_service.get_health_status()
                return jsonify(status), 200
            except Exception as e:
                logger.error(f"Status check error: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Metrics endpoint for monitoring"""
            try:
                status = self.main_service.get_health_status()
                
                metrics = {
                    'service_running': 1 if status['is_running'] else 0,
                    'error_count': status['error_count'],
                    'processed_files_count': status['processed_files_count'],
                    'last_check_timestamp': status['last_check_time'],
                    'check_interval_seconds': status['config']['check_interval']
                }
                
                return jsonify(metrics), 200
            except Exception as e:
                logger.error(f"Metrics error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """Start the health server"""
        try:
            logger.info("Starting health server on port 8080")
            self.app.run(host='0.0.0.0', port=8080, debug=False)
        except Exception as e:
            logger.error(f"Health server error: {e}")