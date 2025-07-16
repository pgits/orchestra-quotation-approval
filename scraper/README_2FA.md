# 2FA Challenge Handler for TD SYNNEX Scraper

This module adds 2FA (Two-Factor Authentication) support to the TD SYNNEX scraper, allowing it to handle verification code challenges automatically.

## Overview

When TD SYNNEX detects a new IP address or suspicious activity, it presents a 2FA challenge page that requires entering a verification code sent to the user's email. This system handles that challenge automatically.

## Files

- `verification_listener.py` - Core listener class for handling verification codes
- `integrated_verification_handler.py` - Selenium integration for 2FA page detection and handling
- `run_verification_api.py` - Standalone API server for receiving verification codes
- `production_scraper_with_2fa.py` - Updated scraper with 2FA support
- `test_2fa_api.sh` - Test commands for the API
- `test_2fa_integration.py` - Integration tests

## How It Works

1. **2FA Detection**: The scraper detects when a 2FA challenge page appears
2. **API Listening**: Starts listening for verification codes via HTTP API
3. **Manual Code Entry**: User receives email and sends code via curl command
4. **Automatic Processing**: Code is automatically entered into the form
5. **Continuation**: Scraper continues normal operation after successful 2FA

## Usage

### 1. Start the API Server

```bash
python3 run_verification_api.py
```

The API will be available at `http://localhost:5000`

### 2. Run the Scraper

```bash
python3 production_scraper_with_2fa.py
```

### 3. Handle 2FA Challenge

When the scraper detects a 2FA challenge, it will:
- Automatically start listening for verification codes
- Display instructions in the console
- Wait up to 30 minutes for the verification code

### 4. Send Verification Code

When you receive the verification code in your email, send it using:

```bash
curl -X POST http://localhost:5000/2fa-challenge \
  -H 'Content-Type: application/json' \
  -d '{"verificationId": "YOUR_CODE_HERE"}'
```

Replace `YOUR_CODE_HERE` with the actual verification code from your email.

## API Endpoints

### POST /2fa-challenge
Submit a verification code.

**Request:**
```json
{
  "verificationId": "123456"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Verification code received successfully",
  "verificationId": "123456",
  "timestamp": "2025-07-16T20:00:00.000Z"
}
```

**Response (Not Waiting):**
```json
{
  "success": false,
  "message": "Not currently waiting for verification code",
  "verificationId": "123456",
  "timestamp": "2025-07-16T20:00:00.000Z"
}
```

### GET /2fa-status
Check the current status of the 2FA listener.

**Response:**
```json
{
  "success": true,
  "status": {
    "waiting_for_code": true,
    "has_code": false,
    "code_received_time": null
  },
  "timestamp": "2025-07-16T20:00:00.000Z"
}
```

### POST /2fa-start
Start listening for verification codes.

### POST /2fa-stop
Stop listening for verification codes.

### GET /health
Health check endpoint.

## Error Handling

- **Invalid JSON**: Returns 400 Bad Request
- **Missing verificationId**: Returns 400 Bad Request
- **Not waiting for code**: Returns 409 Conflict
- **Timeout**: After 30 minutes, the listener automatically stops waiting

## Testing

### Test the API
```bash
./test_2fa_api.sh
```

### Test Integration
```bash
python3 test_2fa_integration.py
```

### Manual Testing Flow

1. Start API server:
   ```bash
   python3 run_verification_api.py
   ```

2. In another terminal, test the flow:
   ```bash
   # Start listening
   curl -X POST http://localhost:5000/2fa-start
   
   # Check status
   curl -X GET http://localhost:5000/2fa-status
   
   # Send verification code
   curl -X POST http://localhost:5000/2fa-challenge \
     -H 'Content-Type: application/json' \
     -d '{"verificationId": "123456"}'
   
   # Check status again
   curl -X GET http://localhost:5000/2fa-status
   ```

## Security Notes

- The API runs on localhost only by default
- Verification codes are not logged in production
- The API has a 30-minute timeout for security
- Only accepts POST requests with proper JSON content type

## Troubleshooting

### Common Issues

1. **API not responding**: Check if the API server is running on port 5000
2. **Scraper not detecting 2FA**: Ensure the page contains the expected elements
3. **Code not accepted**: Verify the verification code is correct and not expired
4. **Timeout**: Make sure to send the code within 30 minutes

### Debug Mode

To enable debug logging, set the logging level to DEBUG in the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

For production use:
1. Consider using a process manager like systemd or supervisor
2. Add proper error handling and monitoring
3. Use environment variables for configuration
4. Consider using HTTPS for the API endpoint
5. Add rate limiting to prevent abuse

## Integration with Existing Scraper

To integrate with your existing scraper:

1. Import the handler:
   ```python
   from integrated_verification_handler import IntegratedTwoFactorHandler
   ```

2. Initialize in your scraper:
   ```python
   self.two_fa_handler = IntegratedTwoFactorHandler()
   ```

3. Check for 2FA after login:
   ```python
   if self.two_fa_handler.detect_2fa_challenge(self.driver):
       if self.two_fa_handler.handle_2fa_challenge(self.driver):
           logger.info("2FA challenge handled successfully")
       else:
           logger.error("Failed to handle 2FA challenge")
           return False
   ```

That's it! The handler will automatically manage the 2FA flow when needed.