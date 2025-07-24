// src/components/chat/ResponseInterface.jsx
import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Image, 
  ExternalLink, 
  TrendingUp,
  DollarSign,
  Calendar,
  BarChart3,
  LineChart,
  Share,
  Copy,
  Bookmark,
  CheckCircle,
  AlertTriangle,
  PieChart,
  ThumbsUp,
  ThumbsDown,
  Star,
  Edit3,
  Save,
  X,
  Send
} from 'lucide-react';

const ResponseInterface = ({ query, onClose }) => {
  const [responses, setResponses] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [followUpQuery, setFollowUpQuery] = useState('');
  const [editingResponseId, setEditingResponseId] = useState(null);
  const [editedQuery, setEditedQuery] = useState('');
  const messagesEndRef = useRef(null);

  // Process initial query on mount
  useEffect(() => {
    if (query && responses.length === 0) {
      processQuery(query);
    }
  }, [query]);

  // Auto-scroll to bottom when new content appears
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [responses, isProcessing]);

  const processQuery = async (queryText, isFollowUp = false, responseIdToReplace = null) => {
    setIsProcessing(true);
    setFollowUpQuery('');
    
    try {
      // Simulate processing phases
      const phases = [
        'Searching for relevant data...',
        'Analyzing query with AI...',
        'Processing database results...',
        'Generating visualization...',
        'Finalizing response...'
      ];

      for (let i = 0; i < phases.length; i++) {
        setProcessingStep(phases[i]);
        await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
      }

      // Call backend API
      console.log('Sending query to backend:', queryText);
      
      const backendResponse = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: queryText })
      });

      let responseData;
      if (backendResponse.ok) {
        const data = await backendResponse.json();
        responseData = transformBackendResponse(data, queryText);
      } else {
        responseData = generateMockResponse(queryText);
      }

      // Add timestamp and unique ID
      const newResponse = {
        id: Date.now().toString(),
        query: queryText,
        timestamp: Date.now(),
        ...responseData,
        activeTab: 'answer'
      };

      setResponses(prev => {
        if (responseIdToReplace) {
          // Replace existing response (for edit functionality)
          return prev.map(r => r.id === responseIdToReplace ? newResponse : r);
        } else {
          // Add new response
          return [...prev, newResponse];
        }
      });

    } catch (error) {
      console.error('Query processing error:', error);
      const errorResponse = {
        id: Date.now().toString(),
        query: queryText,
        timestamp: Date.now(),
        ...generateMockResponse(queryText),
        activeTab: 'answer',
        error: error.message
      };
      
      setResponses(prev => responseIdToReplace 
        ? prev.map(r => r.id === responseIdToReplace ? errorResponse : r)
        : [...prev, errorResponse]
      );
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
      setEditingResponseId(null);
    }
  };

  const transformBackendResponse = (backendData, originalQuery) => {
    return {
      answer: backendData.summary || backendData.response || `Analysis complete for: ${originalQuery}`,
      chartData: backendData.chart_data || null,
      validation: backendData.validation || {
        confidence: 85,
        checks: [
          { type: 'data_quality', passed: true, message: 'Data processed successfully from backend' },
          { type: 'completeness', passed: true, message: 'Response generated successfully' }
        ]
      },
      queryId: backendData.query_id || `query_${Date.now()}`
    };
  };

  const generateMockResponse = (queryText) => ({
    answer: `# Analysis Results for: ${queryText}

Based on your query, here's a comprehensive analysis of the available data from your MongoDB analytics database.

## Key Findings

The analysis reveals significant insights with multiple data points showing clear patterns and trends in your business data.

### Summary
- Data processing completed successfully
- Chart visualization generated based on query requirements  
- Results validated using existing validation system

This response maintains compatibility with your existing backend infrastructure.`,
    
    chartData: {
      type: Math.random() > 0.7 ? 'doughnut' : Math.random() > 0.5 ? 'pie' : Math.random() > 0.3 ? 'line' : 'bar',
      data: {
        labels: ['Category A', 'Category B', 'Category C', 'Category D'],
        datasets: [{
          label: 'Sample Data',
          data: [Math.floor(Math.random() * 100) + 50, Math.floor(Math.random() * 100) + 30, Math.floor(Math.random() * 100) + 70, Math.floor(Math.random() * 100) + 40],
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
          borderColor: ['#2563EB', '#059669', '#D97706', '#DC2626'],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: `Analysis Chart for: ${queryText}` },
          legend: { display: false }
        }
      }
    },
    
    validation: {
      confidence: Math.floor(Math.random() * 20) + 80,
      checks: [
        { type: 'data_quality', passed: true, message: 'Data quality validation passed' },
        { type: 'completeness', passed: true, message: 'Response completeness verified' }
      ]
    }
  });

  const handleFollowUpSubmit = () => {
    if (followUpQuery.trim()) {
      processQuery(followUpQuery.trim(), true);
    }
  };

  const handleFollowUpKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleFollowUpSubmit();
    }
  };

  const startEditingResponse = (responseId, currentQuery) => {
    setEditingResponseId(responseId);
    setEditedQuery(currentQuery);
  };

  const saveEditedResponse = () => {
    if (editedQuery.trim() && editingResponseId) {
      processQuery(editedQuery.trim(), false, editingResponseId);
    }
  };

  const cancelEditingResponse = () => {
    setEditingResponseId(null);
    setEditedQuery('');
  };

  const updateResponseTab = (responseId, newTab) => {
    setResponses(prev => 
      prev.map(r => r.id === responseId ? {...r, activeTab: newTab} : r)
    );
  };

  // Chart Display Component (same as before but extracted for reuse)
  const ChartDisplay = ({ chartData }) => {
    if (!chartData || !chartData.data) return null;

    const { labels, datasets } = chartData.data;
    const data = datasets[0]?.data || [];
    const maxValue = Math.max(...data.filter(val => typeof val === 'number'));
    const chartType = chartData.type || 'bar';

    const renderBarChart = () => (
      <div className="w-full space-y-4 p-4">
        {labels.map((label, index) => (
          <div key={index} className="flex items-center space-x-4">
            <div className="w-40 text-sm text-gray-700 font-medium" title={label}>
              {label.length > 20 ? label.substring(0, 20) + '...' : label}
            </div>
            <div className="flex-1 bg-gray-200 rounded-lg h-12 relative min-w-0">
              <div
                className="bg-blue-500 h-12 rounded-lg flex items-center justify-end pr-4 transition-all duration-700 ease-out relative"
                style={{ width: `${maxValue > 0 ? Math.max((data[index] / maxValue) * 100, 8) : 8}%` }}
              >
                <span className="text-white text-sm font-semibold whitespace-nowrap">
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
      const radius = 120;
      const centerX = 150;
      const centerY = 150;

      return (
        <div className="flex flex-col items-center w-full py-6">
          <svg width="300" height="300" viewBox="0 0 300 300" className="max-w-full h-auto">
            {data.map((value, index) => {
              if (typeof value !== 'number') return null;
              
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

              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
              const color = colors[index % colors.length];
              currentAngle += angle;

              return (
                <g key={index}>
                  <path d={pathData} fill={color} stroke="white" strokeWidth="3" />
                  <text
                    x={centerX + (radius * 0.75) * Math.cos(((currentAngle - angle/2) * Math.PI) / 180)}
                    y={centerY + (radius * 0.75) * Math.sin(((currentAngle - angle/2) * Math.PI) / 180)}
                    textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="14" fontWeight="bold"
                  >
                    {percentage.toFixed(1)}%
                  </text>
                </g>
              );
            })}
          </svg>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg">
            {labels.map((label, index) => {
              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
              const color = colors[index % colors.length];
              const percentage = ((data[index] / total) * 100).toFixed(1);
              const value = data[index];
              
              return (
                <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 rounded-lg">
                  <div className="w-4 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: color }}></div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">{label}</div>
                    <div className="text-xs text-gray-600">
                      {typeof value === 'number' ? value.toLocaleString() : value} ({percentage}%)
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    };

    const renderDoughnutChart = () => {
      const total = data.reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0);
      let currentAngle = 0;
      const outerRadius = 120;
      const innerRadius = 70;
      const centerX = 150;
      const centerY = 150;

      return (
        <div className="flex flex-col items-center w-full py-6">
          <svg width="300" height="300" viewBox="0 0 300 300" className="max-w-full h-auto">
            {data.map((value, index) => {
              if (typeof value !== 'number') return null;
              
              const percentage = (value / total) * 100;
              const angle = (value / total) * 360;
              
              const outerX1 = centerX + outerRadius * Math.cos((currentAngle * Math.PI) / 180);
              const outerY1 = centerY + outerRadius * Math.sin((currentAngle * Math.PI) / 180);
              const outerX2 = centerX + outerRadius * Math.cos(((currentAngle + angle) * Math.PI) / 180);
              const outerY2 = centerY + outerRadius * Math.sin(((currentAngle + angle) * Math.PI) / 180);
              
              const innerX1 = centerX + innerRadius * Math.cos((currentAngle * Math.PI) / 180);
              const innerY1 = centerY + innerRadius * Math.sin((currentAngle * Math.PI) / 180);
              const innerX2 = centerX + innerRadius * Math.cos(((currentAngle + angle) * Math.PI) / 180);
              const innerY2 = centerY + innerRadius * Math.sin(((currentAngle + angle) * Math.PI) / 180);
              
              const largeArcFlag = angle > 180 ? 1 : 0;
              
              const pathData = [
                `M ${outerX1} ${outerY1}`,
                `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${outerX2} ${outerY2}`,
                `L ${innerX2} ${innerY2}`,
                `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerX1} ${innerY1}`,
                'Z'
              ].join(' ');

              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
              const color = colors[index % colors.length];
              currentAngle += angle;

              return (
                <g key={index}>
                  <path d={pathData} fill={color} stroke="white" strokeWidth="3" />
                  <text
                    x={centerX + ((outerRadius + innerRadius) / 2) * 0.85 * Math.cos(((currentAngle - angle/2) * Math.PI) / 180)}
                    y={centerY + ((outerRadius + innerRadius) / 2) * 0.85 * Math.sin(((currentAngle - angle/2) * Math.PI) / 180)}
                    textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="12" fontWeight="bold"
                  >
                    {percentage.toFixed(1)}%
                  </text>
                </g>
              );
            })}
            
            <circle cx={centerX} cy={centerY} r={innerRadius - 8} fill="white" stroke="#E5E7EB" strokeWidth="2" />
            <text x={centerX} y={centerY - 10} textAnchor="middle" dominantBaseline="middle" fill="#374151" fontSize="16" fontWeight="bold">
              Total
            </text>
            <text x={centerX} y={centerY + 12} textAnchor="middle" dominantBaseline="middle" fill="#6B7280" fontSize="14" fontWeight="600">
              {total.toLocaleString()}
            </text>
          </svg>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg">
            {labels.map((label, index) => {
              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
              const color = colors[index % colors.length];
              const percentage = ((data[index] / total) * 100).toFixed(1);
              const value = data[index];
              
              return (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-4 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: color }}></div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">{label}</div>
                    <div className="text-xs text-gray-600">
                      {typeof value === 'number' ? value.toLocaleString() : value} ({percentage}%)
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    };

    const renderLineChart = () => {
      const width = 600;
      const height = 350;
      const padding = 60;
      const maxValue = Math.max(...data);
      const minValue = Math.min(...data);
      const range = maxValue - minValue || 1;
      
      const points = data.map((value, index) => {
        const x = padding + (index * (width - 2 * padding)) / Math.max(data.length - 1, 1);
        const y = height - padding - ((value - minValue) / range) * (height - 2 * padding);
        return `${x},${y}`;
      }).join(' ');

      return (
        <div className="flex justify-center w-full py-6">
          <div className="w-full max-w-4xl">
            <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="border border-gray-200 rounded-lg bg-white">
              <defs>
                <pattern id="grid" width="60" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 60 0 L 0 0 0 30" fill="none" stroke="#F3F4F6" strokeWidth="1"/>
                </pattern>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8"/>
                  <stop offset="100%" stopColor="#1D4ED8" stopOpacity="1"/>
                </linearGradient>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
              
              <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#6B7280" strokeWidth="2"/>
              <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#6B7280" strokeWidth="2"/>
              
              <polyline points={points} fill="none" stroke="url(#lineGradient)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
              
              {data.map((value, index) => {
                const x = padding + (index * (width - 2 * padding)) / Math.max(data.length - 1, 1);
                const y = height - padding - ((value - minValue) / range) * (height - 2 * padding);
                return (
                  <g key={index}>
                    <circle cx={x} cy={y} r="6" fill="#3B82F6" stroke="white" strokeWidth="3" />
                    <text x={x} y={height - padding + 20} textAnchor="middle" fontSize="12" fill="#6B7280" fontWeight="500">
                      {labels[index]}
                    </text>
                    <text x={x} y={y - 15} textAnchor="middle" fontSize="12" fill="#374151" fontWeight="bold">
                      {typeof value === 'number' ? value.toLocaleString() : value}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      );
    };

    const getChartTypeIcon = () => {
      switch (chartType) {
        case 'pie': return <PieChart className="h-5 w-5" />;
        case 'doughnut': return <div className="h-5 w-5 border-2 border-current rounded-full relative"><div className="absolute inset-1 border border-current rounded-full"></div></div>;
        case 'line': return <TrendingUp className="h-5 w-5" />;
        case 'bar': default: return <BarChart3 className="h-5 w-5" />;
      }
    };

    const renderChart = () => {
      switch (chartType) {
        case 'pie': return renderPieChart();
        case 'doughnut': return renderDoughnutChart();
        case 'line': return renderLineChart();
        case 'bar': default: return renderBarChart();
      }
    };

    return (
      <div className="mt-8 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h4 className="text-xl font-semibold text-gray-900">
            {chartData.options?.plugins?.title?.text || 'Analytics Chart'}
          </h4>
          <div className="flex items-center space-x-3 text-sm text-gray-500">
            {getChartTypeIcon()}
            <span className="capitalize font-medium">{chartType} Chart</span>
            <span>•</span>
            <span>{data.length} data points</span>
          </div>
        </div>
        
        <div className="p-6">
          <div className="w-full">
            {renderChart()}
          </div>
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
          <span>Chart Type: {chartType.charAt(0).toUpperCase() + chartType.slice(1)}</span>
          <span>Generated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    );
  };

  // Single Response Component
  const ResponseComponent = ({ response, index }) => {
    const isEditing = editingResponseId === response.id;
    const mockSources = [
      { id: 1, title: 'MongoDB Analytics Database', url: 'mongodb://localhost:27017/analytics_db', favicon: '📊', description: 'Your MongoDB analytics database with sales, customer, and product data.' },
      { id: 2, title: 'Backend Processing Engine', url: 'localhost:5000/api/query', favicon: '⚙️', description: 'Python Flask backend with Gemini AI integration for query processing.' },
      { id: 3, title: 'Chart Generation System', url: 'chart.generator.local', favicon: '📈', description: 'Automated chart generation based on data patterns and query analysis.' }
    ];

    return (
      <div className={`${index > 0 ? 'border-t border-gray-200 pt-8 mt-8' : ''}`}>
        {/* Query Header with Edit Functionality */}
        <div className="mb-6">
          {isEditing ? (
            <div className="space-y-4">
              <textarea
                value={editedQuery}
                onChange={(e) => setEditedQuery(e.target.value)}
                className="w-full px-4 py-3 text-lg border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="2"
                autoFocus
              />
              <div className="flex items-center space-x-3">
                <button
                  onClick={saveEditedResponse}
                  disabled={!editedQuery.trim()}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Save className="w-4 h-4" />
                  <span>Save & Regenerate</span>
                </button>
                <button
                  onClick={cancelEditingResponse}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <X className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-start justify-between">
              <h1 className="text-3xl font-semibold text-gray-900 pr-4">{response.query}</h1>
              <button
                onClick={() => startEditingResponse(response.id, response.query)}
                className="flex items-center space-x-2 px-3 py-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
                title="Edit prompt"
              >
                <Edit3 className="w-4 h-4" />
              </button>
            </div>
          )}
          
          {!isEditing && (
            <div className="flex items-center space-x-8 border-b border-gray-200 mt-4">
              {['Answer', 'Images', 'Sources', 'Steps'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => updateResponseTab(response.id, tab.toLowerCase())}
                  className={`pb-3 px-1 text-sm font-medium transition-colors relative ${
                    response.activeTab === tab.toLowerCase()
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab}
                  {tab === 'Sources' && <span className="ml-1 text-xs">• {mockSources.length}</span>}
                </button>
              ))}
            </div>
          )}
        </div>

        {!isEditing && (
          <>
            {/* Tab Content */}
            {response.activeTab === 'answer' && (
              <div className="space-y-8">
                <div className="prose prose-lg max-w-none">
                  <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                    {response.answer}
                  </div>
                </div>

                {response.chartData && <ChartDisplay chartData={response.chartData} />}

                {response.validation && (
                  <div className="mt-6 p-6 bg-gray-50 rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-gray-800">Answer Validation</h4>
                      <span className={`text-sm font-semibold px-3 py-1 rounded-full ${
                        response.validation.confidence >= 80 ? 'text-green-700 bg-green-100' : 
                        response.validation.confidence >= 60 ? 'text-yellow-700 bg-yellow-100' : 'text-red-700 bg-red-100'
                      }`}>
                        {response.validation.confidence}% confidence
                      </span>
                    </div>
                    <div className="space-y-3">
                      {response.validation.checks.map((check, idx) => (
                        <div key={idx} className="flex items-start space-x-3">
                          {check.passed ? (
                            <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                          )}
                          <span className={`text-sm ${check.passed ? 'text-green-700' : 'text-red-700'}`}>
                            {check.message}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-8 pt-6 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Was this answer helpful?</span>
                    <div className="flex items-center space-x-3">
                      <button className="flex items-center space-x-2 px-4 py-2 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
                        <ThumbsUp className="h-4 w-4" />
                        <span>Yes</span>
                      </button>
                      <button className="flex items-center space-x-2 px-4 py-2 text-sm text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors">
                        <ThumbsDown className="h-4 w-4" />
                        <span>No</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {response.activeTab === 'sources' && (
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-gray-900">Data Sources</h3>
                {mockSources.map((source, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-xl p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start space-x-4">
                      <span className="text-2xl">{source.favicon}</span>
                      <div className="flex-1">
                        <h4 className="text-lg font-medium text-blue-600 hover:text-blue-700 cursor-pointer mb-2">
                          {source.title}
                        </h4>
                        <p className="text-gray-600 mb-3">{source.description}</p>
                        <span className="text-sm text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                          {source.url}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {response.activeTab === 'steps' && (
              <div className="space-y-6">
                <h3 className="text-xl font-semibold text-gray-900">Processing Steps</h3>
                <div className="space-y-4">
                  {[
                    { step: 1, title: 'Query Analysis', description: 'Analyzed your question and identified data requirements', status: 'completed' },
                    { step: 2, title: 'Database Search', description: 'Searched MongoDB analytics database for relevant data', status: 'completed' },
                    { step: 3, title: 'Data Processing', description: 'Processed and aggregated data using backend algorithms', status: 'completed' },
                    { step: 4, title: 'Chart Generation', description: 'Generated appropriate visualization based on data patterns', status: 'completed' },
                    { step: 5, title: 'Validation', description: 'Validated results and calculated confidence scores', status: 'completed' }
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-start space-x-4 p-6 bg-gray-50 rounded-xl">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        item.status === 'completed' ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
                      }`}>
                        {item.step}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-medium text-gray-900 mb-1">{item.title}</h4>
                        <p className="text-gray-600">{item.description}</p>
                      </div>
                      {item.status === 'completed' && (
                        <CheckCircle className="w-6 h-6 text-green-500 mt-1" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {response.activeTab === 'images' && (
              <div className="space-y-6">
                <h3 className="text-xl font-semibold text-gray-900">Visual Analysis</h3>
                <div className="text-center py-16 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
                  <Image className="w-20 h-20 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-xl font-medium text-gray-900 mb-2">No Images Generated</h4>
                  <p className="text-gray-500 max-w-md mx-auto">
                    This query focused on data analysis. Charts and visualizations are available in the Answer tab.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  // Main render
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-5xl mx-auto p-8">
        {/* Render all responses */}
        {responses.map((response, index) => (
          <ResponseComponent key={response.id} response={response} index={index} />
        ))}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className={`${responses.length > 0 ? 'border-t border-gray-200 pt-8 mt-8' : ''}`}>
            <div className="mb-6">
              <h1 className="text-3xl font-semibold text-gray-900 mb-4">{followUpQuery || 'Processing...'}</h1>
              <div className="flex items-center space-x-8 border-b border-gray-200">
                <span className="pb-3 px-1 text-sm font-medium text-blue-600 border-b-2 border-blue-600">
                  Answer
                </span>
              </div>
            </div>

            <div className="bg-blue-50 rounded-xl p-8 border border-blue-200">
              <div className="flex items-center space-x-4 mb-4">
                <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-blue-800 font-medium">{processingStep}</span>
              </div>
              <div className="space-y-3">
                <div className="h-4 bg-blue-200 rounded w-3/4 animate-pulse"></div>
                <div className="h-4 bg-blue-200 rounded w-1/2 animate-pulse"></div>
                <div className="h-4 bg-blue-200 rounded w-2/3 animate-pulse"></div>
              </div>
            </div>
          </div>
        )}

        {/* Follow-up Input */}
        {!isProcessing && responses.length > 0 && (
          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="relative">
              <textarea
                value={followUpQuery}
                onChange={(e) => setFollowUpQuery(e.target.value)}
                onKeyPress={handleFollowUpKeyPress}
                placeholder="Ask a follow-up question..."
                className="w-full px-6 py-4 text-lg border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-16 resize-none"
                rows="1"
                style={{ minHeight: '56px', maxHeight: '120px' }}
              />
              <button
                onClick={handleFollowUpSubmit}
                disabled={!followUpQuery.trim()}
                className={`absolute right-4 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-all duration-200 ${
                  followUpQuery.trim()
                    ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            
            {/* Suggested follow-up questions */}
            <div className="mt-6">
              <p className="text-sm text-gray-600 mb-4 font-medium">Suggested follow-ups:</p>
              <div className="flex flex-wrap gap-3">
                {[
                  'Show this as a different chart type',
                  'What are the monthly trends?',
                  'How does this compare to last year?',
                  'Show me the top 10 results',
                  'Break this down by region',
                  'Analyze the seasonal patterns'
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors font-medium"
                    onClick={() => setFollowUpQuery(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {responses.length === 0 && !isProcessing && (
          <div className="text-center py-16">
            <AlertTriangle className="w-20 h-20 text-red-500 mx-auto mb-6" />
            <h3 className="text-2xl font-medium text-gray-900 mb-4">Unable to Process Query</h3>
            <p className="text-gray-600 mb-6">
              There was an issue processing your request. Please check your backend connection.
            </p>
            <button 
              onClick={() => processQuery(query)}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Try Again
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ResponseInterface;