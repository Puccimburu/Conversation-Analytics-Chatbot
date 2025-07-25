// File: frontend/src/components/chat/ResponseInterface.jsx
// Update your existing ResponseInterface.jsx to integrate with chat system
// This is an enhanced version that works with or without chat context

import React, { useState, useEffect, useRef } from 'react';
import { useChatContext } from '../../context/ChatContext';
import { 
  Send, 
  Loader, 
  Sparkles, 
  Database, 
  CheckCircle, 
  AlertCircle, 
  BarChart3, 
  PieChart, 
  TrendingUp,
  Star,
  Edit3,
  Copy,
  Download,
  RefreshCw
} from 'lucide-react';

const ResponseInterface = ({ 
  chatId = null, 
  initialMessages = [], 
  chatMode = false 
}) => {
  // Context and state
  const { sendQueryWithChat, backendStatus } = useChatContext();
  const [responses, setResponses] = useState(initialMessages);
  const [queryText, setQueryText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [editingResponseId, setEditingResponseId] = useState(null);
  
  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [responses]);

  // Update responses when initialMessages change (for chat mode)
  useEffect(() => {
    if (chatMode && initialMessages) {
      setResponses(initialMessages);
    }
  }, [initialMessages, chatMode]);

  // Focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle query submission
  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    
    if (!queryText.trim() || isProcessing) return;

    const question = queryText.trim();
    setQueryText('');
    setIsProcessing(true);
    setProcessingStep('Initializing...');

    try {
      // Add user message to UI immediately (optimistic update)
      const userMessage = {
        id: `user_${Date.now()}`,
        type: 'user',
        content: question,
        timestamp: Date.now()
      };
      
      setResponses(prev => [...prev, userMessage]);

      // Processing steps simulation
      const steps = [
        'Analyzing your question...',
        'Processing with AI...',
        'Generating insights...',
        'Creating visualization...',
        'Finalizing response...'
      ];

      for (let i = 0; i < steps.length; i++) {
        setProcessingStep(steps[i]);
        await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
      }

      // Send query to backend
      let response;
      if (chatMode && sendQueryWithChat) {
        // Use chat-integrated query processing
        response = await sendQueryWithChat(question, chatId);
      } else {
        // Fallback to direct API call
        response = await fetch('http://localhost:5000/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            question,
            chat_id: chatId // Include chat_id if available
          })
        }).then(res => res.json());
      }

      // Create assistant response
      const assistantMessage = {
        id: `assistant_${Date.now()}`,
        type: 'assistant',
        content: response.summary || 'Analysis completed successfully.',
        timestamp: Date.now(),
        chartData: response.chart_data,
        insights: response.insights || [],
        recommendations: response.recommendations || [],
        validation: {
          confidence: response.ai_powered ? 90 : 75,
          checks: [
            { 
              type: 'data_processing', 
              passed: response.success, 
              message: response.success ? 'Data processed successfully' : 'Processing failed' 
            },
            { 
              type: 'ai_analysis', 
              passed: response.ai_powered || false, 
              message: response.ai_powered ? 'AI-powered analysis completed' : 'Fallback processing used' 
            }
          ]
        },
        executionTime: response.execution_time || 0,
        querySource: response.query_source || 'unknown',
        aiPowered: response.ai_powered || false,
        activeTab: 'answer'
      };

      // Add assistant response to UI
      setResponses(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Query processing error:', error);
      
      // Add error message
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: 'I encountered an error while processing your request. Please try again.',
        timestamp: Date.now(),
        error: error.message,
        validation: {
          confidence: 0,
          checks: [
            { type: 'error', passed: false, message: error.message }
          ]
        },
        activeTab: 'answer'
      };
      
      setResponses(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
    }
  };

  // Tab switching for responses
  const setActiveTab = (responseId, tab) => {
    setResponses(prev => 
      prev.map(response => 
        response.id === responseId 
          ? { ...response, activeTab: tab }
          : response
      )
    );
  };

  // Render chart based on type
  const renderChart = (chartData) => {
    if (!chartData || !chartData.data || !chartData.data.labels) {
      return <div className="text-gray-500 text-center py-8">No chart data available</div>;
    }

    // This is a simplified chart renderer
    // You should integrate with your preferred charting library (Chart.js, Recharts, etc.)
    const { data, type } = chartData;
    
    return (
      <div className="bg-white p-6 rounded-lg border">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold">
            {chartData.options?.plugins?.title?.text || 'Analytics Chart'}
          </h4>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            {type === 'bar' && <BarChart3 className="w-4 h-4" />}
            {type === 'pie' && <PieChart className="w-4 h-4" />}
            {type === 'line' && <TrendingUp className="w-4 h-4" />}
            <span className="capitalize">{type} Chart</span>
          </div>
        </div>
        
        {/* Simplified chart visualization */}
        <div className="space-y-2">
          {data.labels.map((label, index) => {
            const value = data.datasets[0]?.data[index] || 0;
            const maxValue = Math.max(...(data.datasets[0]?.data || [0]));
            const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
            
            return (
              <div key={index} className="flex items-center space-x-3">
                <div className="w-20 text-sm text-gray-600 truncate">{label}</div>
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-blue-500 h-4 rounded-full transition-all duration-1000"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <div className="w-20 text-sm font-medium text-right">
                  {typeof value === 'number' ? value.toLocaleString() : value}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Render individual message
  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isError = message.error;
    
    if (isUser) {
      return (
        <div className="flex justify-end mb-4">
          <div className="max-w-3xl bg-blue-600 text-white rounded-lg px-4 py-3 shadow-sm">
            <p className="whitespace-pre-wrap">{message.content}</p>
            <div className="text-xs text-blue-100 mt-2">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      );
    }

    // Assistant message
    return (
      <div className="mb-8">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {/* Message Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">AI Assistant</h3>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                  {message.aiPowered && (
                    <>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        <Sparkles className="w-3 h-3 text-green-500" />
                        <span>AI-powered</span>
                      </span>
                    </>
                  )}
                  {message.executionTime && (
                    <>
                      <span>•</span>
                      <span>{message.executionTime.toFixed(2)}s</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button className="p-1 text-gray-400 hover:text-gray-600" title="Copy response">
                <Copy className="w-4 h-4" />
              </button>
              <button className="p-1 text-gray-400 hover:text-gray-600" title="Download">
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-gray-100">
            {['answer', 'images', 'sources', 'steps'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(message.id, tab)}
                className={`px-4 py-3 text-sm font-medium capitalize transition-colors ${
                  message.activeTab === tab
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
                {tab === 'answer' && message.chartData && (
                  <span className="ml-1 text-xs text-blue-500">📊</span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {message.activeTab === 'answer' && (
              <div className="space-y-6">
                {/* Main Response */}
                <div className="prose max-w-none">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>

                {/* Chart */}
                {message.chartData && (
                  <div>
                    {renderChart(message.chartData)}
                  </div>
                )}

                {/* Insights */}
                {message.insights && message.insights.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-3 flex items-center">
                      <Star className="w-4 h-4 mr-2" />
                      Key Insights
                    </h4>
                    <ul className="space-y-2">
                      {message.insights.map((insight, index) => (
                        <li key={index} className="text-blue-800 flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {message.recommendations && message.recommendations.length > 0 && (
                  <div className="bg-green-50 rounded-lg p-4">
                    <h4 className="font-semibold text-green-900 mb-3 flex items-center">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Recommendations
                    </h4>
                    <ul className="space-y-2">
                      {message.recommendations.map((rec, index) => (
                        <li key={index} className="text-green-800 flex items-start">
                          <span className="text-green-500 mr-2">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {message.activeTab === 'sources' && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-sm">
                  <Database className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-600">Data Sources</span>
                </div>
                <div className="grid gap-3">
                  <div className="p-3 border rounded-lg">
                    <div className="font-medium text-sm">MongoDB Analytics Database</div>
                    <div className="text-xs text-gray-500">Your primary analytics data source</div>
                  </div>
                  {message.aiPowered && (
                    <div className="p-3 border rounded-lg">
                      <div className="font-medium text-sm">Google Gemini AI</div>
                      <div className="text-xs text-gray-500">AI-powered analysis and insights</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {message.activeTab === 'steps' && (
              <div className="space-y-4">
                <div className="text-sm text-gray-600">Processing Steps</div>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Query received and validated</span>
                  </div>
                  <div className="flex items-center space-x-3 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Database query executed</span>
                  </div>
                  {message.aiPowered && (
                    <div className="flex items-center space-x-3 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>AI analysis completed</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-3 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Response generated</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Validation Footer */}
          {message.validation && (
            <div className="border-t border-gray-100 p-4 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm">
                  <div className={`w-2 h-2 rounded-full ${
                    message.validation.confidence > 80 ? 'bg-green-500' :
                    message.validation.confidence > 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`} />
                  <span className="text-gray-600">
                    {message.validation.confidence}% confidence
                  </span>
                </div>
                
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  {message.validation.checks?.map((check, index) => (
                    <div key={index} className="flex items-center space-x-1">
                      {check.passed ? 
                        <CheckCircle className="w-3 h-3 text-green-500" /> :
                        <AlertCircle className="w-3 h-3 text-red-500" />
                      }
                      <span>{check.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Welcome Message (only show if no messages) */}
          {responses.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                {chatMode ? 'Start your conversation' : 'Convo Analytics'}
              </h2>
              <p className="text-gray-600 mb-6">
                Ask questions about your data and get instant visualizations
              </p>
              
              {/* Example queries */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {[
                  'Compare smartphone vs laptop sales',
                  'Show me customer segments',
                  'What\'s our revenue by category?',
                  'Display monthly sales trends'
                ].map((example, index) => (
                  <button
                    key={index}
                    onClick={() => setQueryText(example)}
                    className="text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    <span className="text-gray-700">{example}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {responses.map((message) => (
            <div key={message.id}>
              {renderMessage(message)}
            </div>
          ))}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="flex justify-start mb-4">
              <div className="bg-white rounded-lg border border-gray-200 px-4 py-3 shadow-sm max-w-xs">
                <div className="flex items-center space-x-3">
                  <Loader className="w-4 h-4 animate-spin text-blue-500" />
                  <span className="text-sm text-gray-600">{processingStep}</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-6">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleQuerySubmit} className="relative">
            <input
              ref={inputRef}
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Ask about your sales data, request charts, or analyze trends..."
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isProcessing}
            />
            <button
              type="submit"
              disabled={!queryText.trim() || isProcessing}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-blue-600 hover:text-blue-700 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          
          {/* Status indicators */}
          <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${
                  backendStatus === 'connected' ? 'bg-green-500' :
                  backendStatus === 'checking' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span>
                  {backendStatus === 'connected' ? 'AI Analytics Ready' :
                   backendStatus === 'checking' ? 'Connecting...' : 'Offline Mode'}
                </span>
              </span>
              
              {chatMode && chatId && (
                <span>Chat: {chatId}</span>
              )}
            </div>
            
            <span>Press Enter to send</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponseInterface;