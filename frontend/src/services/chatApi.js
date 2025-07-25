// File: frontend/src/services/chatApi.js
// Create this new file to handle all backend communication

const API_BASE_URL = 'http://localhost:5000/api';

class ChatApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Helper method for API calls
  async apiCall(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      console.log(`🔍 API Call: ${options.method || 'GET'} ${url}`);
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      console.log(`✅ API Success:`, data);
      return data;
    } catch (error) {
      console.error(`❌ API Error for ${endpoint}:`, error);
      throw error;
    }
  }

  // ============================================================================
  // CHAT MANAGEMENT METHODS
  // ============================================================================

  // Get all chat sessions
  async getAllChats(options = {}) {
    const { limit = 50, offset = 0, status } = options;
    let endpoint = `/chats?limit=${limit}&offset=${offset}`;
    if (status) endpoint += `&status=${status}`;

    return this.apiCall(endpoint);
  }

  // Create new chat session
  async createChat(chatData = {}) {
    return this.apiCall('/chats', {
      method: 'POST',
      body: JSON.stringify(chatData),
    });
  }

  // Get specific chat session
  async getChat(chatId) {
    return this.apiCall(`/chats/${chatId}`);
  }

  // Update chat session
  async updateChat(chatId, updates) {
    return this.apiCall(`/chats/${chatId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Delete chat session
  async deleteChat(chatId, hardDelete = false) {
    const endpoint = `/chats/${chatId}${hardDelete ? '?hard=true' : ''}`;
    return this.apiCall(endpoint, { method: 'DELETE' });
  }

  // Add message to chat
  async addMessageToChat(chatId, messageData) {
    return this.apiCall(`/chats/${chatId}/messages`, {
      method: 'POST',
      body: JSON.stringify(messageData),
    });
  }

  // Search chats
  async searchChats(query, limit = 20) {
    return this.apiCall(`/chats/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  // Get chat statistics
  async getChatStats() {
    return this.apiCall('/chats/stats');
  }

  // ============================================================================
  // QUERY PROCESSING METHODS
  // ============================================================================

  // Send query (with optional chat integration)
  async sendQuery(question, chatId = null) {
    const requestData = { question };
    if (chatId) {
      requestData.chat_id = chatId;
    }

    return this.apiCall('/query', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  // Force AI query processing
  async sendForceAiQuery(question, chatId = null) {
    const requestData = { question };
    if (chatId) {
      requestData.chat_id = chatId;
    }

    return this.apiCall('/query/force-ai', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  // Batch query processing
  async sendBatchQueries(questions) {
    return this.apiCall('/batch_query', {
      method: 'POST',
      body: JSON.stringify({ questions }),
    });
  }

  // ============================================================================
  // SYSTEM METHODS
  // ============================================================================

  // Health check
  async getHealth() {
    return this.apiCall('/health');
  }

  // System test
  async runSystemTest() {
    return this.apiCall('/system/test', { method: 'POST' });
  }

  // Get examples
  async getExamples() {
    return this.apiCall('/examples');
  }

  // Debug collections
  async debugCollections() {
    return this.apiCall('/debug/collections');
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  // Auto-generate chat title from message
  generateChatTitle(message) {
    if (!message) return `Chat ${new Date().toLocaleString()}`;
    
    // Clean and truncate
    let title = message.trim();
    
    // Remove common prefixes
    const prefixes = ['show me', 'what is', 'what are', 'how do', 'can you', 'please'];
    const lowerTitle = title.toLowerCase();
    
    for (const prefix of prefixes) {
      if (lowerTitle.startsWith(prefix)) {
        title = title.substring(prefix.length).trim();
        break;
      }
    }
    
    // Capitalize first letter
    if (title) {
      title = title.charAt(0).toUpperCase() + title.slice(1);
    }
    
    // Truncate if too long
    if (title.length > 50) {
      title = title.substring(0, 47) + '...';
    }
    
    return title || `Chat ${new Date().toLocaleString()}`;
  }

  // Format chat for display
  formatChatForDisplay(chat) {
    return {
      id: chat.chat_id,
      title: chat.title,
      lastMessage: this.getRelativeTime(chat.updated_at),
      timestamp: new Date(chat.updated_at).getTime(),
      category: chat.category || 'conversational',
      priority: 'medium', // Default priority
      isStarred: chat.metadata?.is_favorite || false,
      isShared: false, // Backend doesn't track this yet
      isLive: chat.status === 'active',
      status: chat.status,
      messageCount: chat.metadata?.total_messages || 0,
      participants: 1, // Single user for now
      lastActivity: new Date(chat.metadata?.last_activity || chat.updated_at).getTime(),
      unreadCount: 0, // Backend doesn't track this yet
      isTyping: false,
      sentiment: 'neutral',
      messages: chat.messages || []
    };
  }

  // Get relative time string
  getRelativeTime(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  }

  // Convert backend message to frontend format
  formatMessageForDisplay(message) {
    return {
      id: message.message_id,
      type: message.type, // 'user' | 'assistant' | 'system'
      content: message.content,
      timestamp: new Date(message.timestamp).getTime(),
      chartData: message.chart_data,
      insights: message.insights,
      recommendations: message.recommendations,
      validation: message.validation,
      queryResponse: message.query_response,
      // Add frontend-specific fields
      activeTab: 'answer' // Default tab
    };
  }
}

// Create and export singleton instance
const chatApiService = new ChatApiService();
export default chatApiService;