// Complete Fixed ChatViewPage.jsx with Query Input
// File: frontend/src/components/chat/ChatViewPage.jsx

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import ResponseInterface from './ResponseInterface';
import chatAPI from '../../services/chatApi';

// Custom Send Icon Component
const SendIcon = ({ className }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const ChatViewPage = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [chatData, setChatData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isNewChat, setIsNewChat] = useState(false);
  const [initialQuery, setInitialQuery] = useState(null);
  
  // New state for query input
  const [currentQuery, setCurrentQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [responses, setResponses] = useState([]);
  
  const inputRef = useRef(null);

  useEffect(() => {
    const stateQuery = location.state?.query;
    const stateIsNew = location.state?.isNewChat;
    
    if (stateIsNew && stateQuery) {
      // NEW chat from MainInterface
      console.log('NEW chat detected with query:', stateQuery);
      setIsNewChat(true);
      setInitialQuery(stateQuery);
      setCurrentQuery(''); // Clear input for new queries
      setLoading(false);
      
      // Auto-submit the initial query
      setTimeout(() => {
        submitQuery(stateQuery);
      }, 100);
    } else {
      // EXISTING chat or page reload
      console.log('EXISTING chat or reload detected, loading from backend');
      loadExistingChat();
    }
  }, [chatId, location.state]);

  const loadExistingChat = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Loading existing chat data for chatId:', chatId);

      const response = await fetch(`http://localhost:5000/api/chats/${chatId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Failed to load chat: ${response.status}`);
      }

      const data = await response.json();
      
      if (data && data.chat) {
        console.log('Existing chat loaded successfully:', data.chat);
        setChatData(data.chat);
        setIsNewChat(false);
        
        // Convert existing messages to responses format
        if (data.chat.messages && data.chat.messages.length > 0) {
          const formattedResponses = convertMessagesToResponses(data.chat.messages);
          setResponses(formattedResponses);
        }
      } else {
        throw new Error('Chat not found');
      }

    } catch (err) {
      console.error('Error loading chat:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const convertMessagesToResponses = (messages) => {
    const responses = [];
    let currentResponse = null;

    messages.forEach(msg => {
      if (msg.role === 'user') {
        // Start new response
        if (currentResponse) {
          responses.push(currentResponse);
        }
        currentResponse = {
          id: `response_${Date.now()}_${Math.random()}`,
          query: msg.content,
          timestamp: new Date(msg.timestamp).getTime(),
          content: '',
          chart_data: null,
          insights: [],
          recommendations: []
        };
      } else if (msg.role === 'assistant' && currentResponse) {
        // Complete current response
        currentResponse.content = msg.content;
        currentResponse.chart_data = msg.chart_data;
        currentResponse.insights = msg.insights || [];
        currentResponse.recommendations = msg.recommendations || [];
      }
    });

    // Add final response
    if (currentResponse) {
      responses.push(currentResponse);
    }

    return responses;
  };

  const submitQuery = async (queryText = currentQuery) => {
    if (!queryText.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setCurrentQuery(''); // Clear input immediately

    // Add user query to responses immediately
    const userResponse = {
      id: `response_${Date.now()}`,
      query: queryText,
      timestamp: Date.now(),
      content: 'Processing your request...',
      chart_data: null,
      insights: [],
      recommendations: [],
      isLoading: true
    };

    setResponses(prev => [...prev, userResponse]);

    try {
      console.log('🔍 Submitting query to backend:', queryText);
      
      const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: queryText,
          chat_id: chatId 
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Backend response received:', data);
        
        // Update the response with backend data
        setResponses(prev => prev.map(r => 
          r.id === userResponse.id ? {
            ...r,
            content: data.summary || data.visualization?.summary || 'Analysis completed',
            chart_data: data.visualization?.chart_config || data.chart_data,
            insights: data.insights || [],
            recommendations: data.recommendations || [],
            isLoading: false,
            success: data.success
          } : r
        ));
      } else {
        throw new Error(`Backend error: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ Query submission error:', error);
      
      // Update response with error
      setResponses(prev => prev.map(r => 
        r.id === userResponse.id ? {
          ...r,
          content: `Error: ${error.message}. Please try again.`,
          isLoading: false,
          success: false,
          error: error.message
        } : r
      ));
    } finally {
      setIsSubmitting(false);
      
      // Focus back to input
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuery();
    }
  };

  const handleBackToRecent = () => {
    navigate('/home/recent');
  };

  const handleGoHome = () => {
    navigate('/');
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chat...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Chat Not Available</h2>
          <p className="text-gray-600 mb-6">Error: {error}</p>
          
          <div className="text-xs text-gray-400 mb-6 bg-gray-50 p-3 rounded border">
            <p>Chat ID: {chatId}</p>
          </div>

          <div className="flex flex-col space-y-3">
            <button 
              onClick={loadExistingChat}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry Loading
            </button>
            
            <button 
              onClick={handleBackToRecent}
              className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              Back to Recent Chats
            </button>
            
            <button 
              onClick={handleGoHome}
              className="border border-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Start New Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main chat interface
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={handleBackToRecent}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {chatData?.title || (isNewChat ? 'New Chat' : `Chat ${chatId.slice(-8)}`)}
              </h1>
              <p className="text-sm text-gray-500">
                {isNewChat ? 'Starting new conversation' : `Chat ID: ${chatId}`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {responses.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-4xl mb-2">💬</div>
              <p className="font-medium text-gray-600">No messages yet</p>
              <p className="text-sm text-gray-500 mt-2">Type a question below to get started!</p>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <ResponseInterface 
              responses={responses}
              onEditQuery={(responseId, newQuery) => {
                // Handle query editing if needed
                console.log('Edit query:', responseId, newQuery);
              }}
              isLoading={false}
            />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <div className="relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about your data, request charts, or analyze trends..."
                  disabled={isSubmitting}
                  className={`
                    w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg 
                    focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                    resize-none placeholder-gray-500
                    ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                />
                <button
                  onClick={() => submitQuery()}
                  disabled={!currentQuery.trim() || isSubmitting}
                  className={`
                    absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-lg 
                    transition-all duration-200
                    ${currentQuery.trim() && !isSubmitting
                      ? 'bg-blue-600 text-white hover:bg-blue-700' 
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }
                  `}
                >
                  {isSubmitting ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <SendIcon className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Status indicator */}
          {isSubmitting && (
            <div className="mt-2 text-sm text-blue-600 flex items-center space-x-2">
              <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <span>Processing your request...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatViewPage;