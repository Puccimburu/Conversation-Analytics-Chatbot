// Fixed ResponseInterface.jsx - Removed duplicate inputs + Added Follow-Up Questions
// File: frontend/src/components/chat/ResponseInterface.jsx

import React, { useState, useRef, useEffect } from 'react';
import { 
  Edit3, Save, X, Copy, RefreshCw, ChevronDown, ChevronUp,
  BarChart3, PieChart, TrendingUp, Table as TableIcon, Circle,
  Download, ExternalLink, Zap, Activity, Target, MessageCircle, ArrowRight
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
  query = null,
  onNewQuery = () => {} // NEW: Callback to handle new queries from follow-ups
}) => {
  const [editingResponseId, setEditingResponseId] = useState(null);
  const [expandedResponses, setExpandedResponses] = useState(new Set());
  const [activeTab, setActiveTab] = useState('Answer');
  const [chatResponses, setChatResponses] = useState([]);
  const textareaRef = useRef(null);

  // Initialize chat responses from props
  useEffect(() => {
    if (existingMessages && existingMessages.length > 0) {
      const convertedResponses = existingMessages
        .filter(msg => msg.role === 'assistant')
        .map((msg, index) => ({
          id: `msg_${index}`,
          query: existingMessages[index * 2]?.content || 'Previous query',
          content: msg.content,
          chart_data: msg.chart_data,
          insights: msg.insights,
          recommendations: msg.recommendations,
          suggestions: msg.suggestions || msg.smart_suggestions || [], // IMPORTANT: Extract suggestions
          timestamp: msg.timestamp
        }));
      setChatResponses(convertedResponses);
    }
    
    if (query && chatId) {
      handleQuerySubmission(query);
    }
  }, [existingMessages, query, chatId]);

  // Clean chart title function
  const cleanChartTitle = (title) => {
    if (!title) return 'Data Analysis';
    
    // Remove metadata if present
    if (title.includes('DOMAIN:') || title.includes('USER QUESTION:')) {
      const userQuestionMatch = title.match(/USER QUESTION:\s*(.+)$/);
      if (userQuestionMatch) {
        const question = userQuestionMatch[1].trim();
        return question.charAt(0).toUpperCase() + question.slice(1);
      }
    }
    
    // Clean existing title
    return title.replace(/^Table:\s*/, '').trim();
  };

  // Query submission function
  const handleQuerySubmission = async (queryText) => {
    if (!queryText.trim()) return;

    const loadingResponse = {
      id: `loading_${Date.now()}`,
      query: queryText,
      content: 'Processing your request...',
      isLoading: true
    };

    setChatResponses(prev => [...prev, loadingResponse]);

    try {
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
          // DEBUG: Log what we're extracting
          console.log('🔍 Creating actualResponse from result:', result);
          console.log('🔍 Extracting suggestions:', result.suggestions, 'smart_suggestions:', result.smart_suggestions);
          
          const actualResponse = {
            id: `response_${Date.now()}`,
            query: queryText,
            content: result.summary || result.answer || 'Analysis completed',
            chart_data: result.chart_data || result.visualization,
            insights: result.insights,
            recommendations: result.recommendations,
            suggestions: result.suggestions || result.smart_suggestions || [], // EXTRACT SUGGESTIONS
            processing_mode: result.processing_mode,
            execution_time: result.execution_time
          };
          
          console.log('🔍 actualResponse created with suggestions:', actualResponse.suggestions);

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
      
      const errorResponse = {
        id: `error_${Date.now()}`,
        query: queryText,
        content: `Error: ${error.message}`,
        isError: true,
        suggestions: []
      };

      setChatResponses(prev => 
        prev.map(r => r.id === loadingResponse.id ? errorResponse : r)
      );
    }
  };

  // NEW: Follow-Up Questions Component
  const FollowUpQuestions = ({ suggestions, onQuestionClick }) => {
    // TEMP DEBUG: Log what we're receiving
    console.log('🔍 FollowUpQuestions received:', suggestions, 'length:', suggestions?.length);
    
    if (!suggestions || suggestions.length === 0) {
      console.log('❌ FollowUpQuestions returning null - no suggestions');
      return null;
    }

    return (
      <div className="mt-6 p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-100">
        <div className="flex items-center space-x-2 mb-4">
          <MessageCircle className="w-5 h-5 text-purple-600" />
          <h4 className="text-lg font-semibold text-purple-900">Follow-Up Questions</h4>
          <div className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
            AI Generated
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {suggestions.slice(0, 6).map((suggestion, index) => (
            <button
              key={index}
              onClick={(e) => {
                console.log('🔍 Button clicked:', suggestion);
                e.preventDefault();
                e.stopPropagation();
                onQuestionClick(suggestion);
              }}
              className="group flex items-center justify-between p-4 bg-white rounded-lg border border-purple-200 hover:border-purple-300 hover:shadow-md transition-all duration-200 text-left cursor-pointer"
            >
              <span className="text-sm text-gray-700 group-hover:text-purple-700 font-medium">
                {suggestion}
              </span>
              <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600 transition-colors" />
            </button>
          ))}
        </div>
        
        {suggestions.length > 6 && (
          <div className="mt-3 text-center">
            <span className="text-xs text-purple-600">
              +{suggestions.length - 6} more suggestions available
            </span>
          </div>
        )}
      </div>
    );
  };

  // Handle follow-up question clicks
  const handleFollowUpClick = (question) => {
    console.log('🔍 Follow-up question clicked:', question);
    console.log('🔍 onNewQuery available:', !!onNewQuery);
    
    if (onNewQuery) {
      console.log('🔍 Using onNewQuery callback');
      onNewQuery(question);
    } else {
      console.log('🔍 Using handleQuerySubmission');
      handleQuerySubmission(question);
    }
  };

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

  const handleTabChange = (responseId, newTab) => {
    setActiveTab(newTab);
  };

  // Enhanced formatTableValue function
  const formatTableValue = (value, type) => {
    if (value === null || value === undefined || value === '') {
      return '-';
    }
    
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
                    key={column.key || column.field || index}
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
                    const columnKey = column.key || column.field;
                    let cellValue = row[columnKey];
                    
                    if (cellValue === undefined || cellValue === null) {
                      const altKeys = [
                        columnKey?.toLowerCase(),
                        columnKey?.toUpperCase(),
                        columnKey?.replace(/_/g, ''),
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
        
        <div className="mt-4 px-6 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>Showing {data.length} records</span>
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
    console.log('🔍 ChartDisplay received chartData:', chartData);
    if (chartData.data) {
      chartDataObj = chartData.data;
    } else if (chartData.labels || chartData.datasets) {
      chartDataObj = chartData;
    } else if (chartData.htmlContent || chartData.tableData) {
      chartDataObj = { labels: [], datasets: [] };
    } else {
      return (
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">⚠️</div>
          <p>Invalid chart data format</p>
        </div>
      );
    }

    const labels = chartDataObj.labels || [];
    const datasets = chartDataObj.datasets || [];
    const data = datasets.length > 0 ? (datasets[0]?.data || []) : [];
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

    const renderTable = () => {
      const tableData = chartData.tableData || [];
      const columns = chartData.columns || [];
      
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

    const renderDoughnutChart = () => {
      if (labels.length === 0 || data.length === 0) {
        return <div className="text-center text-gray-500 py-8">No data available for doughnut chart</div>;
      }

      const total = data.reduce((sum, value) => sum + (typeof value === 'number' ? value : 0), 0);
      const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'];
      
      let cumulativeAngle = 0;
      const segments = data.map((value, index) => {
        const numericValue = typeof value === 'number' ? value : 0;
        const percentage = total > 0 ? (numericValue / total) * 100 : 0;
        const angle = total > 0 ? (numericValue / total) * 360 : 0;
        
        const segment = {
          value: numericValue,
          percentage: percentage,
          startAngle: cumulativeAngle,
          endAngle: cumulativeAngle + angle,
          color: colors[index % colors.length],
          label: labels[index]
        };
        
        cumulativeAngle += angle;
        return segment;
      });

      return (
        <div className="flex flex-col lg:flex-row items-center justify-center space-y-6 lg:space-y-0 lg:space-x-8">
          {/* Doughnut Chart */}
          <div className="relative">
            <svg width="280" height="280" className="transform -rotate-90">
              <circle
                cx="140"
                cy="140"
                r="120"
                fill="none"
                stroke="#F3F4F6"
                strokeWidth="40"
              />
              {segments.map((segment, index) => {
                if (segment.percentage === 0) return null;
                
                const radius = 120;
                const circumference = 2 * Math.PI * radius;
                const strokeDasharray = `${(segment.percentage / 100) * circumference} ${circumference}`;
                const strokeDashoffset = -((segment.startAngle / 360) * circumference);
                
                return (
                  <circle
                    key={index}
                    cx="140"
                    cy="140"
                    r={radius}
                    fill="none"
                    stroke={segment.color}
                    strokeWidth="40"
                    strokeDasharray={strokeDasharray}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-300"
                  />
                );
              })}
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">{total.toLocaleString()}</div>
                <div className="text-sm text-gray-500">Total</div>
              </div>
            </div>
          </div>
          
          {/* Legend */}
          <div className="space-y-3">
            {segments.map((segment, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: segment.color }}
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700">
                    {segment.label}
                  </div>
                  <div className="text-xs text-gray-500">
                    {segment.value.toLocaleString()} ({segment.percentage.toFixed(1)}%)
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    };

    const renderChart = () => {
      switch (chartType) {
        case 'bar': return renderBarChart();
        case 'pie': return renderDoughnutChart(); // Reuse doughnut for pie
        case 'doughnut': return renderDoughnutChart();
        case 'table': return renderTable();
        default: return renderBarChart();
      }
    };

    const getChartTypeIcon = () => {
      const iconMap = {
        bar: <BarChart3 className="w-4 h-4" />,
        pie: <PieChart className="w-4 h-4" />,
        doughnut: <Circle className="w-4 h-4" />,
        line: <TrendingUp className="w-4 h-4" />,
        table: <TableIcon className="w-4 h-4" />
      };
      return iconMap[chartType] || <BarChart3 className="w-4 h-4" />;
    };

    // FIXED: Clean the chart title
    const cleanTitle = cleanChartTitle(chartData.options?.plugins?.title?.text || chartData.title);

    return (
      <div className="mt-8 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h4 className="text-xl font-semibold text-gray-900">
            {cleanTitle}
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

  // Multi-Output Display Component
  const MultiOutputDisplay = ({ outputs, primaryInsights, recommendations }) => {
    if (!outputs || !Array.isArray(outputs) || outputs.length === 0) {
      return null;
    }

    const textOutputs = outputs.filter(output => output.type === 'text');
    const tableOutputs = outputs.filter(output => output.type === 'table');
    const chartOutputs = outputs.filter(output => output.type === 'chart');

    return (
      <div className="space-y-6">
        {/* Text Outputs */}
        {textOutputs.map((textOutput, index) => (
          <div key={`text-${index}`} className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
            <div className="flex items-center space-x-2 mb-4">
              <MessageCircle className="w-5 h-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-800">Analysis</h3>
            </div>
            <div className="prose max-w-none">
              <ReactMarkdown className="text-gray-700 leading-relaxed">
                {textOutput.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {/* Charts and Tables Grid */}
        <div className={`grid gap-6 ${chartOutputs.length > 0 && tableOutputs.length > 0 ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
          {/* Chart Outputs */}
          {chartOutputs.map((chartOutput, index) => (
            <div key={`chart-${index}`} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="border-b border-gray-100 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {(() => {
                      const iconMap = {
                        bar: <BarChart3 className="w-5 h-5 text-blue-600" />,
                        pie: <PieChart className="w-5 h-5 text-green-600" />,
                        doughnut: <Circle className="w-5 h-5 text-purple-600" />,
                        line: <TrendingUp className="w-5 h-5 text-orange-600" />
                      };
                      return iconMap[chartOutput.chart_type] || <BarChart3 className="w-5 h-5 text-blue-600" />;
                    })()}
                    <h3 className="text-lg font-semibold text-gray-800 capitalize">
                      {chartOutput.chart_type} Chart
                    </h3>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <ChartDisplay 
                  chartData={{
                    type: chartOutput.chart_type,
                    data: chartOutput.data,
                    options: chartOutput.options
                  }} 
                />
              </div>
            </div>
          ))}

          {/* Table Outputs */}
          {tableOutputs.map((tableOutput, index) => (
            <div key={`table-${index}`} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="border-b border-gray-100 px-6 py-4">
                <div className="flex items-center space-x-2">
                  <TableIcon className="w-5 h-5 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-800">Data Table</h3>
                </div>
              </div>
              <div className="p-6">
                {tableOutput.data && tableOutput.data.tableData && renderDataTable(
                  tableOutput.data.tableData,
                  tableOutput.data.columns || Object.keys(tableOutput.data.tableData[0] || {})
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Insights and Recommendations */}
        {(primaryInsights?.length > 0 || recommendations?.length > 0) && (
          <div className="grid md:grid-cols-2 gap-6">
            {primaryInsights && primaryInsights.length > 0 && (
              <div className="bg-green-50 rounded-xl p-6 border border-green-100">
                <div className="flex items-center space-x-2 mb-4">
                  <Target className="w-5 h-5 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-800">Key Insights</h3>
                </div>
                <ul className="space-y-2">
                  {primaryInsights.map((insight, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <ArrowRight className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {recommendations && recommendations.length > 0 && (
              <div className="bg-orange-50 rounded-xl p-6 border border-orange-100">
                <div className="flex items-center space-x-2 mb-4">
                  <Zap className="w-5 h-5 text-orange-600" />
                  <h3 className="text-lg font-semibold text-gray-800">Recommendations</h3>
                </div>
                <ul className="space-y-2">
                  {recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <ArrowRight className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Single Response Component
  const ResponseComponent = ({ response, index }) => {
    if (!response) {
      return (
        <div className="text-center py-8 text-gray-400">
          <p>Invalid response data</p>
        </div>
      );
    }

    const isEditing = editingResponseId === response.id;
    const mockSources = [
      { id: 1, title: 'MongoDB Analytics Database', url: 'mongodb://localhost:27017/genaiexeco-development', favicon: '📊', description: 'Your MongoDB analytics database with sales, customer, and product data.' },
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
            {/* Multi-Output Display (New System) */}
            {(() => {
              // Debug logging
              console.log('🔍 RESPONSE STRUCTURE DEBUG:');
              console.log('   Has outputs:', response?.outputs && Array.isArray(response.outputs));
              console.log('   Outputs length:', response?.outputs?.length || 0);
              console.log('   Has chart_data:', !!response?.chart_data);
              console.log('   Chart_data type:', typeof response?.chart_data);
              console.log('   Chart_data keys:', response?.chart_data ? Object.keys(response.chart_data) : 'none');
              
              // Use new multi-output system if available
              if (response?.outputs && Array.isArray(response.outputs) && response.outputs.length > 0) {
                console.log('🎯 Using NEW multi-output system');
                return (
                  <MultiOutputDisplay 
                    outputs={response.outputs}
                    primaryInsights={response.primary_insights || response.insights}
                    recommendations={response.recommendations}
                  />
                );
              } else {
                console.log('🎯 Using LEGACY single-output system');
                return (
                  /* Legacy Single Output Display (Backward Compatibility) */
                  <>
                    <div className="prose prose-gray max-w-none mb-6">
                      <ReactMarkdown>
                        {response?.content || response?.answer || response?.summary || 'No response content available.'}
                      </ReactMarkdown>
                    </div>

                    {/* Chart/Visualization */}
                    {response?.chart_data && Object.keys(response.chart_data).length > 0 && (
                      <ChartDisplay chartData={response.chart_data} />
                    )}
                    
                    {/* Debug: Show what we have if chart_data is empty */}
                    {response?.chart_data && Object.keys(response.chart_data).length === 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                        <p className="text-yellow-800">⚠️ Chart data is empty object. Backend might not be sending proper chart data.</p>
                        <details className="mt-2">
                          <summary className="cursor-pointer text-sm">Debug Info</summary>
                          <pre className="text-xs mt-2 bg-gray-100 p-2 rounded">{JSON.stringify(response, null, 2)}</pre>
                        </details>
                      </div>
                    )}
                  </>
                );
              }
            })()}


            {/* NEW: Follow-Up Questions Component */}
            {(() => {
              const suggestionData = response?.suggestions || response?.smart_suggestions || [];
              console.log('🔍 ResponseComponent passing suggestions:', suggestionData, 'from response:', response);
              return (
                <FollowUpQuestions 
                  suggestions={suggestionData} 
                  onQuestionClick={handleFollowUpClick}
                />
              );
            })()}
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

  // Main render - REMOVED ALL INPUT FIELDS
  return (
    <div className="flex flex-col h-full bg-gray-50">
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

      {/* Messages Area - NO INPUT FIELDS HERE */}
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

      {/* REMOVED: Query Input Area - This was the duplicate input field */}
      {/* The main input field should be handled by the parent component (ChatViewPage) */}
    </div>
  );
};

export default ResponseInterface;