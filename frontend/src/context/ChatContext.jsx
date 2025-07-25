// File: frontend/src/context/ChatContext.jsx
// Replace your existing ChatContext.jsx with this updated version

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import chatApiService from '../services/chatApi';

const ChatContext = createContext();

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================
  
  // Core chat state
  const [conversations, setConversations] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [currentChat, setCurrentChat] = useState(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  
  // Real-time state
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  // ============================================================================
  // INITIALIZATION AND HEALTH CHECK
  // ============================================================================

  const checkBackendHealth = useCallback(async () => {
    try {
      setBackendStatus('checking');
      const health = await chatApiService.getHealth();
      
      if (health.status === 'online') {
        setBackendStatus('connected');
        console.log('✅ Backend connected:', health);
      } else {
        setBackendStatus('degraded');
      }
    } catch (error) {
      console.log('❌ Backend unavailable, using offline mode');
      setBackendStatus('unavailable');
    }
  }, []);

  const loadInitialChats = useCallback(async () => {
    if (backendStatus !== 'connected') return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await chatApiService.getAllChats({ limit: 50 });
      
      if (response.success && response.chats) {
        // Convert backend format to frontend format
        const formattedChats = response.chats.map(chat => 
          chatApiService.formatChatForDisplay(chat)
        );
        
        setConversations(formattedChats);
        setLastSyncTime(new Date().toISOString());
        console.log(`✅ Loaded ${formattedChats.length} chat sessions`);
      }
    } catch (error) {
      console.error('Failed to load chats:', error);
      setError('Failed to load chat history');
      // Fallback to empty state rather than dummy data
      setConversations([]);
    } finally {
      setLoading(false);
    }
  }, [backendStatus]);

  // Initialize on mount
  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  // Load chats when backend becomes available
  useEffect(() => {
    if (backendStatus === 'connected') {
      loadInitialChats();
    }
  }, [backendStatus, loadInitialChats]);

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      checkBackendHealth();
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      setBackendStatus('unavailable');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkBackendHealth]);

  // ============================================================================
  // CHAT MANAGEMENT FUNCTIONS
  // ============================================================================

  const addNewChat = useCallback(async (chatConfig = {}) => {
    try {
      setLoading(true);
      setError(null);

      // Prepare chat data
      const chatData = {
        title: chatConfig.title || `Chat ${new Date().toLocaleString()}`,
        category: chatConfig.category || 'conversational',
        ...chatConfig
      };

      if (backendStatus === 'connected') {
        // Create chat via API
        const response = await chatApiService.createChat(chatData);
        
        if (response.success && response.chat) {
          const formattedChat = chatApiService.formatChatForDisplay(response.chat);
          
          // Add to state
          setConversations(prev => [formattedChat, ...prev]);
          setCurrentChatId(response.chat_id);
          setCurrentChat(formattedChat);
          
          console.log(`✅ Created new chat: ${response.chat_id}`);
          return response.chat_id;
        }
      } else {
        // Offline mode - create temporary chat
        const tempChat = {
          id: `temp_${Date.now()}`,
          title: chatData.title,
          category: chatData.category,
          lastMessage: 'just now',
          timestamp: Date.now(),
          priority: 'medium',
          isStarred: false,
          isShared: false,
          isLive: true,
          status: 'active',
          messageCount: 0,
          participants: 1,
          lastActivity: Date.now(),
          unreadCount: 0,
          isTyping: false,
          sentiment: 'neutral',
          messages: [],
          isOffline: true // Mark as offline
        };
        
        setConversations(prev => [tempChat, ...prev]);
        setCurrentChatId(tempChat.id);
        setCurrentChat(tempChat);
        
        return tempChat.id;
      }
    } catch (error) {
      console.error('Failed to create chat:', error);
      setError('Failed to create new chat');
      return null;
    } finally {
      setLoading(false);
    }
  }, [backendStatus]);

  const loadChat = useCallback(async (chatId) => {
    try {
      setLoading(true);
      setError(null);
      
      if (backendStatus === 'connected') {
        const response = await chatApiService.getChat(chatId);
        
        if (response.success && response.chat) {
          const formattedChat = chatApiService.formatChatForDisplay(response.chat);
          
          // Convert messages to frontend format
          if (response.chat.messages) {
            formattedChat.messages = response.chat.messages.map(msg =>
              chatApiService.formatMessageForDisplay(msg)
            );
          }
          
          setCurrentChatId(chatId);
          setCurrentChat(formattedChat);
          
          console.log(`✅ Loaded chat: ${chatId} with ${formattedChat.messages.length} messages`);
          return formattedChat;
        }
      } else {
        // Offline mode - find in local state
        const localChat = conversations.find(chat => chat.id === chatId);
        if (localChat) {
          setCurrentChatId(chatId);
          setCurrentChat(localChat);
          return localChat;
        }
      }
      
      throw new Error('Chat not found');
    } catch (error) {
      console.error('Failed to load chat:', error);
      setError(`Failed to load chat: ${chatId}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [backendStatus, conversations]);

  const updateChat = useCallback(async (chatId, updates) => {
    try {
      if (backendStatus === 'connected') {
        const response = await chatApiService.updateChat(chatId, updates);
        
        if (response.success) {
          // Update local state
          setConversations(prev => 
            prev.map(chat => 
              chat.id === chatId ? { ...chat, ...updates } : chat
            )
          );
          
          if (currentChatId === chatId && currentChat) {
            setCurrentChat(prev => ({ ...prev, ...updates }));
          }
          
          console.log(`✅ Updated chat: ${chatId}`);
          return true;
        }
      } else {
        // Offline mode - update local state only
        setConversations(prev => 
          prev.map(chat => 
            chat.id === chatId ? { ...chat, ...updates } : chat
          )
        );
        
        if (currentChatId === chatId) {
          setCurrentChat(prev => ({ ...prev, ...updates }));
        }
        
        return true;
      }
    } catch (error) {
      console.error('Failed to update chat:', error);
      setError('Failed to update chat');
      return false;
    }
  }, [backendStatus, currentChatId, currentChat]);

  const deleteChat = useCallback(async (chatId) => {
    try {
      if (backendStatus === 'connected') {
        const response = await chatApiService.deleteChat(chatId);
        
        if (response.success) {
          // Remove from local state
          setConversations(prev => prev.filter(chat => chat.id !== chatId));
          
          if (currentChatId === chatId) {
            setCurrentChatId(null);
            setCurrentChat(null);
          }
          
          console.log(`✅ Deleted chat: ${chatId}`);
          return true;
        }
      } else {
        // Offline mode - remove from local state
        setConversations(prev => prev.filter(chat => chat.id !== chatId));
        
        if (currentChatId === chatId) {
          setCurrentChatId(null);
          setCurrentChat(null);
        }
        
        return true;
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      setError('Failed to delete chat');
      return false;
    }
  }, [backendStatus, currentChatId]);

  // ============================================================================
  // QUERY PROCESSING WITH CHAT INTEGRATION
  // ============================================================================

  const sendQueryWithChat = useCallback(async (question, chatId = null, forceAI = false) => {
    try {
      setLoading(true);
      setError(null);

      const targetChatId = chatId || currentChatId;
      
      if (backendStatus === 'connected') {
        // Send to backend with chat integration
        const response = forceAI 
          ? await chatApiService.sendForceAiQuery(question, targetChatId)
          : await chatApiService.sendQuery(question, targetChatId);
        
        if (response.success) {
          // Update chat in conversations list
          if (targetChatId) {
            setConversations(prev => 
              prev.map(chat => 
                chat.id === targetChatId 
                  ? { 
                      ...chat, 
                      lastMessage: 'just now',
                      lastActivity: Date.now(),
                      messageCount: (chat.messageCount || 0) + 2, // user + assistant
                      isLive: true
                    }
                  : chat
              )
            );
            
            // Reload current chat to get updated messages
            if (currentChatId === targetChatId) {
              await loadChat(targetChatId);
            }
          }
          
          console.log(`✅ Query processed successfully with chat integration`);
          return response;
        }
      } else {
        // Offline mode - return mock response
        return {
          success: false,
          error: 'Backend unavailable - working in offline mode',
          offline: true
        };
      }
    } catch (error) {
      console.error('Failed to send query:', error);
      setError('Failed to send query');
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, [backendStatus, currentChatId, loadChat]);

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================

  const refreshChats = useCallback(async () => {
    if (backendStatus === 'connected') {
      await loadInitialChats();
    }
  }, [loadInitialChats, backendStatus]);

  const searchChats = useCallback(async (query) => {
    if (!query.trim()) return conversations;
    
    try {
      if (backendStatus === 'connected') {
        const response = await chatApiService.searchChats(query);
        if (response.success) {
          return response.chats.map(chat => chatApiService.formatChatForDisplay(chat));
        }
      }
      
      // Fallback to local search
      return conversations.filter(chat => 
        chat.title.toLowerCase().includes(query.toLowerCase())
      );
    } catch (error) {
      console.error('Search failed:', error);
      return conversations.filter(chat => 
        chat.title.toLowerCase().includes(query.toLowerCase())
      );
    }
  }, [conversations, backendStatus]);

  const getChatStats = useCallback(async () => {
    try {
      if (backendStatus === 'connected') {
        return await chatApiService.getChatStats();
      }
      
      // Return local stats
      return {
        success: true,
        statistics: {
          total_chats: conversations.length,
          active_chats: conversations.filter(c => c.status === 'active').length,
          total_messages: conversations.reduce((sum, c) => sum + (c.messageCount || 0), 0),
          system_health: { database_available: false }
        }
      };
    } catch (error) {
      console.error('Failed to get stats:', error);
      return { success: false, error: error.message };
    }
  }, [conversations, backendStatus]);

  // ============================================================================
  // CONTEXT VALUE
  // ============================================================================

  const contextValue = {
    // State
    conversations,
    currentChatId,
    currentChat,
    loading,
    error,
    backendStatus,
    isOnline,
    lastSyncTime,
    
    // Chat Management
    addNewChat,
    loadChat,
    updateChat,
    deleteChat,
    setConversations,
    
    // Query Processing
    sendQueryWithChat,
    
    // Utilities
    refreshChats,
    searchChats,
    getChatStats,
    checkBackendHealth,
    
    // Direct API access (for advanced use)
    apiService: chatApiService
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
};

export default ChatContext;