/**
 * Callback Handler for Hardware Quotation Approval Bot
 * Manages callbacks to parent Copilot Studio agents
 */

const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

class CallbackHandler {
    constructor(config = {}) {
        this.retryConfig = {
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 1000,
            backoffMultiplier: config.backoffMultiplier || 2
        };
        this.timeout = config.timeout || 30000;
        this.deadLetterQueue = [];
    }

    /**
     * Send callback notification to parent agent
     * @param {string} callbackUrl - The callback URL provided by parent agent
     * @param {object} payload - The callback payload
     * @returns {Promise<object>} - Response from callback
     */
    async sendCallback(callbackUrl, payload) {
        const requestId = uuidv4();
        const enrichedPayload = {
            ...payload,
            callbackId: requestId,
            timestamp: new Date().toISOString()
        };

        try {
            return await this.executeWithRetry(
                () => this.makeCallbackRequest(callbackUrl, enrichedPayload, requestId),
                callbackUrl,
                enrichedPayload
            );
        } catch (error) {
            this.handleFailedCallback(callbackUrl, enrichedPayload, error);
            throw error;
        }
    }

    /**
     * Execute callback request with retry logic
     */
    async executeWithRetry(requestFn, callbackUrl, payload) {
        let lastError;
        
        for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
            try {
                const result = await requestFn();
                
                // Log successful callback
                console.log(`Callback successful on attempt ${attempt + 1}`, {
                    callbackUrl,
                    quotationId: payload.quotationId,
                    status: payload.status
                });
                
                return result;
            } catch (error) {
                lastError = error;
                
                if (attempt < this.retryConfig.maxRetries) {
                    const delay = this.calculateRetryDelay(attempt);
                    console.warn(`Callback attempt ${attempt + 1} failed, retrying in ${delay}ms`, {
                        error: error.message,
                        callbackUrl
                    });
                    
                    await this.sleep(delay);
                }
            }
        }
        
        throw lastError;
    }

    /**
     * Make the actual HTTP callback request
     */
    async makeCallbackRequest(callbackUrl, payload, requestId) {
        const response = await axios({
            method: 'POST',
            url: callbackUrl,
            data: payload,
            headers: {
                'Content-Type': 'application/json',
                'X-Copilot-Callback': 'true',
                'X-Request-ID': requestId,
                'X-Callback-Version': '1.0'
            },
            timeout: this.timeout,
            validateStatus: (status) => status < 500 // Don't throw on 4xx errors
        });

        if (response.status >= 400) {
            throw new Error(`Callback failed with status ${response.status}: ${response.statusText}`);
        }

        return response.data;
    }

    /**
     * Calculate retry delay with exponential backoff
     */
    calculateRetryDelay(attempt) {
        return this.retryConfig.retryDelay * Math.pow(this.retryConfig.backoffMultiplier, attempt);
    }

    /**
     * Handle failed callbacks by adding to dead letter queue
     */
    handleFailedCallback(callbackUrl, payload, error) {
        const failedCallback = {
            id: uuidv4(),
            callbackUrl,
            payload,
            error: error.message,
            failedAt: new Date().toISOString(),
            retryCount: this.retryConfig.maxRetries
        };

        this.deadLetterQueue.push(failedCallback);

        console.error('Callback failed after all retries', {
            ...failedCallback,
            stack: error.stack
        });

        // In production, this would persist to a database
        // For now, we'll just keep it in memory
    }

    /**
     * Get failed callbacks from dead letter queue
     */
    getFailedCallbacks() {
        return [...this.deadLetterQueue];
    }

    /**
     * Retry a failed callback from dead letter queue
     */
    async retryFailedCallback(failedCallbackId) {
        const index = this.deadLetterQueue.findIndex(cb => cb.id === failedCallbackId);
        
        if (index === -1) {
            throw new Error('Failed callback not found');
        }

        const failedCallback = this.deadLetterQueue[index];
        
        try {
            const result = await this.sendCallback(
                failedCallback.callbackUrl,
                failedCallback.payload
            );
            
            // Remove from dead letter queue on success
            this.deadLetterQueue.splice(index, 1);
            
            return result;
        } catch (error) {
            // Update retry count
            failedCallback.retryCount++;
            failedCallback.lastRetryAt = new Date().toISOString();
            failedCallback.lastError = error.message;
            
            throw error;
        }
    }

    /**
     * Utility function to sleep
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Create standardized callback payloads
     */
    static createCallbackPayload(quotationId, status, details = {}) {
        const basePayload = {
            quotationId,
            status,
            timestamp: new Date().toISOString()
        };

        switch (status) {
            case 'approved':
                return {
                    ...basePayload,
                    approvedBy: details.approvedBy,
                    approvalRecordId: details.approvalRecordId,
                    approvalNotes: details.approvalNotes
                };
                
            case 'rejected':
                return {
                    ...basePayload,
                    rejectedBy: details.rejectedBy,
                    rejectionRecordId: details.rejectionRecordId,
                    rejectionReason: details.rejectionReason,
                    customReason: details.customReason
                };
                
            case 'pending_information':
                return {
                    ...basePayload,
                    requestId: details.requestId,
                    informationType: details.informationType,
                    customQuestion: details.customQuestion,
                    priority: details.priority,
                    requestedBy: details.requestedBy
                };
                
            default:
                return basePayload;
        }
    }
}

module.exports = CallbackHandler;