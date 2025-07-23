// src/context/ChatContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';

const ChatContext = createContext();

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [conversations, setConversations] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
    // Initialize with sample conversations if needed
    if (conversations.length === 0) {
      initializeSampleConversations();
    }
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/health');
      if (response.ok) {
        const health = await response.json();
        setBackendStatus(health.status === 'healthy' ? 'connected' : 'unavailable');
      } else {
        setBackendStatus('unavailable');
      }
    } catch (error) {
      console.log('Backend not available, using mock data');
      setBackendStatus('unavailable');
    }
  };

  const initializeSampleConversations = () => {
    const sampleConversations = [
      {
        id: 'conv_1',
        title: 'Smartphone vs Laptop Sales Comparison',
        category: 'analysis',
        priority: 'high',
        lastMessage: '2 hours ago',
        messageCount: 5,
        unreadCount: 0,
        lastActivity: Date.now() - 7200000, // 2 hours ago
        status: 'active',
        isLive: false,
        participants: 1,
        responses: []
      },
      {
        id: 'conv_2',
        title: 'Top 5 Selling Products Analysis',
        category: 'analysis',
        priority: 'medium',
        lastMessage: '1 day ago',
        messageCount: 3,
        unreadCount: 1,
        lastActivity: Date.now() - 86400000, // 1 day ago
        status: 'active',
        isLive: false,
        participants: 1,
        responses: []
      },
      {
        id: 'conv_3',
        title: 'Monthly Sales Trends Line Chart',
        category: 'analysis',
        priority: 'medium',
        lastMessage: '3 days ago',
        messageCount: 7,
        unreadCount: 0,
        lastActivity: Date.now() - 259200000, // 3 days ago
        status: 'archived',
        isLive: false,
        participants: 1,
        responses: []
      },
      {
        id: 'conv_4',
        title: 'Revenue by Category Breakdown',
        category: 'analysis',
        priority: 'low',
        lastMessage: '1 week ago',
        messageCount: 2,
        unreadCount: 0,
        lastActivity: Date.now() - 604800000, // 1 week ago
        status: 'active',
        isLive: false,
        participants: 1,
        responses: []
      },
      {
        id: 'conv_5',
        title: 'Customer Distribution Analysis',
        category: 'analysis',
        priority: 'medium',
        lastMessage: '2 weeks ago',
        messageCount: 4,
        unreadCount: 0,
        lastActivity: Date.now() - 1209600000, // 2 weeks ago
        status: 'archived',
        isLive: false,
        participants: 1,
        responses: []
      }
    ];

    setConversations(sampleConversations);
  };

  const addNewChat = (chatConfig) => {
    const newChat = {
      id: `conv_${Date.now()}`,
      title: chatConfig.title || 'New Conversation',
      category: chatConfig.category || 'conversational',
      priority: chatConfig.priority || 'medium',
      lastMessage: 'just now',
      messageCount: 1,
      unreadCount: 0,
      lastActivity: Date.now(),
      status: 'active',
      isLive: true,
      participants: 1,
      responses: [],
      ...chatConfig
    };

    setConversations(prev => [newChat, ...prev]);
    return newChat.id;
  };

  const updateChat = (chatId, updates) => {
    setConversations(prev => 
      prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, ...updates, lastActivity: Date.now() }
          : chat
      )
    );
  };

  const deleteChat = (chatId) => {
    setConversations(prev => prev.filter(chat => chat.id !== chatId));
  };

  const markChatAsRead = (chatId) => {
    updateChat(chatId, { unreadCount: 0 });
  };

  const starChat = (chatId) => {
    updateChat(chatId, { starred: true });
  };

  const unstarChat = (chatId) => {
    updateChat(chatId, { starred: false });
  };

  const archiveChat = (chatId) => {
    updateChat(chatId, { status: 'archived' });
  };

  const unarchiveChat = (chatId) => {
    updateChat(chatId, { status: 'active' });
  };

  // Analytics functions that integrate with your backend
  const submitQuery = async (query, options = {}) => {
    if (backendStatus === 'connected') {
      try {
        const response = await fetch('http://localhost:5000/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            chart_preference: options.chartType || 'auto',
            ...options
          })
        });

        if (response.ok) {
          return await response.json();
        } else {
          throw new Error(`Backend error: ${response.status}`);
        }
      } catch (error) {
        console.error('Query submission error:', error);
        return null;
      }
    }
    return null; // Fall back to mock data in components
  };

  const submitFeedback = async (feedbackData) => {
    if (backendStatus === 'connected') {
      try {
        const response = await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(feedbackData)
        });

        if (response.ok) {
          return await response.json();
        }
      } catch (error) {
        console.error('Feedback submission error:', error);
      }
    }
    return null;
  };

  // Search and filter functions
  const searchConversations = (searchTerm) => {
    if (!searchTerm.trim()) return conversations;
    
    return conversations.filter(conv => 
      conv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conv.category.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const filterConversations = (filter) => {
    switch (filter) {
      case 'active':
        return conversations.filter(conv => conv.status === 'active');
      case 'archived':
        return conversations.filter(conv => conv.status === 'archived');
      case 'starred':
        return conversations.filter(conv => conv.starred);
      case 'unread':
        return conversations.filter(conv => conv.unreadCount > 0);
      default:
        return conversations;
    }
  };

  const sortConversations = (sortBy) => {
    const sorted = [...conversations];
    
    switch (sortBy) {
      case 'recent':
        return sorted.sort((a, b) => b.lastActivity - a.lastActivity);
      case 'oldest':
        return sorted.sort((a, b) => a.lastActivity - b.lastActivity);
      case 'title':
        return sorted.sort((a, b) => a.title.localeCompare(b.title));
      case 'category':
        return sorted.sort((a, b) => a.category.localeCompare(b.category));
      case 'priority':
        const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
        return sorted.sort((a, b) => 
          (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0)
        );
      default:
        return sorted;
    }
  };

  const getConversationStats = () => {
    const stats = {
      total: conversations.length,
      active: conversations.filter(conv => conv.status === 'active').length,
      archived: conversations.filter(conv => conv.status === 'archived').length,
      starred: conversations.filter(conv => conv.starred).length,
      unread: conversations.filter(conv => conv.unreadCount > 0).length,
      categories: {}
    };

    // Category breakdown
    conversations.forEach(conv => {
      stats.categories[conv.category] = (stats.categories[conv.category] || 0) + 1;
    });

    return stats;
  };

  const value = {
    // State
    conversations,
    setConversations,
    backendStatus,
    
    // Chat management
    addNewChat,
    updateChat,
    deleteChat,
    markChatAsRead,
    starChat,
    unstarChat,
    archiveChat,
    unarchiveChat,
    
    // Backend integration
    submitQuery,
    submitFeedback,
    checkBackendHealth,
    
    // Search and filter
    searchConversations,
    filterConversations,
    sortConversations,
    getConversationStats
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};