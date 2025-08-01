// src/components/chat/MainChatInterface.jsx
import React, { useState, useEffect } from 'react';
import { useChatContext } from '../../context/ChatContext'; 
import { useNavigate } from 'react-router-dom';
import chatAPI from '../../services/chatApi'; // 🎯 NEW: Import chat API
import { 
  Search, 
  Image, 
  MapPin, 
  Paperclip, 
  Mic, 
  Send,
  Brain,
  Wrench,
  Heart,
  GraduationCap,
  CheckCircle,
  BarChart3,
  PieChart,
  TrendingUp,
  DollarSign
} from 'lucide-react';

const MainChatInterface = () => {
  const { addNewChat } = useChatContext();
  const navigate = useNavigate(); 
  const [query, setQuery] = useState('');
  const [isActive, setIsActive] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [isCreatingChat, setIsCreatingChat] = useState(false); // 🎯 NEW: Track chat creation

  // Check backend health on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/health');
      const health = await response.json();
      setBackendHealth(health);
    } catch (error) {
      console.log('Backend not available, will use mock data');
      setBackendHealth({ status: 'unavailable' });
    }
  };

  // Enhanced suggested actions with data analytics focus
  const suggestedActions = [
    { 
      icon: BarChart3, 
      label: 'Sales Analysis', 
      color: 'bg-blue-50 text-blue-700 border-blue-200',
      example: 'Show me top 5 selling products'
    },
    { 
      icon: PieChart, 
      label: 'Revenue Breakdown', 
      color: 'bg-green-50 text-green-700 border-green-200',
      example: 'Revenue by category pie chart'
    },
    { 
      icon: TrendingUp, 
      label: 'Market Trends', 
      color: 'bg-purple-50 text-purple-700 border-purple-200',
      example: 'Monthly sales trends line chart'
    },
    { 
      icon: DollarSign, 
      label: 'Financial Data', 
      color: 'bg-orange-50 text-orange-700 border-orange-200',
      example: 'Smartphone vs laptop sales comparison'
    },
    { 
      icon: CheckCircle, 
      label: 'Data Insights', 
      color: 'bg-teal-50 text-teal-700 border-teal-200',
      example: 'Customer distribution by segment'
    }
  ];

  // 🎯 UPDATED: Enhanced handleSubmit with chat creation and navigation
  const handleSubmit = async () => {
    if (query.trim() && !isCreatingChat) {
      setIsCreatingChat(true);
      
      try {
        // 🎯 NEW: Create chat session in backend first
        const response = await chatAPI.createChat({
          title: query.length > 50 ? query.substring(0, 50) + '...' : query,
          category: determineCategory(query),
          priority: 'medium',
          first_message: query.trim()
        });

        if (response.success && response.chat_id) {
          console.log('✅ Chat created successfully:', response.chat_id);
          
          // 🎯 NEW: Add to local context for immediate UI update
          addNewChat({
            id: response.chat_id,
            title: query.length > 50 ? query.substring(0, 50) + '...' : query,
            category: determineCategory(query),
            priority: 'medium',
            lastMessage: 'just now',
            messageCount: 1,
            unreadCount: 0,
            lastActivity: Date.now(),
            status: 'active',
            isLive: true,
            participants: 1
          });

          // 🎯 NEW: Navigate to individual chat page with query
          navigate(`/chat/${response.chat_id}`, { 
            state: { 
              query: query.trim(),
              isNewChat: true 
            } 
          });
          
        } else {
          throw new Error('Failed to create chat session');
        }
        
      } catch (error) {
        console.error('Error creating chat:', error);
        
        // 🎯 FALLBACK: Create local chat if backend fails
        const fallbackChatId = `chat_${Date.now()}`;
        addNewChat({
          id: fallbackChatId,
          title: query.length > 50 ? query.substring(0, 50) + '...' : query,
          category: determineCategory(query),
          priority: 'medium',
          lastMessage: 'just now',
          messageCount: 1,
          unreadCount: 0,
          lastActivity: Date.now(),
          status: 'active',
          isLive: true,
          participants: 1
        });

        // Navigate to fallback chat
        navigate(`/chat/${fallbackChatId}`, { 
          state: { 
            query: query.trim(),
            isNewChat: true 
          } 
        });
      } finally {
        setIsCreatingChat(false);
      }
    }
  };

  // Determine category based on query content
  const determineCategory = (queryText) => {
    const lowerQuery = queryText.toLowerCase();
    
    if (lowerQuery.includes('chart') || lowerQuery.includes('plot') || 
        lowerQuery.includes('sales') || lowerQuery.includes('revenue') ||
        lowerQuery.includes('data') || lowerQuery.includes('analysis')) {
      return 'analysis';
    }
    
    if (lowerQuery.includes('technical') || lowerQuery.includes('implementation') ||
        lowerQuery.includes('code') || lowerQuery.includes('system')) {
      return 'technical';
    }
    
    if (lowerQuery.includes('trading') || lowerQuery.includes('market') ||
        lowerQuery.includes('algorithm') || lowerQuery.includes('JTMD')) {
      return 'JTMD';
    }
    
    return 'conversational';
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSuggestedActionClick = (action) => {
    setQuery(action.example);
    setIsActive(true);
  };

  // Quick examples for different chart types
  const quickExamples = [
    {
      icon: BarChart3,
      title: 'Bar Charts',
      color: 'text-blue-500',
      examples: [
        'Top 5 selling products',
        'Sales by region',
        'Customer count by segment'
      ]
    },
    {
      icon: PieChart,
      title: 'Pie Charts',
      color: 'text-green-500',
      examples: [
        'Revenue by category',
        'Customer distribution',
        'Product categories breakdown'
      ]
    },
    {
      icon: TrendingUp,
      title: 'Line Charts',
      color: 'text-purple-500',
      examples: [
        'Monthly sales trends',
        'Revenue over time',
        'Customer growth trends'
      ]
    }
  ];

  // Main search interface with original UI design
  return (
    <div className="flex-1 min-h-screen bg-white flex items-center justify-center p-8">
      <div className="w-full max-w-4xl">
        {/* Backend Status Indicator */}
        {backendHealth && (
          <div className="mb-4 text-center">
            <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs ${
              backendHealth.status === 'healthy' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-yellow-100 text-yellow-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                backendHealth.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
              }`}></div>
              <span>
                {backendHealth.status === 'healthy' 
                  ? 'Connected to Analytics Backend' 
                  : 'Demo Mode - Backend Unavailable'
                }
              </span>
            </div>
          </div>
        )}

        {/* Main Logo/Title */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-normal text-gray-900 mb-3">
            Convo Analytics
          </h1>
          <p className="text-gray-500 text-lg">
            Ask questions about your data and get instant visualizations
          </p>
        </div>

        {/* Loading State */}
        {isCreatingChat && (
          <div className="text-center mb-8">
            <div className="flex items-center justify-center space-x-3 text-gray-600">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
              <span>Creating your conversation...</span>
            </div>
          </div>
        )}

        {/* Main Search Input */}
        <div className="mb-8">
          <div className="relative">
            {/* Input Field */}
            <div className={`
              relative rounded-xl border transition-all duration-200 bg-white
              ${isActive || query ? 'border-gray-300 shadow-lg' : 'border-gray-200 shadow-sm'}
            `}>
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setIsActive(true);
                }}
                onFocus={() => setIsActive(true)}
                onBlur={() => setTimeout(() => setIsActive(false), 100)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your sales data, request charts, or analyze trends..."
                disabled={isCreatingChat}
                className={`
                  w-full px-4 py-4 text-gray-900 placeholder-gray-500 bg-transparent border-0 rounded-xl focus:outline-none focus:ring-0 pr-16
                  ${isCreatingChat ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              />
              
              {/* Send Button */}
              <button
                onClick={handleSubmit}
                disabled={!query.trim() || isCreatingChat}
                className={`
                  absolute right-3 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-all duration-200
                  ${query.trim() && !isCreatingChat
                    ? 'bg-teal-600 text-white hover:bg-teal-700 shadow-sm' 
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {isCreatingChat ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>

            {/* Bottom Toolbar */}
            <div className="flex items-center justify-between mt-3 px-2">
              {/* Left Side Icons */}
              <div className="flex items-center space-x-2">
                <button 
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  title="Search"
                  disabled={isCreatingChat}
                >
                  <Search className="w-4 h-4" />
                </button>
                <button 
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  title="Attach Image"
                  disabled={isCreatingChat}
                >
                  <Image className="w-4 h-4" />
                </button>
                <button 
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  title="Location"
                  disabled={isCreatingChat}
                >
                  <MapPin className="w-4 h-4" />
                </button>
              </div>

              {/* Right Side Icons */}
              <div className="flex items-center space-x-2">
                <button 
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  title="Attach File"
                  disabled={isCreatingChat}
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <button 
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  title="Voice Input"
                  disabled={isCreatingChat}
                >
                  <Mic className="w-4 h-4" />
                </button>
                {/* Audio Visualizer */}
                <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center space-x-1">
                  <div className="w-1 h-2 bg-white rounded-full animate-pulse"></div>
                  <div className="w-1 h-3 bg-white rounded-full animate-pulse" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-1 h-4 bg-white rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-1 h-2 bg-white rounded-full animate-pulse" style={{animationDelay: '0.3s'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Suggested Actions */}
        <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
          {suggestedActions.map((action, index) => {
            const IconComponent = action.icon;
            return (
              <button
                key={index}
                onClick={() => handleSuggestedActionClick(action)}
                disabled={isCreatingChat}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-full border transition-all duration-200 hover:shadow-sm
                  ${action.color} ${isCreatingChat ? 'opacity-50 cursor-not-allowed' : ''}
                `}
                title={action.example}
              >
                <IconComponent className="w-4 h-4" />
                <span className="text-sm font-medium">{action.label}</span>
              </button>
            );
          })}
        </div>

        {/* Quick Examples Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {quickExamples.map((example, index) => {
            const IconComponent = example.icon;
            return (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <IconComponent className={`h-5 w-5 ${example.color}`} />
                  <span className="text-sm font-medium text-gray-900">{example.title}</span>
                </div>
                <div className="space-y-2">
                  {example.examples.map((exampleText, exampleIndex) => (
                    <button
                      key={exampleIndex}
                      onClick={() => setQuery(exampleText)}
                      disabled={isCreatingChat}
                      className={`
                        block w-full text-left text-xs text-gray-600 p-2 rounded transition-colors
                        ${isCreatingChat 
                          ? 'opacity-50 cursor-not-allowed'
                          : 'hover:text-gray-900 hover:bg-white'
                        }
                      `}
                    >
                      "{exampleText}"
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Features Section */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-8 text-xs text-gray-500">
            <div className="flex items-center space-x-1">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>Multi-chart support</span>
            </div>
            <div className="flex items-center space-x-1">
              <BarChart3 className="h-3 w-3 text-blue-500" />
              <span>Automatic chart selection</span>
            </div>
            <div className="flex items-center space-x-1">
              <Brain className="h-3 w-3 text-purple-500" />
              <span>AI-powered insights</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="h-3 w-3 text-yellow-500" />
              <span>Answer validation</span>
            </div>
          </div>
        </div>

        {/* Footer Text */}
        <div className="text-center text-xs text-gray-400">
          <p>Conversational AI can make mistakes. Please verify important information.</p>
          <p className="mt-1">
            {backendHealth?.status === 'healthy' 
              ? 'Connected to your MongoDB analytics database'
              : 'Demo mode with sample data - start your backend to connect'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default MainChatInterface;