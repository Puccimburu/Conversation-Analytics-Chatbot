// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { ChatProvider } from './context/ChatContext';
import Sidebar from './components/layout/Sidebar';
import MainChatInterface from './components/chat/MainChatInterface';
import RecentConversationsPage from './components/chat/RecentConversationsPage';
import './index.css';

// Enhanced page components with better styling
const HomePage = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-gray-900 mb-4">Analytics Dashboard</h1>
    <p className="text-gray-600 mb-8">Welcome to your conversational analytics platform</p>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Recent Conversations</h3>
        </div>
        <p className="text-gray-600 text-sm mb-4">View and manage your chat history with data analytics</p>
        <button 
          onClick={() => window.location.href = '/home/recent'}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors w-full"
        >
          View History
        </button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Favorites</h3>
        </div>
        <p className="text-gray-600 text-sm mb-4">Your starred conversations and top insights</p>
        <button 
          onClick={() => window.location.href = '/home/favorites'}
          className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors w-full"
        >
          View Favorites
        </button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Analytics</h3>
        </div>
        <p className="text-gray-600 text-sm mb-4">Create new data visualizations and insights</p>
        <button 
          onClick={() => window.location.href = '/new'}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors w-full"
        >
          Start Analyzing
        </button>
      </div>
    </div>

    {/* Recent Activity Section */}
    <div className="mt-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500 py-8">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-lg font-medium">No recent activity</p>
          <p className="text-sm mt-1">Start asking questions about your data to see activity here</p>
        </div>
      </div>
    </div>
  </div>
);

const FavoritesPage = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-gray-900 mb-4">Favorites</h1>
    <p className="text-gray-600 mb-6">Your starred conversations and insights</p>
    <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
      <div className="text-gray-400 mb-4">
        <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No favorites yet</h3>
      <p className="text-gray-500 mb-4">Star conversations to save them here</p>
      <button 
        onClick={() => window.location.href = '/new'}
        className="bg-yellow-600 text-white px-6 py-3 rounded-lg hover:bg-yellow-700 transition-colors"
      >
        Start a Conversation
      </button>
    </div>
  </div>
);

const SharedPage = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-gray-900 mb-4">Shared</h1>
    <p className="text-gray-600 mb-6">Conversations shared with you and by you</p>
    <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
      <div className="text-gray-400 mb-4">
        <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No shared conversations</h3>
      <p className="text-gray-500 mb-4">Share insights and analyses with your team</p>
      <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
        Share Analysis
      </button>
    </div>
  </div>
);

const DiscoverPage = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-gray-900 mb-4">Discover</h1>
    <p className="text-gray-600 mb-6">Explore analytics and insights</p>
    
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[
        { title: 'For You', description: 'Personalized analytics insights', category: 'for-you' },
        { title: 'Tech', description: 'Technology and product analytics', category: 'tech' },
        { title: 'Business', description: 'Business intelligence and metrics', category: 'business' },
        { title: 'Finance', description: 'Financial data and trends', category: 'finance' },
        { title: 'Sales', description: 'Sales performance and forecasting', category: 'sales' },
        { title: 'Marketing', description: 'Marketing analytics and ROI', category: 'marketing' }
      ].map((item) => (
        <div key={item.category} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
          <p className="text-gray-600 text-sm">{item.description}</p>
        </div>
      ))}
    </div>
  </div>
);

const SpacesPage = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-gray-900 mb-4">Spaces</h1>
    <p className="text-gray-600 mb-6">Organize your analytics projects</p>
    <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
      <div className="text-gray-400 mb-4">
        <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No spaces yet</h3>
      <p className="text-gray-500 mb-4">Create spaces to organize your analytics projects</p>
      <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
        Create Space
      </button>
    </div>
  </div>
);

// Main interface for new conversations
const NewThreadPage = () => <MainChatInterface />;

// Dynamic page component that shows the current route
const DynamicPage = () => {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const pageName = pathSegments[pathSegments.length - 1] || 'home';
  
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-4 capitalize">
        {pageName.replace('-', ' ')}
      </h1>
      <p className="text-gray-600 mb-4">
        Current path: <code className="bg-gray-100 px-2 py-1 rounded">{location.pathname}</code>
      </p>
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
        <div className="text-gray-400 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {pageName.replace('-', ' ').charAt(0).toUpperCase() + pageName.replace('-', ' ').slice(1)}
        </h3>
        <p className="text-gray-500">
          This page is ready for your content. Connect it to your analytics features.
        </p>
      </div>
    </div>
  );
};

function AppContent() {
  const location = useLocation();
  
  // Hide sidebar for individual chat view and new thread to maximize chat space
  const fullWidthPages = ['/chat', '/new'];
  const showSidebar = !fullWidthPages.some(path => location.pathname.startsWith(path));

  return (
    <div className="App flex min-h-screen bg-gray-50">
      {showSidebar && <Sidebar />}
      
      {/* Main content area */}
      <main className={`${showSidebar ? 'ml-14' : ''} flex-1 min-h-screen bg-white`}>
        <Routes>
          {/* Main chat interface routes */}
          <Route path="/" element={<NewThreadPage />} />
          <Route path="/new" element={<NewThreadPage />} />
          
          
          {/* Home section routes */}
          <Route path="/home" element={<HomePage />} />
          <Route path="/home/recent" element={<RecentConversationsPage />} />
          <Route path="/home/favorites" element={<FavoritesPage />} />
          <Route path="/home/shared" element={<SharedPage />} />
          
          {/* Discover section routes */}
          <Route path="/discover" element={<DiscoverPage />} />
          <Route path="/discover/for-you" element={<DynamicPage />} />
          <Route path="/discover/tech" element={<DynamicPage />} />
          <Route path="/discover/science" element={<DynamicPage />} />
          <Route path="/discover/business" element={<DynamicPage />} />
          <Route path="/discover/health" element={<DynamicPage />} />
          <Route path="/discover/sports" element={<DynamicPage />} />
          <Route path="/discover/entertainment" element={<DynamicPage />} />
          
          {/* Spaces section routes */}
          <Route path="/spaces" element={<SpacesPage />} />
          <Route path="/spaces/create" element={<DynamicPage />} />
          <Route path="/spaces/my" element={<DynamicPage />} />
          <Route path="/spaces/shared" element={<DynamicPage />} />
          <Route path="/spaces/templates" element={<DynamicPage />} />
          
          {/* Account and settings routes */}
          <Route path="/account" element={<DynamicPage />} />
          <Route path="/upgrade" element={<DynamicPage />} />
          <Route path="/install" element={<DynamicPage />} />
          
          {/* Catch-all route for dynamic pages */}
          <Route path="*" element={<DynamicPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <ChatProvider>
      <Router>
        <AppContent />
      </Router>
    </ChatProvider>
  );
}

export default App; 