import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useChatContext } from '../../context/ChatContext';
import { useNavigate } from 'react-router-dom';
import chatAPI from '../../services/chatApi';
import { 
  Search, 
  Plus, 
  Home, 
  Star, 
  Users, 
  Trash2, 
  MoreHorizontal,
  Check,
  X,
  Clock,
  MessageCircle,
  RefreshCw,
  Zap,
  Archive
} from 'lucide-react';

const RecentConversationsPage = () => {
  // Use context for chat management
  const { 
    conversations, 
    setConversations
  } = useChatContext();
  
  const navigate = useNavigate();

  // UI states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChats, setSelectedChats] = useState([]);
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [hoveredChat, setHoveredChat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState('recent');
  const [filterBy, setFilterBy] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [newChatNotification, setNewChatNotification] = useState(null);
  const [isLoadingReal, setIsLoadingReal] = useState(false);
  const [apiError, setApiError] = useState(null);
  const lastUpdate = useRef(Date.now());

  const priorityColors = {
    urgent: 'text-red-600 bg-red-50',
    high: 'text-orange-600 bg-orange-50',
    medium: 'text-blue-600 bg-blue-50',
    low: 'text-gray-600 bg-gray-50'
  };

  // Load real chat data from backend
  const loadRealChats = useCallback(async (refresh = false) => {
    try {
      setIsLoadingReal(true);
      setApiError(null);
      
      const response = await chatAPI.getAllChats({
        limit: 50,
        status: filterBy === 'all' ? null : filterBy
      });
      
      if (response.success && response.chats) {
        const transformedChats = response.chats.map(chat => 
          chatAPI.transformChatForFrontend(chat)
        );
        
        setConversations(transformedChats);
        
        if (refresh) {
          setNewChatNotification({
            title: `Loaded ${transformedChats.length} conversations`,
            category: 'success'
          });
          setTimeout(() => setNewChatNotification(null), 3000);
        }
      }
    } catch (error) {
      console.error('Failed to load real chats:', error);
      setApiError(error.message);
    } finally {
      setIsLoadingReal(false);
    }
  }, [filterBy, setConversations]);

  // Create real chat function
  const createRealChat = useCallback(async (chatData) => {
    try {
      const response = await chatAPI.createChat(chatData);
      
      if (response.success && response.chat) {
        const transformedChat = chatAPI.transformChatForFrontend(response.chat);
        setConversations(prev => [transformedChat, ...prev]);
        
        setNewChatNotification({
          title: response.chat.title,
          category: response.chat.category
        });
        setTimeout(() => setNewChatNotification(null), 4000);
        
        return response.chat_id;
      }
    } catch (error) {
      console.error('Failed to create real chat:', error);
      setApiError('Failed to create chat: ' + error.message);
    }
  }, [setConversations]);

  // Delete real chat function
  const deleteRealChat = useCallback(async (chatId) => {
    try {
      const chat = conversations.find(c => c.id === chatId);
      if (chat && chat._backendData) {
        await chatAPI.deleteChat(chat._backendData.chat_id);
      }
      
      setConversations(prev => prev.filter(c => c.id !== chatId));
      
    } catch (error) {
      console.error('Failed to delete chat:', error);
      setConversations(prev => prev.filter(c => c.id !== chatId));
    }
  }, [conversations, setConversations]);

  // Handle chat navigation
  const handleChatClick = (chatId, e) => {
    if (e.target.closest('input[type="checkbox"]') || e.target.closest('button')) {
      return;
    }
    navigate(`/chat/${chatId}`);
  };

  // Initialize with real data
  useEffect(() => {
    loadRealChats();
  }, [loadRealChats]);

  // Update last activity timestamp
  useEffect(() => {
    const interval = setInterval(() => {
      lastUpdate.current = Date.now();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Dynamic filtering and sorting
  const getFilteredAndSortedConversations = useCallback(() => {
    let filtered = conversations.filter(conv => {
      const matchesSearch = conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           conv.category.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesFilter = filterBy === 'all' || 
                           (filterBy === 'starred' && conv.isStarred) ||
                           (filterBy === 'shared' && conv.isShared) ||
                           (filterBy === 'live' && conv.isLive) ||
                           (filterBy === 'unread' && conv.unreadCount > 0);
      
      return matchesSearch && matchesFilter;
    });

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return b.lastActivity - a.lastActivity;
        case 'alphabetical':
          return a.title.localeCompare(b.title);
        case 'priority':
          const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        case 'messages':
          return b.messageCount - a.messageCount;
        default:
          return b.timestamp - a.timestamp;
      }
    });
  }, [conversations, searchQuery, filterBy, sortBy]);

  const filteredConversations = getFilteredAndSortedConversations();

  // Chat selection
  const toggleChatSelection = useCallback((chatId) => {
    setSelectedChats(prev => {
      const newSelection = prev.includes(chatId)
        ? prev.filter(id => id !== chatId)
        : [...prev, chatId];
      
      setIsSelectionMode(newSelection.length > 0);
      return newSelection;
    });
  }, []);

  // Bulk operations
  const selectAllChats = () => {
    const allChatIds = filteredConversations.map(conv => conv.id);
    setSelectedChats(allChatIds);
    setIsSelectionMode(true);
  };

  const clearSelection = () => {
    setSelectedChats([]);
    setIsSelectionMode(false);
  };

  const performBulkAction = (action) => {
    switch (action) {
      case 'delete':
        selectedChats.forEach(chatId => deleteRealChat(chatId));
        break;
      case 'archive':
        setConversations(prev => prev.map(conv => 
          selectedChats.includes(conv.id) ? { ...conv, status: 'archived' } : conv
        ));
        break;
      case 'star':
        setConversations(prev => prev.map(conv => 
          selectedChats.includes(conv.id) ? { ...conv, isStarred: !conv.isStarred } : conv
        ));
        break;
      default:
        break;
    }
    clearSelection();
  };

  // Refresh functionality
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadRealChats(true);
    setIsRefreshing(false);
  };

  // Get category styling
  const getCategoryStyle = (category) => {
    const styles = {
      'analysis': 'text-blue-600 bg-blue-50 border-blue-200',
      'technical': 'text-purple-600 bg-purple-50 border-purple-200',
      'conversational': 'text-green-600 bg-green-50 border-green-200',
      'JTMD': 'text-orange-600 bg-orange-50 border-orange-200',
      'CVs AND improvement': 'text-indigo-600 bg-indigo-50 border-indigo-200',
      'documentation': 'text-teal-600 bg-teal-50 border-teal-200',
      'React project': 'text-pink-600 bg-pink-50 border-pink-200'
    };
    return styles[category] || 'text-gray-600 bg-gray-50 border-gray-200';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-20 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          {/* Title and New Chat */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-semibold text-gray-900">Your chat history</h1>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className={`w-2 h-2 rounded-full animate-pulse ${apiError ? 'bg-red-500' : 'bg-green-500'}`}></div>
                <span>{apiError ? 'API Error' : 'Live updates enabled'}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleRefresh}
                disabled={isRefreshing || isLoadingReal}
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                title="Refresh conversations"
              >
                <RefreshCw className={`w-4 h-4 ${(isRefreshing || isLoadingReal) ? 'animate-spin' : ''}`} />
              </button>
              <button 
                onClick={() => navigate('/new')}
                className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-all duration-200 flex items-center space-x-2 shadow-sm hover:shadow-md"
              >
                <Plus className="w-4 h-4" />
                <span>New chat</span>
              </button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex items-center space-x-4 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search conversations, categories, or keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              />
            </div>
            
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="recent">Recent</option>
              <option value="alphabetical">A-Z</option>
              <option value="priority">Priority</option>
              <option value="messages">Messages</option>
            </select>

            <select 
              value={filterBy} 
              onChange={(e) => setFilterBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="starred">Starred</option>
              <option value="shared">Shared</option>
              <option value="live">Live</option>
              <option value="unread">Unread</option>
            </select>
          </div>

          {/* Stats and Controls */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">
                {filteredConversations.length} conversations
                {isSelectionMode && (
                  <button 
                    onClick={selectAllChats}
                    className="text-blue-600 hover:text-blue-700 underline ml-2"
                  >
                    Select all
                  </button>
                )}
              </span>
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-gray-500">Last updated: {new Date(lastUpdate.current).toLocaleTimeString()}</span>
              </div>
            </div>
            
            {isSelectionMode && (
              <div className="flex items-center space-x-3">
                <span className="text-blue-600 flex items-center space-x-1">
                  <Check className="w-4 h-4" />
                  <span>{selectedChats.length} selected</span>
                </span>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => performBulkAction('star')}
                    className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors"
                  >
                    <Star className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => performBulkAction('archive')}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    <Archive className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => performBulkAction('delete')}
                    className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
                <button
                  onClick={clearSelection}
                  className="text-gray-500 hover:text-gray-700 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Chat Notification */}
      {newChatNotification && (
        <div className="fixed top-20 right-6 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-30 animate-slide-in">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>New conversation: {newChatNotification.title}</span>
          </div>
        </div>
      )}

      {/* Conversations List */}
      <div className="max-w-6xl mx-auto px-6 py-6">
        <div className="space-y-2">
          {filteredConversations.map((conversation, index) => (
            <div
              key={conversation.id}
              onClick={(e) => handleChatClick(conversation.id, e)}
              className={`
                group relative border rounded-lg transition-all duration-300 cursor-pointer transform hover:scale-[1.01]
                ${selectedChats.includes(conversation.id)
                  ? 'bg-blue-50 border-blue-200 shadow-md scale-[1.01]'
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-md bg-white hover:bg-gray-50'
                }
                ${conversation.isLive ? 'ring-2 ring-green-200 ring-opacity-50' : ''}
              `}
              onMouseEnter={() => setHoveredChat(conversation.id)}
              onMouseLeave={() => setHoveredChat(null)}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="p-4 flex items-center space-x-4">
                {/* Checkbox */}
                <div className={`
                  transition-all duration-200
                  ${hoveredChat === conversation.id || selectedChats.includes(conversation.id)
                    ? 'opacity-100 scale-100' 
                    : 'opacity-0 scale-75'
                  }
                `}>
                  <input
                    type="checkbox"
                    checked={selectedChats.includes(conversation.id)}
                    onChange={() => toggleChatSelection(conversation.id)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 transition-all duration-200"
                  />
                </div>

                {/* Status Indicator */}
                <div className="flex flex-col items-center space-y-1">
                  <div className={`w-3 h-3 rounded-full ${
                    conversation.isLive ? 'bg-green-500 animate-pulse' : 
                    conversation.status === 'active' ? 'bg-blue-500' :
                    conversation.status === 'archived' ? 'bg-gray-400' : 'bg-yellow-500'
                  }`} />
                  {conversation.isTyping && (
                    <div className="flex space-x-1">
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  )}
                </div>

                {/* Chat Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-medium text-gray-900 truncate">
                      {conversation.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full border ${priorityColors[conversation.priority] || priorityColors.medium}`}>
                      {conversation.priority}
                    </span>
                    {conversation.isLive && (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full border border-green-200 animate-pulse">
                        LIVE
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>{conversation.lastMessage}</span>
                    <span className={`px-2 py-1 rounded-full border text-xs ${getCategoryStyle(conversation.category)}`}>
                      {conversation.category}
                    </span>
                    <div className="flex items-center space-x-1">
                      <MessageCircle className="w-3 h-3" />
                      <span>{conversation.messageCount || 0}</span>
                    </div>
                    {(conversation.participants || 1) > 1 && (
                      <div className="flex items-center space-x-1">
                        <Users className="w-3 h-3" />
                        <span>{conversation.participants}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Unread Badge */}
                {conversation.unreadCount > 0 && (
                  <div className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
                    {conversation.unreadCount}
                  </div>
                )}

                {/* Action Icons */}
                <div className={`
                  flex items-center space-x-2 transition-all duration-200
                  ${hoveredChat === conversation.id ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'}
                `}>
                  {conversation.isStarred && (
                    <Star className="w-4 h-4 text-yellow-500 fill-current" />
                  )}
                  {conversation.isShared && (
                    <Users className="w-4 h-4 text-blue-500" />
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteRealChat(conversation.id);
                    }}
                    className="p-1 text-gray-400 hover:text-red-500 transition-all duration-200 hover:scale-110"
                    title="Delete chat"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <button className="p-1 text-gray-400 hover:text-gray-600 transition-all duration-200 hover:scale-110">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {(loading || isLoadingReal) && (
            <div className="flex justify-center py-8">
              <div className="flex items-center space-x-3 text-gray-500">
                <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
                <span>{isLoadingReal ? 'Loading conversations...' : 'Loading more conversations...'}</span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {filteredConversations.length === 0 && !loading && !isLoadingReal && !apiError && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <MessageCircle className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                {searchQuery || filterBy !== 'all' ? 'No matching conversations' : 'No conversations yet'}
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                {searchQuery || filterBy !== 'all'
                  ? 'Try adjusting your search or filter criteria.'
                  : 'Start a new conversation to see it appear here with real-time updates.'
                }
              </p>
              <button 
                onClick={() => navigate('/new')}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Start your first chat
              </button>
            </div>
          )}

          {/* API Error State */}
          {apiError && filteredConversations.length === 0 && !isLoadingReal && (
            <div className="text-center py-12">
              <div className="text-red-400 mb-4">
                <X className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                Backend Connection Issue
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Unable to connect to the backend server. Please check your backend connection.
              </p>
              <div className="flex justify-center space-x-4">
                <button 
                  onClick={() => loadRealChats(true)}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  Retry Connection
                </button>
                <button 
                  onClick={() => navigate('/new')}
                  className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  Start New Chat
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-4">
                Error: {apiError}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Custom Styles */}
      <style jsx>{`
        @keyframes slide-in {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default RecentConversationsPage;