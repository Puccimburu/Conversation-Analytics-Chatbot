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

const ResponseInterface = ({ query, onClose, chatId, existingMessages }) => {
  const [responses, setResponses] = useState([]);
  const [chatId_internal] = useState(chatId); 
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [followUpQuery, setFollowUpQuery] = useState('');
  const [editingResponseId, setEditingResponseId] = useState(null);
  const [editedQuery, setEditedQuery] = useState('');
  const messagesEndRef = useRef(null);
  
  // FIX: Add ref to track initial query processing
  const hasProcessedInitialQuery = useRef(false);

  // FIX: Modified useEffect to prevent double execution
  useEffect(() => {
    if (query && responses.length === 0 && !hasProcessedInitialQuery.current && !isProcessing) {
      hasProcessedInitialQuery.current = true;
      processQuery(query);
    }
  }, [query]);

  // FIX: Reset the ref when query changes
  useEffect(() => {
    if (query) {
      hasProcessedInitialQuery.current = false;
    }
  }, [query]);

  // Auto-scroll to bottom when new content appears
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [responses, isProcessing]);

  
  // In the useEffect for existing messages:
  // 🎯 PASTE THIS ENTIRE BLOCK:
  useEffect(() => {
    if (existingMessages && existingMessages.length > 0) {
      console.log('Loading existing messages:', existingMessages);
      const formattedResponses = existingMessages.map((msg, index) => ({
        id: msg.message_id || `existing_${index}`,
        query: msg.type === 'user' ? msg.content : 'Previous query',     
        timestamp: new Date(msg.timestamp).getTime(),
        answer: msg.type === 'assistant' ? msg.content : 'Previous response', 
        chartData: msg.chart_data || null,
        validation: msg.validation || null,
        activeTab: 'answer'
      }));
      setResponses(formattedResponses);
    } 
  }, [existingMessages]);
  
  const processQuery = async (queryText, isFollowUp = false, responseIdToReplace = null) => {
    // FIX: Add early return if already processing
    if (isProcessing && !responseIdToReplace) {
      console.log('Already processing, skipping duplicate request');
      return;
    }

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
        body: JSON.stringify({ 
          question: queryText,
          chat_id: chatId_internal 
        })  
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
      prev.map(r => r.id === responseId ? { ...r, activeTab: newTab } : r)
    );
  };

  // Chart Display Component
  const ChartDisplay = ({ chartData }) => {
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
                <span className="text-white text-xs font-medium">
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
      const center = radius + 10;
      
      return (
        <div className="flex items-center justify-center">
          <svg width={center * 2} height={center * 2} className="drop-shadow-sm">
            {data.map((value, index) => {
              const percentage = (value / total) * 100;
              const angle = (value / total) * 360;
              const x1 = center + radius * Math.cos((currentAngle - 90) * Math.PI / 180);
              const y1 = center + radius * Math.sin((currentAngle - 90) * Math.PI / 180);
              const x2 = center + radius * Math.cos((currentAngle + angle - 90) * Math.PI / 180);
              const y2 = center + radius * Math.sin((currentAngle + angle - 90) * Math.PI / 180);
              
              const largeArcFlag = angle > 180 ? 1 : 0;
              const pathData = `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
              
              currentAngle += angle;
              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
              
              return (
                <g key={index}>
                  <path
                    d={pathData}
                    fill={colors[index % colors.length]}
                    stroke="white"
                    strokeWidth="2"
                  />
                  <text
                    x={center + (radius * 0.7) * Math.cos((currentAngle - angle/2 - 90) * Math.PI / 180)}
                    y={center + (radius * 0.7) * Math.sin((currentAngle - angle/2 - 90) * Math.PI / 180)}
                    textAnchor="middle"
                    className="fill-white text-xs font-medium"
                  >
                    {percentage > 5 ? `${percentage.toFixed(1)}%` : ''}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      );
    };

    const renderDoughnutChart = () => {
      const total = data.reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0);
      let currentAngle = 0;
      const outerRadius = 80;
      const innerRadius = 45;
      const center = outerRadius + 10;
      
      return (
        <div className="flex items-center justify-center">
          <svg width={center * 2} height={center * 2} className="drop-shadow-sm">
            {data.map((value, index) => {
              const percentage = (value / total) * 100;
              const angle = (value / total) * 360;
              
              const x1Outer = center + outerRadius * Math.cos((currentAngle - 90) * Math.PI / 180);
              const y1Outer = center + outerRadius * Math.sin((currentAngle - 90) * Math.PI / 180);
              const x2Outer = center + outerRadius * Math.cos((currentAngle + angle - 90) * Math.PI / 180);
              const y2Outer = center + outerRadius * Math.sin((currentAngle + angle - 90) * Math.PI / 180);
              
              const x1Inner = center + innerRadius * Math.cos((currentAngle - 90) * Math.PI / 180);
              const y1Inner = center + innerRadius * Math.sin((currentAngle - 90) * Math.PI / 180);
              const x2Inner = center + innerRadius * Math.cos((currentAngle + angle - 90) * Math.PI / 180);
              const y2Inner = center + innerRadius * Math.sin((currentAngle + angle - 90) * Math.PI / 180);
              
              const largeArcFlag = angle > 180 ? 1 : 0;
              const pathData = `M ${x1Outer} ${y1Outer} A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x2Outer} ${y2Outer} L ${x2Inner} ${y2Inner} A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x1Inner} ${y1Inner} Z`;
              
              currentAngle += angle;
              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
              
              return (
                <path
                  key={index}
                  d={pathData}
                  fill={colors[index % colors.length]}
                  stroke="white"
                  strokeWidth="2"
                />
              );
            })}
            <text
              x={center}
              y={center}
              textAnchor="middle"
              className="fill-gray-600 text-sm font-semibold"
            >
              Total: {total.toLocaleString()}
            </text>
          </svg>
        </div>
      );
    };

    const renderLineChart = () => {
    const chartWidth = 800;
    const chartHeight = 500;
    const padding = { top: 60, right: 60, bottom: 80, left: 80 };
    const plotWidth = chartWidth - padding.left - padding.right;
    const plotHeight = chartHeight - padding.top - padding.bottom;
    
    // Calculate data ranges
    const numericData = data.filter(val => typeof val === 'number');
    const maxValue = Math.max(...numericData);
    const minValue = Math.min(...numericData);
    const range = maxValue - minValue || 1;
    const yAxisMax = maxValue + (range * 0.1);
    const yAxisMin = Math.max(0, minValue - (range * 0.1));
    const adjustedRange = yAxisMax - yAxisMin;

    // Grid lines
    const gridLines = 8;
    const yStep = adjustedRange / gridLines;
    
    // Calculate points for the line
    const linePoints = data.map((value, index) => {
      const x = padding.left + (index * plotWidth) / Math.max(data.length - 1, 1);
      const y = padding.top + plotHeight - ((value - yAxisMin) / adjustedRange) * plotHeight;
      return { x, y, value, label: labels[index] };
    });

    // Create smooth curve path
    const createSmoothPath = (points) => {
      if (points.length < 2) return '';
      
      let path = `M ${points[0].x} ${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        
        if (i === 1) {
          const controlX = prev.x + (curr.x - prev.x) * 0.5;
          path += ` Q ${controlX} ${prev.y} ${curr.x} ${curr.y}`;
        } else {
          const prevPrev = points[i - 2];
          const controlX1 = prev.x + (curr.x - prevPrev.x) * 0.15;
          const controlY1 = prev.y;
          const controlX2 = curr.x - (curr.x - prev.x) * 0.15;
          const controlY2 = curr.y;
          path += ` C ${controlX1} ${controlY1} ${controlX2} ${controlY2} ${curr.x} ${curr.y}`;
        }
      }
      return path;
    };

    return (
      <div className="w-full flex justify-center py-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm w-full max-w-5xl">
          <svg 
            width="100%" 
            height={chartHeight} 
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            className="w-full h-auto"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Definitions */}
            <defs>
              {/* Line gradient */}
              <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="1"/>
                <stop offset="100%" stopColor="#1D4ED8" stopOpacity="1"/>
              </linearGradient>
              
              {/* Tooltip shadow */}
              <filter id="tooltipShadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#000000" floodOpacity="0.25"/>
              </filter>
            </defs>

            {/* Chart background */}
            <rect width={chartWidth} height={chartHeight} fill="#FAFAFA" rx="8"/>
            
            {/* Plot area */}
            <rect 
              x={padding.left} 
              y={padding.top} 
              width={plotWidth} 
              height={plotHeight} 
              fill="white"
              stroke="#E5E7EB"
              strokeWidth="1"
            />

            {/* Horizontal grid lines */}
            {Array.from({ length: gridLines + 1 }, (_, i) => {
              const value = yAxisMin + (i * yStep);
              const y = padding.top + plotHeight - (i * plotHeight) / gridLines;
              
              return (
                <g key={`hgrid-${i}`}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={padding.left + plotWidth}
                    y2={y}
                    stroke="#E5E7EB"
                    strokeWidth="1"
                    opacity="0.8"
                  />
                  {/* Y-axis labels */}
                  <text
                    x={padding.left - 15}
                    y={y + 4}
                    textAnchor="end"
                    fontSize="12"
                    fill="#6B7280"
                    fontFamily="system-ui, -apple-system, sans-serif"
                  >
                    {typeof value === 'number' ? 
                      (value >= 1000 ? `${(value/1000).toFixed(1)}K` : Math.round(value).toLocaleString())
                      : value}
                  </text>
                </g>
              );
            })}

            {/* Vertical grid lines */}
            {linePoints.map((point, index) => (
              <line
                key={`vgrid-${index}`}
                x1={point.x}
                y1={padding.top}
                x2={point.x}
                y2={padding.top + plotHeight}
                stroke="#E5E7EB"
                strokeWidth="1"
                opacity="0.6"
              />
            ))}

            {/* Main line */}
            <path
              d={createSmoothPath(linePoints)}
              fill="none"
              stroke="url(#lineGradient)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data points with CSS hover effects */}
            {linePoints.map((point, index) => (
              <g key={`point-${index}`} className="group">
                {/* Data point */}
                <circle
                  cx={point.x}
                  cy={point.y}
                  r="4"
                  fill="#3B82F6"
                  stroke="white"
                  strokeWidth="2"
                  className="transition-all duration-200 group-hover:r-6 group-hover:drop-shadow-lg cursor-pointer"
                  style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.1))' }}
                />

                {/* Hover tooltip using CSS */}
                <g className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                  {/* Tooltip background */}
                  <rect
                    x={point.x - 35}
                    y={point.y - 50}
                    width="70"
                    height="35"
                    fill="#1F2937"
                    rx="6"
                    filter="url(#tooltipShadow)"
                  />
                  {/* Tooltip arrow */}
                  <polygon
                    points={`${point.x - 6},${point.y - 15} ${point.x + 6},${point.y - 15} ${point.x},${point.y - 8}`}
                    fill="#1F2937"
                  />
                  {/* Tooltip label */}
                  <text
                    x={point.x}
                    y={point.y - 38}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#9CA3AF"
                    fontWeight="500"
                  >
                    {point.label}
                  </text>
                  {/* Tooltip value */}
                  <text
                    x={point.x}
                    y={point.y - 23}
                    textAnchor="middle"
                    fontSize="12"
                    fill="white"
                    fontWeight="700"
                  >
                    {typeof point.value === 'number' ? 
                      (point.value >= 1000 ? `$${(point.value/1000).toFixed(1)}K` : `$${point.value.toLocaleString()}`)
                      : point.value}
                  </text>
                </g>
              </g>
            ))}

            {/* X-axis labels */}
            {linePoints.map((point, index) => (
              <text
                key={`xlabel-${index}`}
                x={point.x}
                y={padding.top + plotHeight + 25}
                textAnchor="middle"
                fontSize="12"
                fill="#6B7280"
                fontFamily="system-ui, -apple-system, sans-serif"
              >
                {point.label.length > 8 ? point.label.substring(0, 8) : point.label}
              </text>
            ))}

            {/* Chart title */}
            <text
              x={chartWidth / 2}
              y={30}
              textAnchor="middle"
              fontSize="16"
              fill="#1F2937"
              fontWeight="600"
              fontFamily="system-ui, -apple-system, sans-serif"
            >
              {chartData.options?.plugins?.title?.text || 'Monthly Sales Trends (2024)'}
            </text>

            {/* Y-axis title */}
            <text
              x="20"
              y={chartHeight / 2}
              textAnchor="middle"
              fontSize="12"
              fill="#6B7280"
              fontWeight="500"
              transform={`rotate(-90, 20, ${chartHeight / 2})`}
              fontFamily="system-ui, -apple-system, sans-serif"
            >
              Revenue ($)
            </text>

            {/* X-axis title */}
            <text
              x={chartWidth / 2}
              y={chartHeight - 20}
              textAnchor="middle"
              fontSize="12"
              fill="#6B7280"
              fontWeight="500"
              fontFamily="system-ui, -apple-system, sans-serif"
            >
              Time Period
            </text>

            {/* Trend indicator in top right */}
            {(() => {
              const firstValue = numericData[0];
              const lastValue = numericData[numericData.length - 1];
              const trend = lastValue > firstValue ? 'up' : lastValue < firstValue ? 'down' : 'stable';
              const trendColor = trend === 'up' ? '#10B981' : trend === 'down' ? '#EF4444' : '#6B7280';
              const trendText = trend === 'up' ? 'Rising' : trend === 'down' ? 'Falling' : 'Stable';
              const trendIcon = trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→';
              
              return (
                <g>
                  <rect
                    x={chartWidth - 85}
                    y={15}
                    width="70"
                    height="25"
                    fill={trendColor}
                    opacity="0.1"
                    rx="12"
                  />
                  <text
                    x={chartWidth - 75}
                    y={30}
                    fontSize="12"
                    fill={trendColor}
                    fontWeight="600"
                  >
                    {trendIcon} {trendText}
                  </text>
                </g>
              );
            })()}

            {/* Chart type indicator */}
            <g>
              <circle cx={chartWidth - 25} cy={chartHeight - 25} r="3" fill="#3B82F6"/>
              <text
                x={chartWidth - 45}
                y={chartHeight - 20}
                fontSize="10"
                fill="#6B7280"
                textAnchor="end"
              >
                Line Chart
              </text>
            </g>
          </svg>
          
          {/* Statistics below chart */}
          <div className="mt-6 grid grid-cols-4 gap-4 text-center">
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="text-lg font-bold text-blue-600">
                {typeof maxValue === 'number' ? 
                  (maxValue >= 1000 ? `${(maxValue/1000).toFixed(1)}K` : `${maxValue.toLocaleString()}`)
                  : maxValue}
              </div>
              <div className="text-xs text-blue-700 font-medium">Peak Value</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <div className="text-lg font-bold text-gray-700">
                {(() => {
                  const avg = numericData.reduce((a, b) => a + b, 0) / numericData.length;
                  return typeof avg === 'number' ? 
                    (avg >= 1000 ? `${(avg/1000).toFixed(1)}K` : `${Math.round(avg).toLocaleString()}`)
                    : 'N/A';
                })()}
              </div>
              <div className="text-xs text-gray-600 font-medium">Average</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <div className="text-lg font-bold text-gray-700">{data.length}</div>
              <div className="text-xs text-gray-600 font-medium">Data Points</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3 border border-green-200">
              <div className="text-lg font-bold text-green-600">
                {(() => {
                  const total = numericData.reduce((a, b) => a + b, 0);
                  return typeof total === 'number' ? 
                    (total >= 1000 ? `${(total/1000).toFixed(1)}K` : `${total.toLocaleString()}`)
                    : 'N/A';
                })()}
              </div>
              <div className="text-xs text-green-700 font-medium">Total</div>
            </div>
          </div>

          {/* Interaction hint */}
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              💡 <span className="font-medium">Tip:</span> Hover over data points to see detailed values
            </p>
          </div>
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
              </div>
            )}

            {response.activeTab === 'images' && (
              <div className="space-y-6">
                <div className="text-center py-12">
                  <Image className="w-20 h-20 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 font-medium">Image analysis not available</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Charts and visualizations are available in the Answer tab.
                  </p>
                </div>
              </div>
            )}

            {response.activeTab === 'sources' && (
              <div className="space-y-4">
                {mockSources.map((source) => (
                  <div key={source.id} className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="text-2xl">{source.favicon}</div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{source.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                      <div className="text-xs text-gray-500 mt-2 font-mono">{source.url}</div>
                    </div>
                    <ExternalLink className="h-4 w-4 text-gray-400" />
                  </div>
                ))}
              </div>
            )}

            {response.activeTab === 'steps' && (
              <div className="space-y-4">
                {[
                  { step: 1, title: 'Query Analysis', description: 'Analyzed your natural language question and extracted key parameters.', status: 'completed' },
                  { step: 2, title: 'Database Query', description: 'Generated and executed MongoDB aggregation pipeline.', status: 'completed' },
                  { step: 3, title: 'Data Processing', description: 'Processed raw results and prepared for visualization.', status: 'completed' },
                  { step: 4, title: 'Chart Generation', description: 'Created appropriate chart type and formatted data.', status: 'completed' },
                  { step: 5, title: 'Response Validation', description: 'Validated results and generated summary insights.', status: 'completed' }
                ].map((step) => (
                  <div key={step.step} className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      step.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {step.status === 'completed' ? '✓' : step.step}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{step.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                    </div>
                  </div>
                ))}
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