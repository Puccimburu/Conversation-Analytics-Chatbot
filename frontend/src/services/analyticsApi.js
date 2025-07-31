import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Create axios instance with default config
const analyticsApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout for analytics queries
  headers: {
    'Content-Type': 'application/json',
  },
});

// Analytics query function
export const sendAnalyticsQuery = async (question) => {
  try {
    const response = await analyticsApi.post('/query', {
      question: question,
      timestamp: Date.now()
    });
    
    return {
      success: true,
      data: response.data,
      timestamp: Date.now()
    };
  } catch (error) {
    console.error('Analytics API Error:', error);
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Failed to process analytics query',
      timestamp: Date.now()
    };
  }
};

// Health check function
export const checkApiHealth = async () => {
  try {
    const response = await analyticsApi.get('/health');
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

export default analyticsApi;