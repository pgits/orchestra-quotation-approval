#!/usr/bin/env python3
"""
mitmproxy configuration script for capturing 2FA authentication flows
"""

import json
import logging
from datetime import datetime
from mitmproxy import http
from mitmproxy import ctx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/mitm.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AuthFlowCapture:
    """Capture and log authentication flows"""
    
    def __init__(self):
        self.flows = []
        self.auth_domains = [
            'login.microsoftonline.com',
            'account.live.com',
            'login.live.com',
            'accounts.google.com',
            'auth.google.com',
            'api.github.com',
            'github.com',
            'hexalinks.sharepoint.com',
            'tdsynnex.com'
        ]
        
    def request(self, flow: http.HTTPFlow) -> None:
        """Process incoming requests"""
        request = flow.request
        
        # Log all requests to auth-related domains
        if any(domain in request.pretty_host for domain in self.auth_domains):
            logger.info(f"AUTH REQUEST: {request.method} {request.pretty_url}")
            
            # Log headers for auth requests
            auth_headers = {}
            for name, value in request.headers.items():
                if any(keyword in name.lower() for keyword in ['auth', 'token', 'cookie', 'session']):
                    auth_headers[name] = value
            
            if auth_headers:
                logger.info(f"AUTH HEADERS: {json.dumps(auth_headers, indent=2)}")
        
        # Log POST requests (likely form submissions)
        if request.method == "POST":
            logger.info(f"POST REQUEST: {request.pretty_url}")
            
            # Try to log form data
            if request.content:
                try:
                    content_type = request.headers.get('content-type', '').lower()
                    if 'application/x-www-form-urlencoded' in content_type:
                        logger.info(f"FORM DATA: {request.content.decode('utf-8')}")
                    elif 'application/json' in content_type:
                        logger.info(f"JSON DATA: {request.content.decode('utf-8')}")
                except Exception as e:
                    logger.warning(f"Could not decode request content: {e}")
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Process responses"""
        request = flow.request
        response = flow.response
        
        # Log responses from auth domains
        if any(domain in request.pretty_host for domain in self.auth_domains):
            logger.info(f"AUTH RESPONSE: {response.status_code} {request.pretty_url}")
            
            # Log Set-Cookie headers
            if 'set-cookie' in response.headers:
                logger.info(f"SET-COOKIE: {response.headers['set-cookie']}")
            
            # Log redirects
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('location', '')
                logger.info(f"REDIRECT: {response.status_code} -> {location}")
        
        # Log error responses
        if response.status_code >= 400:
            logger.warning(f"ERROR RESPONSE: {response.status_code} {request.pretty_url}")
            
            # Try to log error content
            if response.content:
                try:
                    content = response.content.decode('utf-8')[:1000]  # First 1000 chars
                    logger.warning(f"ERROR CONTENT: {content}")
                except:
                    pass
        
        # Store flow for later analysis
        flow_data = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'url': request.pretty_url,
            'host': request.pretty_host,
            'status_code': response.status_code,
            'request_headers': dict(request.headers),
            'response_headers': dict(response.headers),
            'is_auth_flow': any(domain in request.pretty_host for domain in self.auth_domains)
        }
        
        self.flows.append(flow_data)
        
        # Save flows to file periodically
        if len(self.flows) % 10 == 0:
            self.save_flows()
    
    def save_flows(self):
        """Save captured flows to JSON file"""
        try:
            with open('/app/logs/captured_flows.json', 'w') as f:
                json.dump(self.flows, f, indent=2)
            logger.info(f"Saved {len(self.flows)} flows to file")
        except Exception as e:
            logger.error(f"Error saving flows: {e}")

# Initialize the capture addon
addons = [
    AuthFlowCapture()
]

def load(loader):
    """Load configuration options"""
    loader.add_option(
        name="auth_capture",
        typespec=bool,
        default=True,
        help="Enable authentication flow capture"
    )