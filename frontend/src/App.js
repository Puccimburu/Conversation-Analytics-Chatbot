import React, { useState, useRef, useEffect } from 'react';
import { Send, BarChart3, TrendingUp, Database, MessageCircle, Loader } from 'lucide-react';

// Chart.js components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement,
} from 'chart.js';
import { Bar, Pie, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement
);

const API_BASE_URL = 'http://localhost:5000/api';

const ConversationalAnalytics = () => {
  const [messages, setMessages] = useState([
    {
      type: 'system',
      content: "Hello! I'm your AI analytics assistant. Ask me anything about your sales data, customer insights, or business metrics. Try questions like 'What were our top selling products last month?' or 'Show me revenue by region'.",
      timestamp: new Date()
    }
  ]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Fetch basic stats on component mount
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`);
      const data = await response.json();
      setStats(data.overview || data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const renderChart = (chartData) => {
    if (!chartData) return null;

    const chartProps = {
      data: chartData.data,
      options: chartData.options
    };

    switch (chartData.type) {
      case 'bar':
        return <Bar {...chartProps} />;
      case 'pie':
        return <Pie {...chartProps} />;
      case 'doughnut':
        return <Doughnut {...chartProps} />;
      case 'line':
        return <Line {...chartProps} />;
      default:
        return <Bar {...chartProps} />;
    }
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!currentQuery.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: currentQuery,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentQuery('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: currentQuery }),
      });

      const result = await response.json();

      if (response.ok) {
        const assistantMessage = {
          type: 'assistant',
          content: result.summary,
          chartData: result.chart_data,
          rawData: result.raw_data,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        const errorMessage = {
          type: 'error',
          content: `Error: ${result.error || 'Something went wrong'}`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: `Connection error: ${error.message}. Make sure the backend server is running on http://localhost:5000`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestedQueries = [
    "What were our top 5 selling products this quarter?",
    "Show me revenue by region and month",
    "Which customer segment generates the most profit?",
    "Compare smartphone vs laptop sales performance",
    "What's our conversion rate by marketing channel?",
    "Show me inventory levels for low-stock products"
  ];

  const handleSuggestedQuery = (query) => {
    setCurrentQuery(query);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="bg-indigo-600 p-2 rounded-lg">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Conversational Analytics</h1>
                <p className="text-sm text-gray-500">Ask questions about your data in natural language</p>
              </div>
            </div>
            
            {/* Stats Display */}
            {stats && (
              <div className="hidden md:flex space-x-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-600">{stats.total_sales || 0}</div>
                  <div className="text-xs text-gray-500">Total Orders</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">${stats.total_revenue?.toLocaleString() || 0}</div>
                  <div className="text-xs text-gray-500">Total Revenue</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{stats.total_customers || 0}</div>
                  <div className="text-xs text-gray-500">Customers</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Suggested Queries Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <MessageCircle className="h-5 w-5 mr-2 text-indigo-600" />
                Suggested Questions
              </h3>
              <div className="space-y-2">
                {suggestedQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuery(query)}
                    className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-indigo-50 rounded-lg transition-colors duration-200"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Chat Interface */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm">
              {/* Messages Area */}
              <div className="h-96 overflow-y-auto p-6 space-y-6">
                {messages.map((message, index) => (
                  <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-2xl ${
                      message.type === 'user' 
                        ? 'bg-indigo-600 text-white' 
                        : message.type === 'error'
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : 'bg-gray-100 text-gray-900'
                    } rounded-lg p-4`}>
                      <p className="text-sm">{message.content}</p>
                      
                      {/* Chart Display */}
                      {message.chartData && (
                        <div className="mt-4 bg-white p-4 rounded-lg">
                          <div className="h-64">
                            {renderChart(message.chartData)}
                          </div>
                        </div>
                      )}
                      
                      <div className="text-xs opacity-70 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Loading Message */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-900 rounded-lg p-4 flex items-center space-x-2">
                      <Loader className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Analyzing your data...</span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t p-6">
                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={currentQuery}
                    onChange={(e) => setCurrentQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSubmit(e)}
                    placeholder="Ask a question about your data..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={isLoading || !currentQuery.trim()}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isLoading ? (
                      <Loader className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    <span>Ask</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationalAnalytics;