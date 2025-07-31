// src/components/chat/ChatViewPage.jsx
// Simple data loader - handles both NEW and EXISTING chats
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import ResponseInterface from './ResponseInterface';
import chatAPI from '../../services/chatApi'; // ADD THIS IMPORT

const ChatViewPage = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [chatData, setChatData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isNewChat, setIsNewChat] = useState(false);
  const [initialQuery, setInitialQuery] = useState(null);

  useEffect(() => {
    const stateQuery = location.state?.query;
    const stateIsNew = location.state?.isNewChat;
    
    if (stateIsNew && stateQuery) {
      // NEW chat from MainInterface
      console.log('NEW chat detected with query:', stateQuery);
      setIsNewChat(true);
      setInitialQuery(stateQuery);
      setLoading(false);
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

      // Fetch existing chat data from backend
      const response = await fetch(`http://localhost:5000/api/chats/${chatId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Failed to load chat: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.chat) {
        console.log('Existing chat loaded successfully:', data.chat);
        setChatData(data.chat);
        setIsNewChat(false);
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

  const handleBackToRecent = () => {
    navigate('/home/recent');
  };

  const handleGoHome = () => {
    navigate('/');
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex-1 min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading conversation...</p>
          <p className="text-sm text-gray-400 mt-2">Chat ID: {chatId}</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex-1 min-h-screen bg-white flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.866-.833-2.64 0L5.232 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          
          <h3 className="text-xl font-medium text-gray-900 mb-2">Chat Not Found</h3>
          <p className="text-gray-600 mb-4">{error || 'This conversation could not be loaded.'}</p>
          
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

  // Success state - Render ResponseInterface
  console.log('Rendering ResponseInterface:', {
    chatId,
    isNewChat,
    initialQuery,
    existingMessages: chatData?.messages?.length || 0
  });

  // SIMPLIFIED: Just render ResponseInterface with appropriate props
  if (isNewChat) {
    // NEW CHAT: Pass initial query to ResponseInterface to process
    return (
      <ResponseInterface 
        query={initialQuery}
        chatId={chatId}
        onClose={handleBackToRecent}
      />
    );
  } else {
    // EXISTING CHAT: Pass conversation history to ResponseInterface
    return (
      <ResponseInterface 
        chatId={chatId}
        existingMessages={chatData?.messages || []}
        chatTitle={chatData?.title}
        onClose={handleBackToRecent}
      />
    );
  }
};

export default ChatViewPage;