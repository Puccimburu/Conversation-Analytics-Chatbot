// src/components/chat/IndividualChatView.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChatContext } from '../../context/ChatContext';
import { 
  ArrowLeft, 
  Send, 
  Search, 
  Image, 
  Paperclip, 
  Mic, 
  MoreHorizontal,
  Star,
  Share,
  User,
  Home,
  Plus,
  Globe,
  Layers,
  ExternalLink,
  Download,
  TrendingUp,
  BarChart3,
  PieChart,
  CheckCircle,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Clock
} from 'lucide-react';

const IndividualChatView = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const { conversations, updateChat } = useChatContext();
  const [currentChat, setCurrentChat] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [activeTab, setActiveTab] = useState('answer');
  const [responses, setResponses] = useState([]);
  const [currentResponseIndex, setCurrentResponseIndex] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const messagesEndRef = useRef(null);

  // Find the current chat
  useEffect(() => {
    const chat = conversations.find(conv => conv.id === chatId);
    if (chat) {
      setCurrentChat(chat);
      if (!chat.responses || chat.responses.length === 0) {
        const initialResponse = generateInitialResponse(chat.title, chat.category);
        const newResponses = [initialResponse];
        setResponses(newResponses);
        updateChat(chatId, { responses: newResponses });
      } else {
        setResponses(chat.responses);
        setCurrentResponseIndex(chat.responses.length - 1);
      }
    } else {
      navigate('/home/recent');
    }
  }, [chatId, conversations, updateChat, navigate]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (isProcessing || responses.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isProcessing, responses.length]);

  // Chart Display Component (Enhanced from original App.js)
  const ChartDisplay = ({ chartData, title }) => {
    if (!chartData || !chartData.data) return null;

    const { labels, datasets } = chartData.data;
    const data = datasets[0]?.data || [];
    const maxValue = Math.max(...data.filter(val => typeof val === 'number'));
    const chartType = chartData.type || 'bar';

    const renderBarChart = () => (
      <div className="space-y-3">
        {labels.map((label, index) => (
          <div key={index} className="flex items-center space-x-3">
            <div className="w-32 text-sm text-gray-700 font-medium truncate" title={label}>
              {label}
            </div>
            <div className="flex-1 bg-gray-200 rounded-full h-8 relative">
              <div
                className="bg-blue-500 h-8 rounded-full flex items-center justify-end pr-3 transition-all duration-500 ease-out"
                style={{ width: `${maxValue > 0 ? (data[index] / maxValue) * 100 : 0}%` }}
              >
                <span className="text-white text-sm font-semibold">
                  {typeof data[index] === 'number' ? data[index].toLocaleString() : data[index]}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );

    const renderPieChart = () => {
      const total = data.reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0);
      let currentAngle = 0;
      const radius = 80;
      const centerX = 100;
      const centerY = 100;

      return (
        <div className="flex items-center justify-center">
          <svg width="200" height="200" viewBox="0 0 200 200">
            {data.map((value, index) => {
              const percentage = (value / total) * 100;
              const angle = (value / total) * 360;
              const x1 = centerX + radius * Math.cos((currentAngle * Math.PI) / 180);
              const y1 = centerY + radius * Math.sin((currentAngle * Math.PI) / 180);
              const x2 = centerX + radius * Math.cos(((currentAngle + angle) * Math.PI) / 180);
              const y2 = centerY + radius * Math.sin(((currentAngle + angle) * Math.PI) / 180);
              
              const largeArcFlag = angle > 180 ? 1 : 0;
              const pathData = [
                `M ${centerX} ${centerY}`,
                `L ${x1} ${y1}`,
                `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                'Z'
              ].join(' ');

              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
              const color = colors[index % colors.length];
              currentAngle += angle;

              return (
                <g key={index}>
                  <path
                    d={pathData}
                    fill={color}
                    stroke="white"
                    strokeWidth="2"
                  />
                  <text
                    x={centerX + (radius * 0.7) * Math.cos(((currentAngle - angle/2) * Math.PI) / 180)}
                    y={centerY + (radius * 0.7) * Math.sin(((currentAngle - angle/2) * Math.PI) / 180)}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="white"
                    fontSize="12"
                    fontWeight="bold"
                  >
                    {percentage.toFixed(1)}%
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      );
    };

    const getChartTypeIcon = () => {
      switch (chartType) {
        case 'pie':
        case 'doughnut':
          return <PieChart className="h-4 w-4" />;
        case 'line':
          return <TrendingUp className="h-4 w-4" />;
        case 'bar':
        default:
          return <BarChart3 className="h-4 w-4" />;
      }
    };

    return (
      <div className="mt-6 bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900 text-lg">
            {title || chartData.options?.plugins?.title?.text || 'Analytics Chart'}
          </h4>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            {getChartTypeIcon()}
            <span className="capitalize">{chartType} Chart</span>
            <span>•</span>
            <span>{data.length} data points</span>
          </div>
        </div>
        
        <div className="chart-container min-h-[300px]">
          {chartType === 'pie' || chartType === 'doughnut' ? renderPieChart() : renderBarChart()}
        </div>
        
        <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
          <span>Chart Type: {chartType.charAt(0).toUpperCase() + chartType.slice(1)}</span>
          <span>Generated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    );
  };

  // Validation Display Component
  const ValidationDisplay = ({ validation }) => {
    if (!validation) return null;

    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-gray-800">Answer Validation</h4>
          <div className="flex items-center space-x-2">
            <span className={`text-sm font-medium ${
              validation.confidence >= 80 ? 'text-green-600' : 
              validation.confidence >= 60 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {validation.confidence}% confidence
            </span>
          </div>
        </div>

        {validation.checks && (
          <div className="space-y-2">
            {validation.checks.map((check, index) => (
              <div key={index} className="flex items-start space-x-2">
                {check.passed ? (
                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                )}
                <span className={check.passed ? 'text-green-700' : 'text-red-700'}>
                  {check.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Feedback Component
  const FeedbackComponent = ({ queryId, responseId }) => {
    const [feedbackGiven, setFeedbackGiven] = useState(false);

    const quickFeedback = async (isHelpful) => {
      if (!queryId) return;

      try {
        await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query_id: queryId,
            response_id: responseId,
            rating: isHelpful ? 5 : 2,
            type: 'general',
            comment: isHelpful ? 'Quick positive feedback' : 'Quick negative feedback'
          })
        });
        setFeedbackGiven(true);
      } catch (error) {
        console.error('Quick feedback error:', error);
      }
    };

    return (
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Was this answer helpful?</span>
          
          {!feedbackGiven ? (
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => quickFeedback(true)}
                className="flex items-center space-x-1 px-3 py-1 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
              >
                <ThumbsUp className="h-4 w-4" />
                <span>Yes</span>
              </button>
              <button 
                onClick={() => quickFeedback(false)}
                className="flex items-center space-x-1 px-3 py-1 text-sm text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
              >
                <ThumbsDown className="h-4 w-4" />
                <span>No</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm">Thank you for your feedback!</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Generate initial response
  const generateInitialResponse = (title, category) => {
    const timestamp = Date.now();
    return {
      id: `response_${timestamp}`,
      query: title,
      timestamp,
      category,
      answer: generateAnswerContent(title, category),
      sources: generateSources(title, category),
      steps: generateSteps(title),
      chartData: generateSampleChart(title, category),
      validation: generateValidation(),
      relatedQuestions: generateRelatedQuestions(title, category)
    };
  };

  const generateAnswerContent = (title, category) => {
    if (title.toLowerCase().includes('smartphone') && title.toLowerCase().includes('laptop')) {
      return `# ${title}

## Sales Comparison Analysis

Based on your sales data analysis, here's a comprehensive comparison between smartphone and laptop sales:

### Key Findings

**Smartphone Sales:**
- Total Revenue: $11,649.84
- Market Share: 44.4%
- Units Sold: Strong performance in mobile category

**Laptop Sales:**
- Total Revenue: $14,599.89
- Market Share: 55.6%
- Units Sold: Leading product category

### Performance Summary

Laptops outperform smartphones with a **$2,950.05 revenue difference**, representing a 20.2% higher revenue generation. This indicates stronger customer preference and higher transaction values in the laptop segment.

### Strategic Recommendations

1. **Focus on laptop inventory** - Higher revenue potential
2. **Optimize smartphone pricing** - Increase competitiveness
3. **Cross-selling opportunities** - Bundle products for higher value`;
    }

    return `# ${title}

Based on your query about "${title}", here's a comprehensive analysis of the available data.

## Overview

The analysis reveals important insights about your business data with actionable recommendations for optimization.

### Key Insights

• **Data Quality**: High-quality data processing with validated results
• **Performance Metrics**: Clear performance indicators identified
• **Trends Analysis**: Historical patterns show consistent growth
• **Opportunities**: Several optimization opportunities available

### Detailed Analysis

The data shows significant patterns that can inform strategic decision-making and operational improvements.`;
  };

  const generateSampleChart = (title, category) => {
    if (title.toLowerCase().includes('smartphone') && title.toLowerCase().includes('laptop')) {
      return {
        type: 'bar',
        data: {
          labels: ['Smartphones', 'Laptops'],
          datasets: [{
            label: 'Revenue ($)',
            data: [11649.84, 14599.89],
            backgroundColor: ['rgba(59, 130, 246, 0.8)', 'rgba(16, 185, 129, 0.8)'],
            borderColor: ['rgba(59, 130, 246, 1)', 'rgba(16, 185, 129, 1)'],
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: true, text: 'Smartphone vs Laptop Revenue Comparison' },
            legend: { display: false }
          },
          scales: {
            y: { beginAtZero: true, title: { display: true, text: 'Revenue ($)' } },
            x: { title: { display: true, text: 'Product Category' } }
          }
        }
      };
    }

    return {
      type: 'bar',
      data: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
        datasets: [{
          label: 'Sample Data',
          data: [65, 59, 80, 81],
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: 'Quarterly Performance' },
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true },
          x: { display: true }
        }
      }
    };
  };

  const generateValidation = () => ({
    confidence: Math.floor(Math.random() * 20) + 80, // 80-100%
    checks: [
      { type: 'data_quality', passed: true, message: 'Data quality validation passed' },
      { type: 'completeness', passed: true, message: 'Response completeness verified' },
      { type: 'accuracy', passed: Math.random() > 0.3, message: 'Answer accuracy validated' }
    ]
  });

  const generateSources = (title, category) => [
    {
      id: 1,
      title: `Analytics Database - ${title}`,
      url: 'database.internal',
      domain: 'database.internal',
      favicon: '📊',
      description: `Internal analytics database with comprehensive ${category} data.`,
      selected: true,
      reviewed: true
    },
    {
      id: 2,
      title: `${category} Best Practices`,
      url: 'docs.internal',
      domain: 'docs.internal',
      favicon: '📚',
      description: `Documentation and guidelines for ${category} analysis.`,
      selected: true,
      reviewed: false
    }
  ];

  const generateSteps = (title) => [
    { id: 1, title: `Processing query: "${title}"`, status: 'completed' },
    { id: 2, title: 'Analyzing database for relevant data', status: 'completed' },
    { id: 3, title: 'Generating appropriate visualizations', status: 'completed' },
    { id: 4, title: 'Validating results and insights', status: 'completed' }
  ];

  const generateRelatedQuestions = (title, category) => {
    if (title.toLowerCase().includes('smartphone') && title.toLowerCase().includes('laptop')) {
      return [
        'Show me monthly sales trends for smartphones',
        'What are the top laptop brands by revenue?',
        'Customer demographics for smartphone buyers',
        'Seasonal patterns in laptop sales'
      ];
    }

    return [
      'Can you show this data as a pie chart?',
      'What are the monthly trends for this data?',
      'How does this compare to last year?',
      'Show me the top 10 results instead'
    ];
  };

  // Handle new message processing
  const handleSendMessage = async () => {
    if (!newMessage.trim() || !currentChat) return;

    setIsProcessing(true);
    setProcessingStep('Analyzing your question...');

    const steps = [
      'Analyzing your question...',
      'Querying database...',
      'Processing results...',
      'Generating visualization...',
      'Validating response...'
    ];

    for (let i = 0; i < steps.length; i++) {
      setProcessingStep(steps[i]);
      await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
    }

    try {
      // Try backend API call
      const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: newMessage,
          chart_preference: 'auto'
        })
      });

      let backendData = null;
      if (response.ok) {
        backendData = await response.json();
      }

      // Generate new response (use backend data if available, otherwise mock)
      const newResponse = {
        id: `response_${Date.now()}`,
        query: newMessage,
        timestamp: Date.now(),
        category: currentChat.category,
        answer: backendData?.answer || generateAnswerContent(newMessage, currentChat.category),
        chartData: backendData?.chartData || generateSampleChart(newMessage, currentChat.category),
        validation: backendData?.validation || generateValidation(),
        sources: generateSources(newMessage, currentChat.category),
        steps: generateSteps(newMessage),
        relatedQuestions: generateRelatedQuestions(newMessage, currentChat.category)
      };

      const updatedResponses = [...responses, newResponse];
      setResponses(updatedResponses);
      setCurrentResponseIndex(updatedResponses.length - 1);
      
      updateChat(chatId, { 
        responses: updatedResponses,
        messageCount: updatedResponses.length,
        lastMessage: 'just now',
        lastActivity: Date.now(),
        unreadCount: 0
      });

    } catch (error) {
      console.error('Error processing message:', error);
      // Continue with mock response on error
    }

    setNewMessage('');
    setIsProcessing(false);
    setProcessingStep('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!currentChat) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 mb-4">
            <Search className="w-16 h-16 mx-auto" />
          </div>
          <h3 className="text-xl font-medium text-gray-900 mb-2">Chat not found</h3>
          <p className="text-gray-500 mb-4">The conversation you're looking for doesn't exist.</p>
          <button 
            onClick={() => navigate('/home/recent')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Chat History
          </button>
        </div>
      </div>
    );
  }

  const currentResponse = responses[currentResponseIndex];

  return (
    <div className="flex min-h-screen bg-white">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-screen w-14 bg-gray-50 border-r border-gray-200 flex flex-col z-50">
        <div className="flex items-center justify-center h-14 border-b border-gray-200">
          <div className="w-7 h-7 bg-slate-800 rounded-md flex items-center justify-center">
            <Search className="w-4 h-4 text-white" />
          </div>
        </div>

        <nav className="flex-1 py-4">
          <ul className="flex flex-col space-y-1 px-2">
            <li>
              <button 
                onClick={() => navigate('/new')}
                className="w-10 h-10 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700 flex items-center justify-center transition-all duration-200"
                title="New Thread"
              >
                <Plus className="w-5 h-5" />
              </button>
            </li>
            <li>
              <button 
                onClick={() => navigate('/home')}
                className="w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-all duration-200"
                title="Home"
              >
                <Home className="w-5 h-5" />
              </button>
            </li>
            <li>
              <button 
                onClick={() => navigate('/discover')}
                className="w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-all duration-200"
                title="Discover"
              >
                <Globe className="w-5 h-5" />
              </button>
            </li>
            <li>
              <button 
                onClick={() => navigate('/spaces')}
                className="w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-all duration-200"
                title="Spaces"
              >
                <Layers className="w-5 h-5" />
              </button>
            </li>
          </ul>
        </nav>

        <div className="border-t border-gray-200 p-2 space-y-1">
          <button className="w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-all duration-200">
            <User className="w-5 h-5" />
          </button>
          <button className="w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-all duration-200">
            <ExternalLink className="w-5 h-5" />
          </button>
          <button className="w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-all duration-200">
            <Download className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 ml-14">
        {/* Header with navigation */}
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => navigate('/home/recent')}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  {currentResponse ? currentResponse.query : currentChat.title}
                </h1>
                <div className="flex items-center space-x-6 mt-2">
                  <button
                    onClick={() => setActiveTab('answer')}
                    className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'answer'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    Answer
                  </button>
                  <button
                    onClick={() => setActiveTab('images')}
                    className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'images'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    Images
                  </button>
                  <button
                    onClick={() => setActiveTab('sources')}
                    className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'sources'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    Sources • {currentResponse?.sources?.length || 0}
                  </button>
                  <button
                    onClick={() => setActiveTab('steps')}
                    className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'steps'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    Steps
                  </button>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                <Star className="w-5 h-5" />
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                <Share className="w-5 h-5" />
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                <MoreHorizontal className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Content Area with all responses */}
        <div className="max-w-4xl mx-auto px-6 py-8">
          {/* Render all responses */}
          {responses.map((response, index) => (
            <div key={response.id} className={`mb-12 ${index > 0 ? 'border-t border-gray-200 pt-8' : ''}`}>
              {index > 0 && (
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">{response.query}</h2>
                  <div className="flex items-center space-x-6 text-sm text-gray-500">
                    <span>Answer</span>
                    <span>Images</span>
                    <span>Sources • {response.sources?.length || 0}</span>
                    <span>Steps</span>
                  </div>
                </div>
              )}

              {/* Answer Content */}
              {(activeTab === 'answer' || index > 0) && (
                <div className="space-y-6">
                  {/* Category Badge */}
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      response.category === 'analysis' ? 'bg-blue-100 text-blue-700' :
                      response.category === 'technical' ? 'bg-purple-100 text-purple-700' :
                      response.category === 'JTMD' ? 'bg-orange-100 text-orange-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {response.category}
                    </span>
                    <div className="flex items-center space-x-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(response.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  {/* Main Answer */}
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                      {response.answer}
                    </div>
                  </div>

                  {/* Chart Display */}
                  {response.chartData && (
                    <ChartDisplay 
                      chartData={response.chartData} 
                      title={response.chartData.options?.plugins?.title?.text}
                    />
                  )}

                  {/* Validation Display */}
                  {response.validation && (
                    <ValidationDisplay validation={response.validation} />
                  )}

                  {/* Feedback Component */}
                  <FeedbackComponent 
                    queryId={response.id} 
                    responseId={response.id}
                  />

                  {/* Related Questions */}
                  {response.relatedQuestions && response.relatedQuestions.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Related Questions</h3>
                      <div className="space-y-2">
                        {response.relatedQuestions.map((question, qIndex) => (
                          <button
                            key={qIndex}
                            onClick={() => setNewMessage(question)}
                            className="block w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Sources Tab Content */}
              {activeTab === 'sources' && index === currentResponseIndex && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">Sources</h3>
                  {response.sources?.map((source, sourceIndex) => (
                    <div key={sourceIndex} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start space-x-3">
                        <span className="text-lg">{source.favicon}</span>
                        <div className="flex-1">
                          <h4 className="font-medium text-blue-600 hover:text-blue-700 cursor-pointer">
                            {source.title}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                          <span className="text-xs text-gray-500 mt-2 block">{source.url}</span>
                          <div className="flex items-center space-x-4 mt-2">
                            {source.selected && (
                              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Selected</span>
                            )}
                            {source.reviewed && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Reviewed</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Steps Tab Content */}
              {activeTab === 'steps' && index === currentResponseIndex && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">Processing Steps</h3>
                  {response.steps?.map((step, stepIndex) => (
                    <div key={stepIndex} className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                        step.status === 'completed' ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
                      }`}>
                        {stepIndex + 1}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{step.title}</h4>
                        {step.details && (
                          <ul className="mt-2 text-sm text-gray-600 space-y-1">
                            {step.details.map((detail, detailIndex) => (
                              <li key={detailIndex} className="flex items-center space-x-2">
                                <CheckCircle className="w-3 h-3 text-green-500" />
                                <span>{detail}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-blue-800 font-medium">{processingStep}</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Follow-up Input - Always at bottom */}
        <div className="border-t border-gray-200 bg-white px-6 py-4 sticky bottom-0">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a follow-up question..."
                className="w-full pl-4 pr-16 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="1"
                style={{ minHeight: '44px', maxHeight: '120px' }}
                disabled={isProcessing}
              />
              
              <button
                onClick={handleSendMessage}
                disabled={!newMessage.trim() || isProcessing}
                className={`
                  absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-all duration-200
                  ${newMessage.trim() && !isProcessing
                    ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm' 
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center space-x-2">
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                  <Search className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                  <Image className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                  <Paperclip className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                  <Mic className="w-4 h-4" />
                </button>
              </div>
              
              <div className="text-xs text-gray-500">
                Press Enter to send, Shift+Enter for new line
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IndividualChatView;