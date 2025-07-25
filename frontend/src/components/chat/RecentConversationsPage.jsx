// File: frontend/src/components/chat/RecentConversationsPage.jsx
// Replace your existing RecentConversationsPage.jsx with this updated version

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useChatContext } from '../../context/ChatContext';
import { useNavigate } from 'react-router-dom';
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
  Archive,
  Wifi,
  WifiOff,
  Database,
  AlertCircle
} from 'lucide-react';

const RecentConversationsPage = () => {
  // Use context for real data
  const { 
    conversations, 
    addNewChat, 
    deleteChat,
    updateChat,
    loading,
    error,
    backendStatus,
    isOnline,
    refreshChats,
    searchChats,
    lastSyncTime
  } = useChatContext();
  
  const navigate = useNavigate();

  // UI state
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredConversations, setFilteredConversations] = useState([]);
  const [selectedChats, setSelectedChats] = useState([]);
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [hoveredChat, setHoveredChat] = useState(null);
  const [sortBy, setSortBy] = useState('recent');
  const [filterBy, setFilterBy] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [newChatNotification, setNewChatNotification] = useState(null);
  const [showingSearchResults, setShowingSearchResults] = useState(false);

  // Status indicators
  const getStatusInfo = useMemo(() => {
    if (!isOnline) {
      return { 
        icon: WifiOff, 
        text: 'Offline Mode', 
        color: 'text-red-500',
        bgColor: 'bg-red-50'
      };
    }
    
    switch (backendStatus) {
      case 'connected':
        return { 
          icon: Database, 
          text: 'Connected', 
          color: 'text-green-500',
          bgColor: 'bg-green-50'
        };
      case 'checking':
        return { 
          icon: RefreshCw, 
          text: 'Connecting...', 
          color: 'text-blue-500',
          bgColor: 'bg-blue-50'
        };
      case 'unavailable':
        return { 
          icon: AlertCircle, 
          text: 'Backend Unavailable', 
          color: 'text-orange-500',
          bgColor: 'bg-orange-50'
        };
      default:
        return { 
          icon: AlertCircle, 
          text: 'Unknown Status', 
          color: 'text-gray-500',
          bgColor: 'bg-gray-50'
        };
    }
  }, [isOnline, backendStatus]);

  // Search functionality
  const handleSearch = useCallback(async (query) => {
    setSearchQuery(query);
    
    if (!query.trim()) {
      setFilteredConversations(conversations);
      setShowingSearchResults(false);
      return;
    }

    try {
      const results = await searchChats(query);
      setFilteredConversations(results);
      setShowingSearchResults(true);
    } catch (error) {
      console.error('Search failed:', error);
      // Fallback to local filter
      const localResults = conversations.filter(conv => 
        conv.title.toLowerCase().includes(query.toLowerCase())
      );
      setFilteredConversations(localResults);
      setShowingSearchResults(true);
    }
  }, [conversations, searchChats]);

  // Apply filters and sorting
  const applyFiltersAndSort = useCallback((chats) => {
    let filtered = [...chats];

    // Apply filters
    if (filterBy !== 'all') {
      filtered = filtered.filter(conv => {
        switch (filterBy) {
          case 'starred': return conv.isStarred;
          case 'shared': return conv.isShared;
          case 'live': return conv.isLive;
          case 'unread': return conv.unreadCount > 0;
          case 'active': return conv.status === 'active';
          case 'archived': return conv.status === 'archived';
          default: return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
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

    return filtered;
  }, [filterBy, sortBy]);

  // Update filtered conversations when conversations, filters, or sort changes
  useEffect(() => {
    if (!showingSearchResults) {
      const filtered = applyFiltersAndSort(conversations);
      setFilteredConversations(filtered);
    }
  }, [conversations, applyFiltersAndSort, showingSearchResults]);

  // Handle chat navigation
  const handleChatClick = (chatId, e) => {
    // Prevent navigation if clicking on checkbox or action buttons
    if (e.target.closest('input[type="checkbox"]') || e.target.closest('button')) {
      return;
    }
    navigate(`/chat/${chatId}`);
  };

  // Handle creating new chat
  const handleCreateNewChat = async () => {
    try {
      const chatId = await addNewChat({
        title: 'New Conversation',
        category: 'conversational',
        priority: 'medium'
      });
      
      if (chatId) {
        // Show notification
        setNewChatNotification({
          title: 'New Conversation',
          category: 'conversational'
        });
        setTimeout(() => setNewChatNotification(null), 3000);
        
        // Navigate to new chat
        navigate(`/chat/${chatId}`);
      }
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  // Handle refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshChats();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Chat selection functions
  const toggleChatSelection = useCallback((chatId) => {
    setSelectedChats(prev => {
      const newSelection = prev.includes(chatId)
        ? prev.filter(id => id !== chatId)
        : [...prev, chatId];
      
      setIsSelectionMode(newSelection.length > 0);
      return newSelection;
    });
  }, []);

  const selectAllChats = () => {
    const allChatIds = filteredConversations.map(conv => conv.id);
    setSelectedChats(allChatIds);
    setIsSelectionMode(true);
  };

  const clearSelection = () => {
    setSelectedChats([]);
    setIsSelectionMode(false);
  };

  // Bulk operations
  const performBulkAction = async (action) => {
    try {
      switch (action) {
        case 'delete':
          for (const chatId of selectedChats) {
            await deleteChat(chatId);
          }
          break;
        case 'archive':
          for (const chatId of selectedChats) {
            await updateChat(chatId, { status: 'archived' });
          }
          break;
        case 'star':
          for (const chatId of selectedChats) {
            const chat = conversations.find(c => c.id === chatId);
            await updateChat(chatId, { isStarred: !chat?.isStarred });
          }
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Bulk action failed:', error);
    } finally {
      clearSelection();
    }
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
      {/* Dynamic Header */}
      <div className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-20 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          {/* Title and Status */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-semibold text-gray-900">Your chat history</h1>
              <div className={`flex items-center space-x-2 text-sm px-3 py-1 rounded-full ${getStatusInfo.bgColor}`}>
                <getStatusInfo.icon className={`w-4 h-4 ${getStatusInfo.color} ${backendStatus === 'checking' ? 'animate-spin' : ''}`} />
                <span className={getStatusInfo.color}>{getStatusInfo.text}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleRefresh}
                disabled={isRefreshing || backendStatus === 'unavailable'}
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors disabled:opacity-50"
                title="Refresh conversations"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <button 
                onClick={handleCreateNewChat}
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
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              />
              {showingSearchResults && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    handleSearch('');
                  }}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
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
              <option value="active">Active</option>
              <option value="starred">Starred</option>
              <option value="shared">Shared</option>
              <option value="live">Live</option>
              <option value="unread">Unread</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          {/* Stats and Controls */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">
                {showingSearchResults ? 
                  `${filteredConversations.length} search results` :
                  `${filteredConversations.length} conversations`
                }
                {isSelectionMode && (
                  <button 
                    onClick={selectAllChats}
                    className="text-blue-600 hover:text-blue-700 underline ml-2"
                  >
                    Select all
                  </button>
                )}
              </span>
              {lastSyncTime && (
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-500">
                    Last synced: {new Date(lastSyncTime).toLocaleTimeString()}
                  </span>
                </div>
              )}
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

      {/* Error Display */}
      {error && (
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <div>
              <p className="text-red-700 font-medium">Error</p>
              <p className="text-red-600 text-sm">{error}</p>
            </div>
            <button
              onClick={handleRefresh}
              className="ml-auto text-red-600 hover:text-red-700 text-sm underline"
            >
              Retry
            </button>
          </div>
        </div>
      )}

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
        {/* Loading State */}
        {loading && filteredConversations.length === 0 && (
          <div className="flex justify-center py-12">
            <div className="flex items-center space-x-3 text-gray-500">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
              <span>Loading conversations...</span>
            </div>
          </div>
        )}

        {/* Conversations */}
        {!loading && (
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
                  ${conversation.isOffline ? 'border-orange-200 bg-orange-50' : ''}
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
                      <span className={`px-2 py-1 text-xs rounded-full border ${
                        conversation.priority === 'urgent' ? 'text-red-600 bg-red-50' :
                        conversation.priority === 'high' ? 'text-orange-600 bg-orange-50' :
                        conversation.priority === 'medium' ? 'text-blue-600 bg-blue-50' :
                        'text-gray-600 bg-gray-50'
                      }`}>
                        {conversation.priority}
                      </span>
                      {conversation.isLive && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full border border-green-200 animate-pulse">
                          LIVE
                        </span>
                      )}
                      {conversation.isOffline && (
                        <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full border border-orange-200">
                          OFFLINE
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
                        <span>{conversation.messageCount}</span>
                      </div>
                      {conversation.participants > 1 && (
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
                      onClick={async (e) => {
                        e.stopPropagation();
                        await deleteChat(conversation.id);
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

            {/* Empty State */}
            {filteredConversations.length === 0 && !loading && (
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">
                  <MessageCircle className="w-16 h-16 mx-auto" />
                </div>
                <h3 className="text-xl font-medium text-gray-900 mb-2">
                  {showingSearchResults ? 'No matching conversations' : 
                   backendStatus === 'unavailable' ? 'Backend unavailable' :
                   'No conversations yet'}
                </h3>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  {showingSearchResults
                    ? 'Try adjusting your search criteria.'
                    : backendStatus === 'unavailable'
                    ? 'Check your connection and try refreshing.'
                    : 'Start a new conversation to see it appear here with real-time updates.'
                  }
                </p>
                <button 
                  onClick={handleCreateNewChat}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  Start your first chat
                </button>
              </div>
            )}
          </div>
        )}
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