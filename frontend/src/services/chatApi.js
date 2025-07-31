// src/services/chatApi.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ChatAPI {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Helper method for making API calls
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }
      
      return data;
    } catch (error) {
      console.error(`ChatAPI Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Create a new chat session
  async createChat(chatData) {
    try {
      const response = await this.makeRequest('/api/chats', {
        method: 'POST',
        body: JSON.stringify({
          title: chatData.title || 'New Chat Session',
          category: chatData.category || 'conversational',
          priority: chatData.priority || 'medium',
          first_message: chatData.first_message || null
        })
      });

      return {
        success: true,
        chat_id: response.chat_id,
        chat: response.chat,
        message: response.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Get all chat sessions
  async getAllChats(options = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (options.limit) queryParams.append('limit', options.limit);
      if (options.offset) queryParams.append('offset', options.offset);
      if (options.status) queryParams.append('status', options.status);
      
      const endpoint = `/api/chats${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await this.makeRequest(endpoint);

      return {
        success: true,
        chats: response.chats || [],
        total: response.total || 0
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        chats: []
      };
    }
  }

  // Get a specific chat session
  async getChat(chatId) {
    try {
      const response = await this.makeRequest(`/api/chats/${chatId}`);

      return {
        success: true,
        chat: response.chat
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Update chat session metadata
  async updateChat(chatId, updates) {
    try {
      const response = await this.makeRequest(`/api/chats/${chatId}`, {
        method: 'PUT',
        body: JSON.stringify(updates)
      });

      return {
        success: true,
        chat: response.chat,
        message: response.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Delete a chat session
  async deleteChat(chatId, hardDelete = false) {
    try {
      const endpoint = `/api/chats/${chatId}${hardDelete ? '?hard=true' : ''}`;
      const response = await this.makeRequest(endpoint, {
        method: 'DELETE'
      });

      return {
        success: true,
        message: response.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Add a message to an existing chat
  async addMessage(chatId, messageData) {
    try {
      const response = await this.makeRequest(`/api/chats/${chatId}/messages`, {
        method: 'POST',
        body: JSON.stringify({
          type: messageData.type || 'user',
          content: messageData.content,
          chart_data: messageData.chart_data || null,
          validation: messageData.validation || null,
          insights: messageData.insights || null,
          recommendations: messageData.recommendations || null,
          query_response: messageData.query_response || null
        })
      });

      return {
        success: true,
        message_id: response.message_id,
        message: response.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Transform backend chat data to frontend format
  transformChatForFrontend(backendChat) {
    return {
      id: backendChat.chat_id,
      title: backendChat.title || 'Untitled Chat',
      category: backendChat.category || 'conversational',
      priority: backendChat.metadata?.priority || 'medium',
      lastMessage: this.getLastMessageTime(backendChat.updated_at),
      messageCount: backendChat.metadata?.total_messages || 0,
      unreadCount: 0, // Could be calculated based on last_read timestamp
      lastActivity: new Date(backendChat.updated_at).getTime(),
      status: backendChat.status || 'active',
      isLive: backendChat.status === 'active',
      participants: 1,
      isStarred: backendChat.metadata?.is_favorite || false,
      isShared: false, // Not implemented yet
      isTyping: false,
      messages: backendChat.messages || [],
      
      // Keep reference to original backend data
      _backendData: backendChat
    };
  }

  // Helper method to format last message time
  getLastMessageTime(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const messageTime = new Date(timestamp);
    const diffMs = now - messageTime;
    
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return messageTime.toLocaleDateString();
  }

  // Get chat statistics
  async getChatStats() {
    try {
      const response = await this.makeRequest('/api/chats/stats');

      return {
        success: true,
        stats: response.stats
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stats: {
          total: 0,
          active: 0,
          archived: 0
        }
      };
    }
  }

  // Search chats
  async searchChats(query, options = {}) {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('q', query);
      
      if (options.limit) queryParams.append('limit', options.limit);
      if (options.category) queryParams.append('category', options.category);
      
      const response = await this.makeRequest(`/api/chats/search?${queryParams.toString()}`);

      return {
        success: true,
        chats: response.chats || [],
        total: response.total || 0
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        chats: []
      };
    }
  }

  // Check if backend is available
  async checkHealth() {
    try {
      const response = await this.makeRequest('/api/health');
      return {
        success: true,
        status: response.status || 'healthy'
      };
    } catch (error) {
      return {
        success: false,
        status: 'unavailable',
        error: error.message
      };
    }
  }
}

// Create and export a singleton instance
const chatAPI = new ChatAPI();
export default chatAPI;