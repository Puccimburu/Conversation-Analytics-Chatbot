// Complete and Corrected ResponseInterface.jsx with fixed table rendering
// File: frontend/src/components/chat/ResponseInterface.jsx

import React, { useState, useRef, useEffect } from 'react';
import { 
  Send,
  Edit3, Save, X, Copy, RefreshCw, ChevronDown, ChevronUp,
  BarChart3, PieChart, TrendingUp, Table as TableIcon,
  Download, ExternalLink, Zap, Activity, Target
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const ResponseInterface = ({ 
  responses = [], 
  onEditQuery = () => {}, 
  isLoading = false,
  chatId = null,
  existingMessages = [],
  chatTitle = '',
  onClose = () => {},
  query = null // Initial query for new chats
}) => {
  const [editingResponseId, setEditingResponseId] = useState(null);
  const [expandedResponses, setExpandedResponses] = useState(new Set());
  const [activeTab, setActiveTab] = useState('Answer');
  const [currentQuery, setCurrentQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chatResponses, setChatResponses] = useState([]);
  const textareaRef = useRef(null);
  const queryInputRef = useRef(null);

  // Initialize chat responses from props
  useEffect(() => {
    if (existingMessages && existingMessages.length > 0) {
      // Convert existing messages to response format
      const convertedResponses = existingMessages
        .filter(msg => msg.role === 'assistant')
        .map((msg, index) => ({
          id: `msg_${index}`,
          query: existingMessages[index * 2]?.content || 'Previous query', // Get corresponding user message
          content: msg.content,
          chart_data: msg.chart_data,
          insights: msg.insights,
          recommendations: msg.recommendations,
          timestamp: msg.timestamp
        }));
      setChatResponses(convertedResponses);
    }
    
    // Handle initial query for new chats
    if (query && chatId) {
      handleQuerySubmission(query);
    }
  }, [existingMessages, query, chatId]);

  // Query submission function
  const handleQuerySubmission = async (queryText) => {
    if (!queryText.trim() || isSubmitting) return;

    setIsSubmitting(true);
    
    // Add user message to chat immediately
    const userMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString()
    };

    // Add loading response
    const loadingResponse = {
      id: `loading_${Date.now()}`,
      query: queryText,
      content: 'Processing your request...',
      isLoading: true
    };

    setChatResponses(prev => [...prev, loadingResponse]);

    try {
      // Make API call to backend
      const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: queryText,
          chat_id: chatId
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          // Replace loading response with actual result
          const actualResponse = {
            id: `response_${Date.now()}`,
            query: queryText,
            content: result.summary || result.answer || 'Analysis completed',
            chart_data: result.chart_data || result.visualization,
            insights: result.insights,
            recommendations: result.recommendations,
            processing_mode: result.processing_mode,
            execution_time: result.execution_time
          };

          setChatResponses(prev => 
            prev.map(r => r.id === loadingResponse.id ? actualResponse : r)
          );
        } else {
          throw new Error(result.error || 'Query processing failed');
        }
      } else {
        throw new Error(`Server error: ${response.status}`);
      }
    } catch (error) {
      console.error('Query submission error:', error);
      
      // Replace loading response with error
      const errorResponse = {
        id: `error_${Date.now()}`,
        query: queryText,
        content: `Error: ${error.message}`,
        isError: true
      };

      setChatResponses(prev => 
        prev.map(r => r.id === loadingResponse.id ? errorResponse : r)
      );
    } finally {
      setIsSubmitting(false);
      setCurrentQuery(''); // Clear input
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    handleQuerySubmission(currentQuery);
  };

  // Handle enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuerySubmission(currentQuery);
    }
  };

  useEffect(() => {
    if (editingResponseId && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(
        textareaRef.current.value.length,
        textareaRef.current.value.length
      );
    }
  }, [editingResponseId]);

  const handleEdit = (responseId) => {
    setEditingResponseId(responseId);
  };

  const handleSaveEdit = (responseId, newQuery) => {
    onEditQuery(responseId, newQuery);
    setEditingResponseId(null);
  };

  const handleCancelEdit = () => {
    setEditingResponseId(null);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const toggleExpanded = (responseId) => {
    setExpandedResponses(prev => {
      const newSet = new Set(prev);
      if (newSet.has(responseId)) {
        newSet.delete(responseId);
      } else {
        newSet.add(responseId);
      }
      return newSet;
    });
  };

  const handleTabChange = (responseId, newTab) => {
    setActiveTab(newTab);
  };

  // Enhanced formatTableValue function
  const formatTableValue = (value, type) => {
    // Handle null/undefined values
    if (value === null || value === undefined || value === '') {
      return '-';
    }
    
    // Handle ObjectId or complex objects
    if (typeof value === 'object' && value !== null) {
      if (value.toString && typeof value.toString === 'function') {
        value = value.toString();
      } else {
        value = JSON.stringify(value);
      }
    }
    
    switch (type) {
      case 'number':
        return typeof value === 'number' ? value.toLocaleString() : value;
      case 'currency':
        return typeof value === 'number' ? `$${value.toLocaleString()}` : value;
      case 'percentage':
        return typeof value === 'number' ? `${value.toFixed(1)}%` : value;
      case 'date':
        try {
          return new Date(value).toLocaleDateString();
        } catch {
          return value;
        }
      case 'boolean':
        return value ? 'Yes' : 'No';
      default:
        return String(value);
    }
  };

  // Fixed renderDataTable function
  const renderDataTable = (data, columns) => {
    console.log('🔍 Table Debug - Data:', data?.slice(0, 2)); // Debug first 2 rows
    console.log('🔍 Table Debug - Columns:', columns);
    
    if (!data || data.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <div className="text-6xl mb-4">📊</div>
          <p className="font-medium">No data available</p>
        </div>
      );
    }

    return (
      <div className="w-full">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column, index) => (
                  <th
                    key={column.key || column.field || index} // Support both key and field
                    className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      column.align === 'right' ? 'text-right' : 
                      column.align === 'center' ? 'text-center' : 'text-left'
                    }`}
                    style={{ width: column.width || 'auto' }}
                  >
                    {column.label || column.header || column.field || 'Column'}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((row, rowIndex) => (
                <tr 
                  key={rowIndex} 
                  className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                >
                  {columns.map((column, colIndex) => {
                    // Try multiple ways to access the data
                    const columnKey = column.key || column.field;
                    let cellValue = row[columnKey];
                    
                    // If no direct match, try alternative access patterns
                    if (cellValue === undefined || cellValue === null) {
                      // Try case variations
                      const altKeys = [
                        columnKey?.toLowerCase(),
                        columnKey?.toUpperCase(),
                        columnKey?.replace(/_/g, ''),
                        columnKey?.replace(/([A-Z])/g, '_$1').toLowerCase(),
                        // For users table common fields
                        columnKey === 'userId' ? '_id' : null,
                        columnKey === 'emailId' ? 'email' : null,
                        columnKey === 'name' ? 'firstName' : null,
                      ].filter(Boolean);
                      
                      for (const altKey of altKeys) {
                        if (row[altKey] !== undefined && row[altKey] !== null) {
                          cellValue = row[altKey];
                          break;
                        }
                      }
                    }
                    
                    return (
                      <td
                        key={colIndex}
                        className={`px-6 py-4 whitespace-nowrap text-sm ${
                          column.align === 'right' ? 'text-right text-gray-900' : 
                          column.align === 'center' ? 'text-center text-gray-900' : 'text-left text-gray-900'
                        }`}
                      >
                        {formatTableValue(cellValue, column.type)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Table summary */}
        <div className="mt-4 px-6 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>Showing {data.length} records</span>
            <span>
              {data.length > 0 && columns.some(col => col.type === 'number') && (
                <>
                  Total: {columns
                    .filter(col => col.type === 'number')
                    .map(col => {
                      const columnKey = col.key || col.field;
                      const sum = data.reduce((acc, row) => {
                        const val = parseFloat(row[columnKey]) || 0;
                        return acc + val;
                      }, 0);
                      return `${col.label || col.header}: ${sum.toLocaleString()}`;
                    })
                    .join(', ')
                  }
                </>
              )}
            </span>
          </div>
        </div>
      </div>
    );
  };

  // Chart Display Component
  const ChartDisplay = ({ chartData }) => {
    if (!chartData) {
      return (
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">📊</div>
          <p>No chart data available</p>
        </div>
      );
    }

    // Handle both direct data and nested data structures
    let chartDataObj = {};
    if (chartData.data) {
      chartDataObj = chartData.data;
    } else if (chartData.labels || chartData.datasets) {
      chartDataObj = chartData;
    } else if (chartData.htmlContent || chartData.tableData) {
      // Special handling for HTML and table formats
      chartDataObj = { labels: [], datasets: [] };
    } else {
      return (
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">⚠️</div>
          <p>Invalid chart data format</p>
        </div>
      );
    }

    // Defensive data extraction with fallbacks
    const labels = chartDataObj.labels || [];
    const datasets = chartDataObj.datasets || [];
    const data = datasets.length > 0 ? (datasets[0]?.data || []) : [];
    
    // Safety check for maxValue calculation
    const numericData = data.filter(val => typeof val === 'number' && !isNaN(val));
    const maxValue = numericData.length > 0 ? Math.max(...numericData) : 0;
    const chartType = chartData.type || chartData.chartType || 'bar';

    const renderBarChart = () => {
      if (labels.length === 0 || data.length === 0) {
        return <div className="text-center text-gray-500 py-8">No data available for chart</div>;
      }
      
      return (
        <div className="space-y-3">
          {labels.map((label, index) => {
            const dataValue = data[index] !== undefined ? data[index] : 0;
            const numericValue = typeof dataValue === 'number' ? dataValue : 0;
            
            return (
              <div key={index} className="flex items-center space-x-3">
                <div className="w-32 text-sm text-gray-700 font-medium truncate" title={label}>
                  {label}
                </div>
                <div className="flex-1 bg-gray-200 rounded-full h-8 relative">
                  <div
                    className="bg-blue-500 h-8 rounded-full flex items-center justify-end pr-3 transition-all duration-500 ease-out"
                    style={{ width: `${maxValue > 0 ? (numericValue / maxValue) * 100 : 0}%` }}
                  >
                    <span className="text-white text-xs font-medium">
                      {typeof dataValue === 'number' ? dataValue.toLocaleString() : dataValue}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      );
    };

    const renderPieChart = () => {
      if (labels.length === 0 || data.length === 0) {
        return <div className="text-center text-gray-500 py-8">No data available for chart</div>;
      }

      const total = data.reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0);
      const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316'];
      
      return (
        <div className="flex flex-col lg:flex-row items-center space-y-4 lg:space-y-0 lg:space-x-8">
          <div className="w-64 h-64">
            <svg viewBox="0 0 200 200" className="w-full h-full">
              {data.map((value, index) => {
                const percentage = total > 0 ? (value / total) * 100 : 0;
                const angle = (percentage / 100) * 360;
                const startAngle = data.slice(0, index).reduce((sum, val) => sum + ((val / total) * 360), 0);
                
                const x1 = 100 + 80 * Math.cos((startAngle - 90) * Math.PI / 180);
                const y1 = 100 + 80 * Math.sin((startAngle - 90) * Math.PI / 180);
                const x2 = 100 + 80 * Math.cos((startAngle + angle - 90) * Math.PI / 180);
                const y2 = 100 + 80 * Math.sin((startAngle + angle - 90) * Math.PI / 180);
                
                const largeArcFlag = angle > 180 ? 1 : 0;
                const pathData = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
                
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
            </svg>
          </div>
          <div className="space-y-2">
            {labels.map((label, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-sm font-medium">{label}</span>
                <span className="text-sm text-gray-500">
                  {typeof data[index] === 'number' ? data[index].toLocaleString() : data[index]}
                  {total > 0 && ` (${((data[index] / total) * 100).toFixed(1)}%)`}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    };

    const renderLineChart = () => {
      if (labels.length === 0 || data.length === 0) {
        return <div className="text-center text-gray-500 py-8">No data available for chart</div>;
      }

      const numericData = data.filter(val => typeof val === 'number' && !isNaN(val));
      const minValue = Math.min(...numericData);
      const maxValue = Math.max(...numericData);
      const range = maxValue - minValue || 1;

      return (
        <div className="w-full h-64">
          <svg viewBox="0 0 400 200" className="w-full h-full">
            <defs>
              <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3"/>
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.1"/>
              </linearGradient>
            </defs>
            
            {/* Grid lines */}
            {[0, 1, 2, 3, 4].map(i => (
              <line
                key={i}
                x1="50"
                y1={40 + i * 32}
                x2="350"
                y2={40 + i * 32}
                stroke="#E5E7EB"
                strokeWidth="1"
              />
            ))}
            
            {/* Data line */}
            <polyline
              fill="none"
              stroke="#3B82F6"
              strokeWidth="3"
              points={data.map((value, index) => {
                const x = 50 + (index / (data.length - 1)) * 300;
                const y = 200 - 40 - ((value - minValue) / range) * 120;
                return `${x},${y}`;
              }).join(' ')}
            />
            
            {/* Data points */}
            {data.map((value, index) => {
              const x = 50 + (index / (data.length - 1)) * 300;
              const y = 200 - 40 - ((value - minValue) / range) * 120;
              return (
                <circle
                  key={index}
                  cx={x}
                  cy={y}
                  r="4"
                  fill="#3B82F6"
                  stroke="white"
                  strokeWidth="2"
                />
              );
            })}
            
            {/* Labels */}
            {labels.map((label, index) => {
              const x = 50 + (index / (data.length - 1)) * 300;
              return (
                <text
                  key={index}
                  x={x}
                  y="190"
                  textAnchor="middle"
                  className="fill-gray-600 text-xs"
                >
                  {label}
                </text>
              );
            })}
          </svg>
        </div>
      );
    };

    const renderTable = () => {
      const tableData = chartData.tableData || [];
      const columns = chartData.columns || [];
      
      console.log('🔍 DEBUG - Chart Data:', chartData);
      console.log('🔍 DEBUG - Table Data:', tableData);
      console.log('🔍 DEBUG - Columns:', columns);
      
      // If no specific table data, convert chart data to table format
      if (tableData.length === 0 && labels && data) {
        const convertedData = labels.map((label, index) => ({
          category: label,
          value: data[index],
          percentage: data.length > 0 ? 
            ((data[index] / data.reduce((a, b) => a + b, 0)) * 100).toFixed(1) + '%' : '0%'
        }));
        return renderDataTable(convertedData, [
          { key: 'category', label: 'Category', width: '40%' },
          { key: 'value', label: 'Value', width: '30%', align: 'right' },
          { key: 'percentage', label: 'Percentage', width: '30%', align: 'right' }
        ]);
      }
      
      return renderDataTable(tableData, columns);
    };

    const renderAdvancedChart = (type) => {
      const chartTypeInfo = {
        scatter: { icon: '📈', description: 'Scatter Plot - Correlation analysis' },
        bubble: { icon: '🫧', description: 'Bubble Chart - 3D data visualization' },
        radar: { icon: '🕸️', description: 'Radar Chart - Multi-dimensional comparison' },
        polar: { icon: '🌀', description: 'Polar Chart - Circular data representation' },
        area: { icon: '📈', description: 'Area Chart - Filled line chart' },
        histogram: { icon: '📊', description: 'Histogram - Data distribution' },
        heatmap: { icon: '🔥', description: 'Heatmap - Intensity visualization' },
        treemap: { icon: '🗂️', description: 'Treemap - Hierarchical data' },
        sankey: { icon: '🌊', description: 'Sankey Diagram - Flow visualization' },
        timeline: { icon: '⏰', description: 'Timeline - Sequential events' },
        gauge: { icon: '⏱️', description: 'Gauge - Progress indicator' },
        funnel: { icon: '🔽', description: 'Funnel Chart - Conversion process' },
        waterfall: { icon: '💧', description: 'Waterfall - Sequential changes' },
        candlestick: { icon: '📊', description: 'Candlestick - Financial data' },
        map: { icon: '🗺️', description: 'Map - Geographic visualization' }
      };

      const info = chartTypeInfo[type] || { icon: '📊', description: 'Advanced Chart' };

      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">{info.icon}</div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">{info.description}</h3>
          <p className="text-gray-600 mb-4">Advanced chart rendering coming soon!</p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
            <p className="text-sm text-blue-800">
              This chart type is supported by the backend but requires additional frontend implementation.
            </p>
          </div>
        </div>
      );
    };

    const renderChart = () => {
      switch (chartType) {
        case 'bar': return renderBarChart();
        case 'pie': return renderPieChart();
        case 'line': return renderLineChart();
        case 'table': return renderTable();
        case 'doughnut': return renderPieChart(); // Same as pie for now
        case 'scatter': return renderAdvancedChart('scatter');
        case 'bubble': return renderAdvancedChart('bubble');
        case 'radar': return renderAdvancedChart('radar');
        case 'polar': return renderAdvancedChart('polar');
        case 'area': return renderAdvancedChart('area');
        case 'histogram': return renderAdvancedChart('histogram');
        case 'heatmap': return renderAdvancedChart('heatmap');
        case 'treemap': return renderAdvancedChart('treemap');
        case 'sankey': return renderAdvancedChart('sankey');
        case 'timeline': return renderAdvancedChart('timeline');
        case 'gauge': return renderAdvancedChart('gauge');
        case 'funnel': return renderAdvancedChart('funnel');
        case 'waterfall': return renderAdvancedChart('waterfall');
        case 'candlestick': return renderAdvancedChart('candlestick');
        case 'map': return renderAdvancedChart('map');
        case 'custom': return renderAdvancedChart('custom');
        case 'mixed': return renderAdvancedChart('mixed');
        default: return renderBarChart();
      }
    };

    const getChartTypeIcon = () => {
      const iconMap = {
        bar: <BarChart3 className="w-4 h-4" />,
        pie: <PieChart className="w-4 h-4" />,
        line: <TrendingUp className="w-4 h-4" />,
        table: <TableIcon className="w-4 h-4" />,
        doughnut: <PieChart className="w-4 h-4" />
      };
      return iconMap[chartType] || <BarChart3 className="w-4 h-4" />;
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
            <span>{data.length || chartData.tableData?.length || 0} data points</span>
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
    // Handle missing response object
    if (!response) {
      return (
        <div className="text-center py-8 text-gray-400">
          <p>Invalid response data</p>
        </div>
      );
    }

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
            <div className="flex items-center space-x-3">
              <textarea
                ref={textareaRef}
                defaultValue={response?.query || ''}
                className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="2"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSaveEdit(response?.id, e.target.value);
                  }
                  if (e.key === 'Escape') {
                    handleCancelEdit();
                  }
                }}
              />
              <button
                onClick={() => handleSaveEdit(response?.id, textareaRef.current?.value)}
                className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                title="Save changes"
              >
                <Save className="w-4 h-4" />
              </button>
              <button
                onClick={handleCancelEdit}
                className="p-2 text-gray-500 hover:bg-gray-50 rounded-lg"
                title="Cancel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-start justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex-1">
                {response?.query || 'No query available'}
              </h3>
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => handleEdit(response?.id)}
                  className="p-2 text-gray-500 hover:bg-gray-50 rounded-lg"
                  title="Edit query"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => copyToClipboard(response?.query || '')}
                  className="p-2 text-gray-500 hover:bg-gray-50 rounded-lg"
                  title="Copy query"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6 border-b border-gray-200">
          {['Answer', 'Images', 'Sources', 'Steps'].map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabChange(response?.id, tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              {tab}
              {tab === 'Sources' && <span className="ml-1 text-xs bg-gray-200 px-1.5 py-0.5 rounded-full">3</span>}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'Answer' && (
          <div>
            {/* Main Response Content */}
            <div className="prose prose-gray max-w-none mb-6">
              <ReactMarkdown>
                {response?.content || response?.answer || 'No response content available.'}
              </ReactMarkdown>
            </div>

            {/* Chart/Visualization */}
            {response?.chart_data && (
              <ChartDisplay chartData={response.chart_data} />
            )}

            {/* Insights Section */}
            {response?.insights && Array.isArray(response.insights) && response.insights.length > 0 && (
              <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-100">
                <div className="flex items-center space-x-2 mb-4">
                  <Zap className="w-5 h-5 text-blue-600" />
                  <h4 className="text-lg font-semibold text-blue-900">Key Insights</h4>
                </div>
                <ul className="space-y-2">
                  {response.insights.map((insight, idx) => (
                    <li key={idx} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-blue-800">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations Section */}
            {response?.recommendations && Array.isArray(response.recommendations) && response.recommendations.length > 0 && (
              <div className="mt-6 p-6 bg-green-50 rounded-xl border border-green-100">
                <div className="flex items-center space-x-2 mb-4">
                  <Target className="w-5 h-5 text-green-600" />
                  <h4 className="text-lg font-semibold text-green-900">Recommendations</h4>
                </div>
                <ul className="space-y-2">
                  {response.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-green-800">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Answer Validation */}
            {response?.validation && (
              <div className="mt-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold text-gray-900">Answer Validation</h4>
                  <div className="flex items-center space-x-2">
                    <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                      {response.validation.confidence || '85%'} confidence
                    </div>
                  </div>
                </div>
                <ul className="space-y-2">
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-gray-700">Data processed successfully from backend</span>
                  </li>
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-gray-700">Response generated successfully</span>
                  </li>
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'Images' && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🖼️</div>
            <p className="font-medium">No images in this response</p>
          </div>
        )}

        {activeTab === 'Sources' && (
          <div className="space-y-4">
            {mockSources.map((source) => (
              <div key={source.id} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="text-2xl">{source.favicon}</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h5 className="font-medium text-gray-900">{source.title}</h5>
                    <ExternalLink className="w-4 h-4 text-gray-400" />
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{source.description}</p>
                  <div className="text-xs text-gray-500 font-mono">{source.url}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'Steps' && (
          <div className="space-y-4">
            <div className="flex items-start space-x-4 p-4 bg-blue-50 rounded-lg">
              <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">1</div>
              <div>
                <h5 className="font-medium text-gray-900 mb-1">Query Analysis</h5>
                <p className="text-sm text-gray-600">Analyzed user query and determined intent for data retrieval</p>
              </div>
            </div>
            <div className="flex items-start space-x-4 p-4 bg-blue-50 rounded-lg">
              <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">2</div>
              <div>
                <h5 className="font-medium text-gray-900 mb-1">Database Query</h5>
                <p className="text-sm text-gray-600">Generated and executed MongoDB aggregation pipeline</p>
              </div>
            </div>
            <div className="flex items-start space-x-4 p-4 bg-blue-50 rounded-lg">
              <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">3</div>
              <div>
                <h5 className="font-medium text-gray-900 mb-1">Data Processing</h5>
                <p className="text-sm text-gray-600">Processed raw data and determined optimal visualization format</p>
              </div>
            </div>
            <div className="flex items-start space-x-4 p-4 bg-green-50 rounded-lg">
              <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">4</div>
              <div>
                <h5 className="font-medium text-gray-900 mb-1">Response Generation</h5>
                <p className="text-sm text-gray-600">Generated insights, recommendations, and formatted response</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Loading Component
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-300 rounded"></div>
            <div className="h-4 bg-gray-300 rounded w-5/6"></div>
            <div className="h-4 bg-gray-300 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  // Determine which responses to display
  const displayResponses = chatResponses.length > 0 ? chatResponses : responses;
  const hasResponses = Array.isArray(displayResponses) && displayResponses.length > 0;

  // Main render
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Chat Header */}
      {chatId && (
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {chatTitle || 'Analytics Chat'}
              </h1>
              <p className="text-sm text-gray-500">Chat ID: {chatId}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {isLoading ? (
          <div className="space-y-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-300 rounded w-3/4 mb-4"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-300 rounded"></div>
                <div className="h-4 bg-gray-300 rounded w-5/6"></div>
                <div className="h-4 bg-gray-300 rounded w-4/6"></div>
              </div>
            </div>
          </div>
        ) : hasResponses ? (
          <div className="space-y-8">
            {displayResponses.map((response, index) => (
              <ResponseComponent key={response?.id || index} response={response} index={index} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">💬</div>
            <p className="font-medium">No responses yet</p>
            <p className="text-sm mt-2">Ask a question to get started!</p>
          </div>
        )}
      </div>

      {/* Query Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <input
              ref={queryInputRef}
              type="text"
              value={currentQuery}
              onChange={(e) => setCurrentQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your data..."
              disabled={isSubmitting}
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            {isSubmitting && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={!currentQuery.trim() || isSubmitting}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
          >
            <Send className="w-4 h-4" />
            <span>{isSubmitting ? 'Sending...' : 'Send'}</span>
          </button>
        </form>
        
        {/* Quick Examples */}
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            'List all users',
            'Show sales by category', 
            'Product performance chart',
            'Revenue trends this month'
          ].map((example) => (
            <button
              key={example}
              onClick={() => setCurrentQuery(example)}
              disabled={isSubmitting}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ResponseInterface;