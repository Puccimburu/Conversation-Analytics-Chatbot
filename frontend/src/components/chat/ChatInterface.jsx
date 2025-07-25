// File: frontend/src/components/chat/ChatInterface.jsx
// This is the main chat interface that loads specific chats or creates new ones

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChatContext } from '../../context/ChatContext';
import ResponseInterface from './ResponseInterface'; // Your existing component
import { ArrowLeft, Loader, AlertCircle, MessageCircle, Sparkles, Star } from 'lucide-react';

const ChatInterface = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const { 
    currentChat, 
    currentChatId, 
    loadChat, 
    addNewChat, 
    loading, 
    error, 
    backendStatus 
  } = useChatContext();

  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);

  // Handle loading chat or creating new one
  useEffect(() => {
    const initializeChat = async () => {
      if (chatId === 'new') {
        // Create new chat
        setIsCreatingChat(true);
        try {
          const newChatId = await addNewChat({
            title: 'New Conversation',
            category: 'conversational'
          });
          
          if (newChatId) {
            navigate(`/chat/${newChatId}`, { replace: true });
          }
        } catch (error) {
          console.error('Failed to create new chat:', error);
        } finally {
          setIsCreatingChat(false);
        }
      } else if (chatId && chatId !== currentChatId) {
        // Load existing chat
        await loadChat(chatId);
      }
    };

    initializeChat();
  }, [chatId, currentChatId, addNewChat, loadChat, navigate]);

  // Update messages when current chat changes
  useEffect(() => {
    if (currentChat && currentChat.messages) {
      setChatMessages(currentChat.messages);
    } else {
      setChatMessages([]);
    }
  }, [currentChat]);

  // Loading states
  if (isCreatingChat) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Creating new conversation...</h2>
          <p className="text-gray-600">Setting up your chat session</p>
        </div>
      </div>
    );
  }

  if (loading && !currentChat) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading conversation...</h2>
          <p className="text-gray-600">Please wait while we fetch your chat history</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !currentChat) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Unable to load chat</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex space-x-3 justify-center">
            <button
              onClick={() => navigate('/home/recent')}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <ArrowLeft className="w-4 h-4 inline mr-2" />
              Back to chats
            </button>
            <button
              onClick={() => navigate('/chat/new')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Start new chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main chat interface
  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Chat Header */}
      {currentChat && (
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/home/recent')}
                className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                title="Back to chats"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  currentChat.isLive ? 'bg-green-500 animate-pulse' : 
                  currentChat.status === 'active' ? 'bg-blue-500' : 'bg-gray-400'
                }`} />
                
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">{currentChat.title}</h1>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <span className="capitalize">{currentChat.category}</span>
                    <span>•</span>
                    <span>{currentChat.messageCount} messages</span>
                    {backendStatus === 'connected' && (
                      <>
                        <span>•</span>
                        <span className="flex items-center space-x-1">
                          <Sparkles className="w-3 h-3 text-green-500" />
                          <span>AI-powered</span>
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {currentChat.isStarred && (
                <div className="text-yellow-500">
                  <Star className="w-5 h-5 fill-current" />
                </div>
              )}
              
              <span className={`px-2 py-1 text-xs rounded-full ${
                currentChat.status === 'active' ? 'bg-green-100 text-green-700' :
                currentChat.status === 'archived' ? 'bg-gray-100 text-gray-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {currentChat.status}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Chat Content */}
      <div className="flex-1 overflow-hidden">
        <ResponseInterface 
          chatId={currentChatId}
          initialMessages={chatMessages}
          chatMode={true}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
              