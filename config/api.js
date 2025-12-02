/**
 * API Configuration for TracBack
 * 
 * Set API_BASE_URL environment variable for production:
 * For Cassini deployment: NEXT_PUBLIC_API_URL=https://your-domain.kent.edu/api
 * For local development: NEXT_PUBLIC_API_URL=http://localhost:5000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  
  // Auth endpoints
  AUTH: {
    LOGIN: `${API_BASE_URL}/api/auth/login`,
    SIGNUP: `${API_BASE_URL}/api/auth/signup`,
    REQUEST_PASSWORD_RESET: `${API_BASE_URL}/api/auth/request-password-reset`,
    RESET_PASSWORD: `${API_BASE_URL}/api/auth/reset-password`,
  },
  
  // Item endpoints
  ITEMS: {
    LOST: `${API_BASE_URL}/api/lost-items`,
    FOUND: `${API_BASE_URL}/api/found-items`,
    REPORT: `${API_BASE_URL}/api/report`,
  },
  
  // User endpoints
  USER: {
    PROFILE: (userId) => `${API_BASE_URL}/api/user/${userId}`,
    REPORTS: (userId) => `${API_BASE_URL}/api/user/${userId}/reports-with-matches`,
  },
  
  // Claim endpoints
  CLAIMS: {
    ATTEMPTS: (itemId) => `${API_BASE_URL}/api/claim-attempts/${itemId}`,
    UPDATE: `${API_BASE_URL}/api/update-claim-attempt`,
    FINALIZE: `${API_BASE_URL}/api/finalize-claim`,
  },
  
  // Message endpoints
  MESSAGES: {
    CONVERSATIONS: `${API_BASE_URL}/api/messages/conversations`,
    MESSAGES: `${API_BASE_URL}/api/messages`,
    CREATE_CONVERSATION: `${API_BASE_URL}/api/create-conversation`,
    CONVERSATION_DETAILS: `${API_BASE_URL}/api/get-conversation-details`,
  },
  
  // Security questions
  SECURITY: {
    QUESTIONS: `${API_BASE_URL}/api/security-questions/bulk`,
  },
  
  // Moderation
  MODERATION: {
    CHECK: `${API_BASE_URL}/api/check-moderator`,
  },
  
  // Uploads
  UPLOADS: (filename) => `${API_BASE_URL}/api/uploads/${filename}`,
};

export default API_CONFIG;
