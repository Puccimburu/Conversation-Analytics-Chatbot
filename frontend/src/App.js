// File: frontend/src/App.jsx
// Replace or update your existing App.jsx with proper routing

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChatProvider } from './context/ChatContext';
import Sidebar from './components/layout/Sidebar'; // Your existing sidebar
import RecentConversationsPage from './components/chat/RecentConversationsPage';
import ChatInterface from './components/chat/ChatInterface'; // We'll create this
import ResponseInterface from './components/chat/ResponseInterface'; // Your existing component

function App() {
  return (
    <ChatProvider>
      <Router>
        <div className="flex h-screen bg-gray-50">
          {/* Sidebar - Your existing beautiful sidebar */}
          <Sidebar />
          
          {/* Main Content Area */}
          <div className="flex-1 flex flex-col overflow-hidden ml-14"> {/* ml-14 accounts for sidebar width */}
            <Routes>
              {/* Home route - shows recent conversations */}
              <Route path="/" element={<Navigate to="/home/recent" replace />} />
              
              {/* Home routes */}
              <Route path="/home" element={<Navigate to="/home/recent" replace />} />
              <Route path="/home/recent" element={<RecentConversationsPage />} />
              <Route path="/home/favorites" element={<RecentConversationsPage />} />
              <Route path="/home/shared" element={<RecentConversationsPage />} />
              
              {/* Chat routes */}
              <Route path="/chat/new" element={<ChatInterface />} />
              <Route path="/chat/:chatId" element={<ChatInterface />} />
              
              {/* Legacy route for your existing interface */}
              <Route path="/analytics" element={<ResponseInterface />} />
              
              {/* Discover routes (placeholder) */}
              <Route path="/discover/*" element={<div className="p-6"><h1>Discover - Coming Soon</h1></div>} />
              
              {/* Spaces routes (placeholder) */}
              <Route path="/spaces/*" element={<div className="p-6"><h1>Spaces - Coming Soon</h1></div>} />
              
              {/* Account routes (placeholder) */}
              <Route path="/account" element={<div className="p-6"><h1>Account Settings - Coming Soon</h1></div>} />
              
              {/* Catch all - redirect to home */}
              <Route path="*" element={<Navigate to="/home/recent" replace />} />
            </Routes>
          </div>
        </div>
      </Router>
    </ChatProvider>
  );
}

export default App;