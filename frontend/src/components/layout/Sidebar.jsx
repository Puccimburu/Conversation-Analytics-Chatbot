import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Search,
  Plus,
  Home,
  Globe,
  Layers,
  User,
  ExternalLink,
  Download
} from 'lucide-react';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [hoveredItem, setHoveredItem] = useState(null);
  const [expandedPanel, setExpandedPanel] = useState(null);

  // Navigation items matching Perplexity's structure
  const navigationItems = [
    { 
      name: 'conversational ai', 
      icon: Search, 
      path: '/', 
      isLogo: true
    },
    { 
      name: 'New Thread', 
      icon: Plus, 
      path: '/new', 
      isAction: true
    },
    { 
      name: 'Home', 
      icon: Home, 
      path: '/home',
      subcategories: [
        { name: 'Recent Conversations', path: '/home/recent' },
        { name: 'Favorites', path: '/home/favorites' },
        { name: 'Shared', path: '/home/shared' }
      ]
    },
    { 
      name: 'Discover', 
      icon: Globe, 
      path: '/discover',
      subcategories: [
        { name: 'For You', path: '/discover/for-you' },
        { name: 'Technology', path: '/discover/tech' },
        { name: 'Science', path: '/discover/science' },
        { name: 'Business', path: '/discover/business' },
        { name: 'Health', path: '/discover/health' },
        { name: 'Sports', path: '/discover/sports' },
        { name: 'Entertainment', path: '/discover/entertainment' }
      ]
    },
    { 
      name: 'Spaces', 
      icon: Layers, 
      path: '/spaces',
      subcategories: [
        { name: 'Create Space', path: '/spaces/create' },
        { name: 'My Spaces', path: '/spaces/my' },
        { name: 'Shared Spaces', path: '/spaces/shared' },
        { name: 'Templates', path: '/spaces/templates' }
      ]
    }
  ];

  const bottomItems = [
    { name: 'Account', icon: User, path: '/account', isBottom: true },
    { name: 'Upgrade', icon: ExternalLink, path: '/upgrade', isBottom: true },
    { name: 'Install', icon: Download, path: '/install', isBottom: true }
  ];

  const handleItemHover = (item, index) => {
    if (item.subcategories) {
      setHoveredItem(index);
      setExpandedPanel(item);
    }
  };

  const handleSubcategoryClick = (path) => {
    navigate(path);
    setExpandedPanel(null);
    setHoveredItem(null);
  };

  const handleNavClick = (item) => {
    if (!item.subcategories) {
      navigate(item.path);
    }
  };

  const handleSidebarAreaLeave = () => {
    setHoveredItem(null);
    setExpandedPanel(null);
  };

  return (
    <div 
      className="fixed left-0 top-0 z-50 flex"
      onMouseLeave={handleSidebarAreaLeave}
    >
      {/* Main Sidebar */}
      <aside className="h-screen w-14 bg-gray-50 border-r border-gray-200 flex flex-col">
        {/* Logo Section */}
        <div className="flex items-center justify-center h-14 border-b border-gray-200">
          <div className="w-7 h-7 bg-slate-800 rounded-md flex items-center justify-center">
            <Search className="w-4 h-4 text-white" />
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-4">
          <ul className="flex flex-col space-y-1 px-2">
            {navigationItems.slice(1).map((item, index) => {
              const IconComponent = item.icon;
              const actualIndex = index + 1;
              
              return (
                <li 
                  key={actualIndex}
                  className="relative group"
                  onMouseEnter={() => handleItemHover(item, actualIndex)}
                >
                  <button 
                    className={`
                      w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-200
                      ${item.isAction 
                        ? 'bg-gray-200 hover:bg-gray-300 text-gray-700' 
                        : location.pathname === item.path
                          ? 'bg-teal-600 text-white shadow-lg'
                          : 'text-gray-600 hover:bg-gray-200 hover:text-gray-900'
                      }
                      ${hoveredItem === actualIndex ? 'bg-gray-200 text-gray-900' : ''}
                    `}
                    onClick={() => handleNavClick(item)}
                    title={item.name}
                  >
                    <IconComponent className="w-5 h-5" />
                  </button>
                  
                  {/* Tooltip */}
                  <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    {item.name}
                  </div>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom Section */}
        <div className="border-t border-gray-200 p-2 space-y-1">
          {bottomItems.map((item, index) => {
            const IconComponent = item.icon;
            
            return (
              <div key={index} className="relative group">
                <button
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-gray-600 hover:bg-gray-200 hover:text-gray-900 transition-all duration-200"
                  onClick={() => handleNavClick(item)}
                  title={item.name}
                >
                  {item.name === 'Account' ? (
                    <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                      C
                    </div>
                  ) : (
                    <IconComponent className="w-5 h-5" />
                  )}
                </button>
                
                {/* Tooltip */}
                <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {item.name}
                </div>
              </div>
            );
          })}
        </div>
      </aside>

      {/* Expandable Panel */}
      {expandedPanel && (
        <div className="h-screen w-64 bg-white border-r border-gray-200 shadow-lg">
          {/* Panel Header */}
          <div className="h-14 border-b border-gray-200 flex items-center px-6 bg-gray-50">
            <div className="flex items-center space-x-3">
              <expandedPanel.icon className="w-5 h-5 text-teal-600" />
              <span className="font-medium text-gray-900">{expandedPanel.name}</span>
            </div>
          </div>
          
          {/* Panel Content */}
          <div className="py-4">
            <ul className="space-y-1">
              {expandedPanel.subcategories?.map((subcat, index) => (
                <li key={index}>
                  <button 
                    className={`
                      w-full text-left px-6 py-2.5 text-sm transition-colors duration-200 flex items-center justify-between group
                      ${location.pathname === subcat.path 
                        ? 'bg-teal-50 text-teal-700 border-r-2 border-teal-600' 
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }
                    `}
                    onClick={() => handleSubcategoryClick(subcat.path)}
                  >
                    <span>{subcat.name}</span>
                    <span className="text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      {subcat.path}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;