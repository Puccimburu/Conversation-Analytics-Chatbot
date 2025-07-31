// src/context/ChatContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import chatAPI from '../services/chatApi'; // 🎯 NEW: Import our chat API

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
  const [isLoadingChats, setIsLoadingChats] = useState(false); // 🎯 NEW: Track loading state

  // 🎯 ENHANCED: Check backend health and load real chats
  useEffect(() => {
    initializeChats();
  }, []);

  const initializeChats = async () => {
    setIsLoadingChats(true);
    
    // Check backend health first
    await checkBackendHealth();
    
    // Try to load real chats, fall back to sample data if needed
    await loadInitialChats();
    
    setIsLoadingChats(false);
  };

  const checkBackendHealth = async () => {
    try {
      const healthResponse = await chatAPI.checkHealth();
      if (healthResponse.success) {
        setBackendStatus('connected');
      } else {
        setBackendStatus('unavailable');
      }
    } catch (error) {
      console.log('Backend not available, using local data');
      setBackendStatus('unavailable');
    }
  };

  // 🎯 NEW: Load initial chats from backend
  const loadInitialChats = async () => {
    try {
      if (backendStatus === 'connected') {
        const response = await chatAPI.getAllChats({ limit: 50 });
        
        if (response.success && response.chats.length > 0) {
          // Transform backend chats to frontend format
          const transformedChats = response.chats.map(chat => 
            chatAPI.transformChatForFrontend(chat)
          );
          setConversations(transformedChats);
          return;
        }
      }
      
      // Fallback: Initialize with sample data if no real chats
      if (conversations.length === 0) {
        initializeSampleConversations();
      }
    } catch (error) {
      console.error('Failed to load initial chats:', error);
      // Fallback to sample conversations
      if (conversations.length === 0) {
        initializeSampleConversations();
      }
    }
  };

  // 🎯 STREAMLINED: Simplified sample conversations (only used as fallback)
  const initializeSampleConversations = () => {
    const sampleConversations = [
      {
        id: 'sample_1',
        title: 'Welcome to Analytics Chat',
        category: 'analysis',
        priority: 'medium',
        lastMessage: 'just now',
        messageCount: 1,
        unreadCount: 0,
        lastActivity: Date.now(),
        status: 'active',
        isLive: false,
        participants: 1,
        responses: []
      }
    ];

    setConversations(sampleConversations);
  };

  // 🎯 ENHANCED: Add new chat with backend integration
  const addNewChat = (chatConfig) => {
    const newChat = {
      id: chatConfig.id || `conv_${Date.now()}`, // 🎯 Use provided ID (from backend) or generate
      title: chatConfig.title || 'New Conversation',
      category: chatConfig.category || 'conversational',
      priority: chatConfig.priority || 'medium',
      lastMessage: chatConfig.lastMessage || 'just now',
      messageCount: chatConfig.messageCount || 1,
      unreadCount: chatConfig.unreadCount || 0,
      lastActivity: chatConfig.lastActivity || Date.now(),
      status: chatConfig.status || 'active',
      isLive: chatConfig.isLive !== undefined ? chatConfig.isLive : true,
      participants: chatConfig.participants || 1,
      responses: chatConfig.responses || [],
      ...chatConfig
    };

    setConversations(prev => [newChat, ...prev]);
    return newChat.id;
  };

  // 🎯 ENHANCED: Update chat with backend sync
  const updateChat = async (chatId, updates) => {
    // Update local state immediately for UI responsiveness
    setConversations(prev => 
      prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, ...updates, lastActivity: Date.now() }
          : chat
      )
    );

    // 🎯 NEW: Sync with backend if connected
    if (backendStatus === 'connected') {
      try {
        const chat = conversations.find(c => c.id === chatId);
        if (chat && chat._backendData) {
          await chatAPI.updateChat(chat._backendData.chat_id, updates);
        }
      } catch (error) {
        console.error('Failed to sync chat update with backend:', error);
        // UI already updated, so this is not critical
      }
    }
  };

  // 🎯 ENHANCED: Delete chat with backend sync
  const deleteChat = async (chatId) => {
    // Find the chat first
    const chat = conversations.find(c => c.id === chatId);
    
    // Remove from local state immediately
    setConversations(prev => prev.filter(chat => chat.id !== chatId));

    // 🎯 NEW: Sync with backend if connected
    if (backendStatus === 'connected' && chat && chat._backendData) {
      try {
        await chatAPI.deleteChat(chat._backendData.chat_id);
      } catch (error) {
        console.error('Failed to delete chat from backend:', error);
        // Chat already removed from UI, so this is not critical
      }
    }
  };

  // 🎯 NEW: Refresh chats from backend
  const refreshChats = async () => {
    if (backendStatus === 'connected') {
      setIsLoadingChats(true);
      try {
        const response = await chatAPI.getAllChats({ limit: 50 });
        
        if (response.success) {
          const transformedChats = response.chats.map(chat => 
            chatAPI.transformChatForFrontend(chat)
          );
          setConversations(transformedChats);
        }
      } catch (error) {
        console.error('Failed to refresh chats:', error);
      } finally {
        setIsLoadingChats(false);
      }
    }
  };

  // 🎯 EXISTING: Keep all your existing functions (unchanged)
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

  // 🎯 ENHANCED: Analytics functions with chat_id support
  const submitQuery = async (query, options = {}) => {
    if (backendStatus === 'connected') {
      try {
        const response = await fetch('http://localhost:5000/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            chat_id: options.chat_id || null, // 🎯 NEW: Include chat_id
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

  // 🎯 EXISTING: Keep all your search and filter functions (unchanged)
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

  // 🎯 ENHANCED: Provider value with new functions
  const value = {
    // State
    conversations,
    setConversations,
    backendStatus,
    isLoadingChats, // 🎯 NEW: Loading state
    
    // Chat management (enhanced)
    addNewChat,
    updateChat,
    deleteChat,
    markChatAsRead,
    starChat,
    unstarChat,
    archiveChat,
    unarchiveChat,
    refreshChats, // 🎯 NEW: Refresh function
    
    // Backend integration (enhanced)
    submitQuery,
    submitFeedback,
    checkBackendHealth,
    
    // Search and filter (unchanged)
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