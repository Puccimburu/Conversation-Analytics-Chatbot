import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Image, 
  MapPin, 
  Paperclip, 
  Mic, 
  Send,
  BarChart3,
  DollarSign,
  Users,
  TrendingUp,
  Package,
  ThumbsUp, 
  ThumbsDown, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Star,
  PieChart
} from 'lucide-react';

const MainChatInterface = () => {
  const [query, setQuery] = useState('');
  const [isActive, setIsActive] = useState(false);
  const [showResponse, setShowResponse] = useState(false);
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [stats, setStats] = useState(null);

  // Load initial stats
  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/health');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Analytics-focused suggested actions
  const suggestedActions = [
    { icon: DollarSign, label: 'Sales Analysis', color: 'bg-green-50 text-green-700 border-green-200' },
    { icon: Users, label: 'Customer Insights', color: 'bg-blue-50 text-blue-700 border-blue-200' },
    { icon: TrendingUp, label: 'Revenue Trends', color: 'bg-purple-50 text-purple-700 border-purple-200' },
    { icon: Package, label: 'Product Performance', color: 'bg-orange-50 text-orange-700 border-orange-200' },
    { icon: BarChart3, label: 'Market Analysis', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' }
  ];

  // Feedback Modal Component
  const FeedbackModal = ({ isOpen, onClose, queryId, currentAnswer }) => {
    const [rating, setRating] = useState(0);
    const [feedbackType, setFeedbackType] = useState('general');
    const [comment, setComment] = useState('');
    const [correction, setCorrection] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const submitFeedback = async () => {
      if (rating === 0) {
        alert('Please provide a rating');
        return;
      }

      setIsSubmitting(true);
      try {
        const response = await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query_id: queryId,
            rating,
            type: feedbackType,
            comment,
            correction
          })
        });

        if (response.ok) {
          alert('Thank you for your feedback!');
          onClose();
          setRating(0);
          setComment('');
          setCorrection('');
        } else {
          alert('Failed to submit feedback');
        }
      } catch (error) {
        console.error('Feedback submission error:', error);
        alert('Failed to submit feedback');
      } finally {
        setIsSubmitting(false);
      }
    };

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <h3 className="text-lg font-semibold mb-4">Rate This Answer</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Overall Rating</label>
            <div className="flex space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`h-6 w-6 cursor-pointer ${
                    star <= rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                  }`}
                  onClick={() => setRating(star)}
                />
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {rating === 0 && 'Click to rate'}
              {rating === 1 && 'Very Poor'}
              {rating === 2 && 'Poor'}
              {rating === 3 && 'Average'}
              {rating === 4 && 'Good'}
              {rating === 5 && 'Excellent'}
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">What aspect are you rating?</label>
            <select
              value={feedbackType}
              onChange={(e) => setFeedbackType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="general">Overall Quality</option>
              <option value="accuracy">Data Accuracy</option>
              <option value="completeness">Completeness</option>
              <option value="clarity">Clarity/Readability</option>
              <option value="chart">Chart Appropriateness</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Additional Comments (Optional)</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="What could be improved?"
              className="w-full border border-gray-300 rounded-md px-3 py-2 h-20 resize-none"
            />
          </div>

          {rating <= 2 && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-red-600">
                What should the correct answer be?
              </label>
              <textarea
                value={correction}
                onChange={(e) => setCorrection(e.target.value)}
                placeholder="Please provide the correct answer or explanation..."
                className="w-full border border-red-300 rounded-md px-3 py-2 h-20 resize-none"
              />
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={submitFeedback}
              disabled={isSubmitting || rating === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
            >
              <Send className="h-4 w-4" />
              <span>{isSubmitting ? 'Submitting...' : 'Submit Feedback'}</span>
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Validation Display Component
  const ValidationDisplay = ({ validation }) => {
    if (!validation) return null;

    const getConfidenceColor = (confidence) => {
      switch (confidence) {
        case 'high': return 'text-green-600 bg-green-50';
        case 'medium': return 'text-yellow-600 bg-yellow-50';
        case 'low': return 'text-red-600 bg-red-50';
        default: return 'text-gray-600 bg-gray-50';
      }
    };

    const getConfidenceIcon = (confidence) => {
      switch (confidence) {
        case 'high': return <CheckCircle className="h-4 w-4" />;
        case 'medium': return <Info className="h-4 w-4" />;
        case 'low': return <AlertTriangle className="h-4 w-4" />;
        default: return <Info className="h-4 w-4" />;
      }
    };

    return (
      <div className="mt-4 border border-gray-200 rounded-lg p-4 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-gray-900">Answer Validation</h4>
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(validation.confidence)}`}>
            {getConfidenceIcon(validation.confidence)}
            <span>{validation.confidence?.toUpperCase()} CONFIDENCE</span>
          </div>
        </div>

        <div className="mb-3">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm font-medium">Validation Score:</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  validation.overall_score >= 0.8 ? 'bg-green-500' :
                  validation.overall_score >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${validation.overall_score * 100}%` }}
              />
            </div>
            <span className="text-sm text-gray-600">{Math.round(validation.overall_score * 100)}%</span>
          </div>
        </div>

        {validation.checks && validation.checks.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Automated Checks:</p>
            {validation.checks.map((check, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm">
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

        {validation.suggestions && validation.suggestions.length > 0 && (
          <div className="mt-3 p-3 bg-blue-50 rounded-md">
            <p className="text-sm font-medium text-blue-800 mb-1">Suggestions:</p>
            <ul className="text-sm text-blue-700 space-y-1">
              {validation.suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start space-x-1">
                  <span>•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  // Multi-Chart Display Component - Clean version from your working app.js
  const ChartDisplay = ({ chartData }) => {
    if (!chartData || !chartData.data) return null;

    const { labels, datasets } = chartData.data;
    const data = datasets[0]?.data || [];
    const maxValue = Math.max(...data.filter(val => typeof val === 'number'));
    const chartType = chartData.type || 'bar';

    console.log('Rendering chart type:', chartType, 'with data:', data);

    const colorSchemes = {
      vibrant: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']
    };

    const getChartColors = (type, dataLength) => {
      const scheme = colorSchemes.vibrant;
      if (type === 'pie' || type === 'doughnut') {
        return scheme.slice(0, dataLength);
      }
      return scheme[0];
    };

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
      const pieColors = getChartColors('pie', data.length);
      let currentAngle = 0;
      
      return (
        <div className="flex flex-col lg:flex-row items-center space-y-4 lg:space-y-0 lg:space-x-6">
          <div className="relative">
            <svg width="240" height="240" viewBox="0 0 240 240" className="transform -rotate-90">
              {data.map((value, index) => {
                const percentage = total > 0 ? (value / total) * 100 : 0;
                const angle = (percentage / 100) * 360;
                const startAngle = currentAngle;
                const endAngle = currentAngle + angle;
                currentAngle += angle;

                const x1 = 120 + 100 * Math.cos((startAngle * Math.PI) / 180);
                const y1 = 120 + 100 * Math.sin((startAngle * Math.PI) / 180);
                const x2 = 120 + 100 * Math.cos((endAngle * Math.PI) / 180);
                const y2 = 120 + 100 * Math.sin((endAngle * Math.PI) / 180);
                const largeArcFlag = angle > 180 ? 1 : 0;

                if (percentage < 0.5) return null;

                return (
                  <path
                    key={index}
                    d={`M 120 120 L ${x1} ${y1} A 100 100 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
                    fill={pieColors[index % pieColors.length]}
                    stroke="white"
                    strokeWidth="3"
                    className="hover:opacity-80 transition-opacity cursor-pointer"
                    title={`${labels[index]}: ${percentage.toFixed(1)}%`}
                  />
                );
              })}
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center bg-white rounded-full p-3 shadow-sm">
                <div className="text-sm font-bold text-gray-900">Total</div>
                <div className="text-xs text-gray-600">{total.toLocaleString()}</div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 gap-3 max-w-sm">
            {labels.map((label, index) => {
              const percentage = total > 0 ? ((data[index] / total) * 100) : 0;
              return (
                <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                  <div 
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: pieColors[index % pieColors.length] }}
                  />
                  <span className="text-sm text-gray-700 flex-1 font-medium" title={label}>
                    {label}
                  </span>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">
                      {data[index].toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {percentage.toFixed(1)}%
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
      const doughnutTotal = data.reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0);
      const doughnutColors = getChartColors('doughnut', data.length);
      let doughnutAngle = 0;
      
      return (
        <div className="flex flex-col lg:flex-row items-center space-y-4 lg:space-y-0 lg:space-x-6">
          <div className="relative">
            <svg width="240" height="240" viewBox="0 0 240 240" className="transform -rotate-90">
              {data.map((value, index) => {
                const percentage = doughnutTotal > 0 ? (value / doughnutTotal) * 100 : 0;
                const angle = (percentage / 100) * 360;
                const startAngle = doughnutAngle;
                const endAngle = doughnutAngle + angle;
                doughnutAngle += angle;

                const x1 = 120 + 100 * Math.cos((startAngle * Math.PI) / 180);
                const y1 = 120 + 100 * Math.sin((startAngle * Math.PI) / 180);
                const x2 = 120 + 100 * Math.cos((endAngle * Math.PI) / 180);
                const y2 = 120 + 100 * Math.sin((endAngle * Math.PI) / 180);
                
                const x3 = 120 + 60 * Math.cos((endAngle * Math.PI) / 180);
                const y3 = 120 + 60 * Math.sin((endAngle * Math.PI) / 180);
                const x4 = 120 + 60 * Math.cos((startAngle * Math.PI) / 180);
                const y4 = 120 + 60 * Math.sin((startAngle * Math.PI) / 180);
                
                const largeArcFlag = angle > 180 ? 1 : 0;

                if (percentage < 0.5) return null;

                return (
                  <path
                    key={index}
                    d={`M ${x1} ${y1} A 100 100 0 ${largeArcFlag} 1 ${x2} ${y2} L ${x3} ${y3} A 60 60 0 ${largeArcFlag} 0 ${x4} ${y4} Z`}
                    fill={doughnutColors[index % doughnutColors.length]}
                    stroke="white"
                    strokeWidth="3"
                    className="hover:opacity-80 transition-opacity cursor-pointer"
                    title={`${labels[index]}: ${percentage.toFixed(1)}%`}
                  />
                );
              })}
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">Total</div>
                <div className="text-sm text-gray-600">{doughnutTotal.toLocaleString()}</div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 gap-3 max-w-sm">
            {labels.map((label, index) => {
              const percentage = doughnutTotal > 0 ? ((data[index] / doughnutTotal) * 100) : 0;
              return (
                <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                  <div 
                    className="w-4 h-4 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: doughnutColors[index % doughnutColors.length] }}
                  />
                  <span className="text-sm text-gray-700 flex-1 font-medium" title={label}>
                    {label}
                  </span>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">
                      {data[index].toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {percentage.toFixed(1)}%
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
      const lineMaxValue = Math.max(...data.filter(val => typeof val === 'number'));
      const lineMinValue = Math.min(...data.filter(val => typeof val === 'number'));
      const lineRange = lineMaxValue - lineMinValue || 1;
      
      return (
        <div className="w-full bg-white p-4 rounded border">
          <svg width="100%" height="320" viewBox="0 0 700 320" className="bg-gray-50 rounded">
            {[0, 1, 2, 3, 4, 5].map(i => (
              <g key={i}>
                <line
                  x1="80"
                  y1={60 + (i * 40)}
                  x2="650"
                  y2={60 + (i * 40)}
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
                <text
                  x="70"
                  y={65 + (i * 40)}
                  textAnchor="end"
                  className="text-xs fill-gray-500"
                >
                  {Math.round(lineMaxValue - (i * lineRange / 5)).toLocaleString()}
                </text>
              </g>
            ))}
            
            <polyline
              points={data.map((value, index) => {
                const x = 80 + (index * (570 / Math.max(data.length - 1, 1)));
                const y = 260 - ((value - lineMinValue) / lineRange) * 200;
                return `${x},${y}`;
              }).join(' ')}
              fill="none"
              stroke="#3B82F6"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            
            {data.map((value, index) => {
              const x = 80 + (index * (570 / Math.max(data.length - 1, 1)));
              const y = 260 - ((value - lineMinValue) / lineRange) * 200;
              return (
                <g key={index}>
                  <circle
                    cx={x}
                    cy={y}
                    r="5"
                    fill="#3B82F6"
                    stroke="white"
                    strokeWidth="2"
                    className="hover:r-7 transition-all cursor-pointer"
                  />
                  <text
                    x={x}
                    y={y - 10}
                    textAnchor="middle"
                    className="text-xs fill-gray-700 opacity-0 hover:opacity-100"
                  >
                    {value.toLocaleString()}
                  </text>
                </g>
              );
            })}
            
            {labels.map((label, index) => {
              const x = 80 + (index * (570 / Math.max(data.length - 1, 1)));
              return (
                <text
                  key={index}
                  x={x}
                  y="290"
                  textAnchor="middle"
                  className="text-xs fill-gray-600"
                  transform={label.length > 8 ? `rotate(-45, ${x}, 290)` : ''}
                >
                  {label.length > 12 ? label.substring(0, 12) + '...' : label}
                </text>
              );
            })}
          </svg>
        </div>
      );
    };

    const renderChart = () => {
      switch (chartType) {
        case 'pie':
          return renderPieChart();
        case 'doughnut':
          return renderDoughnutChart();
        case 'line':
          return renderLineChart();
        case 'bar':
        default:
          return renderBarChart();
      }
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
      <div className="mt-4 bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900 text-lg">
            {chartData.options?.plugins?.title?.text || 'Analytics Chart'}
          </h4>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            {getChartTypeIcon()}
            <span className="capitalize">{chartType} Chart</span>
            <span>•</span>
            <span>{data.length} data points</span>
          </div>
        </div>
        
        <div className="chart-container">
          {renderChart()}
        </div>
        
        <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
          <span>Chart Type: {chartType.charAt(0).toUpperCase() + chartType.slice(1)}</span>
          <span>Generated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    );
  };

  // Message Component with Feedback
  const MessageWithFeedback = ({ message }) => {
    const [showFeedback, setShowFeedback] = useState(false);
    const [feedbackGiven, setFeedbackGiven] = useState(false);

    const quickFeedback = async (isHelpful) => {
      if (!message.queryId) return;

      try {
        await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query_id: message.queryId,
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
      <div className="space-y-4">
        <div className="text-gray-800 whitespace-pre-wrap">{message.content}</div>
        
        {message.chartData && <ChartDisplay chartData={message.chartData} />}

        {message.validation && <ValidationDisplay validation={message.validation} />}

        {message.queryId && (
          <div className="mt-4 pt-3 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Was this answer helpful?</span>
              
              {!feedbackGiven ? (
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => quickFeedback(true)}
                    className="flex items-center space-x-1 px-3 py-1 text-green-600 hover:bg-green-50 rounded-md transition-colors"
                    title="Yes, this was helpful"
                  >
                    <ThumbsUp className="h-4 w-4" />
                    <span className="text-sm">Yes</span>
                  </button>
                  
                  <button
                    onClick={() => quickFeedback(false)}
                    className="flex items-center space-x-1 px-3 py-1 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    title="No, this needs improvement"
                  >
                    <ThumbsDown className="h-4 w-4" />
                    <span className="text-sm">No</span>
                  </button>
                  
                  <button
                    onClick={() => setShowFeedback(true)}
                    className="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded-md transition-colors text-sm"
                  >
                    Detailed Feedback
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm">Thank you for your feedback!</span>
                </div>
              )}
            </div>

            <div className="mt-2 text-xs text-gray-400">
              Query ID: {message.queryId} | 
              Confidence: {message.validation?.confidence || 'unknown'} | 
              Score: {message.validation ? Math.round(message.validation.overall_score * 100) : 0}%
            </div>
          </div>
        )}

        <FeedbackModal
          isOpen={showFeedback}
          onClose={() => setShowFeedback(false)}
          queryId={message.queryId}
          currentAnswer={message.content}
        />
      </div>
    );
  };

  const handleSubmit = async () => {
    if (query.trim()) {
      setSubmittedQuery(query);
      setIsProcessing(true);
      
      try {
        const response = await fetch('http://localhost:5000/api/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: query
          })
        });
        
        if (response.ok) {
          const result = await response.json();
          console.log('Your backend result:', result);
          
          setAnalysisResult(result);
          setShowResponse(true);
        } else {
          console.error('Analytics API error:', response.status);
          alert('Failed to process your analytics query. Please try again.');
        }
      } catch (error) {
        console.error('Error connecting to your backend:', error);
        alert('Cannot connect to analytics backend. Please ensure your Flask server is running on port 5000.');
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  const handleSuggestedActionClick = (label) => {
    const queryMap = {
      'Sales Analysis': 'Compare smartphone vs laptop sales performance this quarter',
      'Customer Insights': 'Show me customer segmentation analysis and purchasing patterns by region',
      'Revenue Trends': 'Analyze revenue trends over the past 6 months with forecasting',
      'Product Performance': 'Which products are performing best and what are the key success factors?',
      'Market Analysis': 'Compare our market performance against industry benchmarks'
    };
    
    setQuery(queryMap[label] || label);
    setIsActive(true);
  };

  const handleBackToSearch = () => {
    setShowResponse(false);
    setQuery('');
    setSubmittedQuery('');
    setIsActive(false);
    setIsProcessing(false);
    setAnalysisResult(null);
  };

  const handleFollowUp = (followUpQuery) => {
    setQuery(followUpQuery);
    handleSubmit();
  };

  // Response interface with ALL your original features
  if (showResponse && analysisResult) {
    return (
      <div className="flex-1 min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-8 py-6">
          {/* Header with query title */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-medium text-gray-900 mb-2">{submittedQuery}</h1>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center justify-center space-x-8 mb-8">
            <button className="pb-2 border-b-2 border-blue-500 text-blue-600 font-medium">
              Answer
            </button>
            <button className="pb-2 text-gray-500 hover:text-gray-700">
              Images
            </button>
            <button className="pb-2 text-gray-500 hover:text-gray-700 flex items-center space-x-1">
              <span>Sources</span>
              <span className="text-xs">• {analysisResult.sources?.length || 0}</span>
            </button>
            <button className="pb-2 text-gray-500 hover:text-gray-700">
              Steps
            </button>
          </div>

          {/* Main Content Area */}
          <div className="space-y-8">
            {/* Analytics Results with ALL your original features */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 text-center mb-4">
                Business Analytics Results
              </h2>
              <p className="text-gray-600 text-center mb-6">
                Below is a comprehensive analysis of your business data from MongoDB with 
                AI-powered insights, validation, and interactive charts.
              </p>

              {/* Display using MessageWithFeedback to get ALL features */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <MessageWithFeedback 
                  message={{
                    content: analysisResult.summary || analysisResult.answer,
                    chartData: analysisResult.chart_data,
                    queryId: analysisResult.query_id,
                    validation: analysisResult.validation
                  }}
                />
              </div>
            </div>

            {/* Follow-up Input */}
            <div className="bg-white">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Ask a follow-up question..."
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100 pr-12"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.target.value.trim()) {
                      handleFollowUp(e.target.value);
                      e.target.value = '';
                    }
                  }}
                />
                <button className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600">
                  <Search className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Back to Search Button */}
            <div className="text-center">
              <button
                onClick={handleBackToSearch}
                className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                ← Start New Analysis
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main search interface - EXACT same styling as conversational-ai
  return (
    <div className="flex-1 min-h-screen bg-white flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        {/* Main Logo/Title */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-normal text-gray-900 mb-3">
            Analytics AI
          </h1>
          <p className="text-gray-500 text-lg">
            Ask questions about your business data
          </p>
          {/* System Status */}
          {stats && (
            <div className="flex items-center justify-center space-x-4 mt-4 text-sm">
              <div className={`flex items-center space-x-1 ${stats.services?.database === 'available' ? 'text-green-600' : 'text-red-600'}`}>
                <div className={`w-2 h-2 rounded-full ${stats.services?.database === 'available' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>Database {stats.services?.database === 'available' ? 'Connected' : 'Offline'}</span>
              </div>
              <div className={`flex items-center space-x-1 ${stats.services?.gemini === 'available' ? 'text-green-600' : 'text-yellow-600'}`}>
                <div className={`w-2 h-2 rounded-full ${stats.services?.gemini === 'available' ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                <span>AI {stats.services?.gemini === 'available' ? 'Enhanced' : 'Fallback'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Main Search Input */}
        <div className="mb-8">
          <div className="relative">
            <div className={`
              relative rounded-xl border transition-all duration-200 bg-white
              ${isActive || query 
                ? 'border-gray-300 shadow-lg' : 'border-gray-200 shadow-sm'}
            `}>
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setIsActive(true);
                }}
                onFocus={() => setIsActive(true)}
                onBlur={() => setIsActive(false)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about sales, customers, revenue, products..."
                disabled={isProcessing}
                className="w-full px-4 py-4 text-gray-900 placeholder-gray-500 bg-transparent border-0 rounded-xl focus:outline-none focus:ring-0 pr-16"
              />
              
              <button
                onClick={handleSubmit}
                disabled={!query.trim() || isProcessing}
                className={`
                  absolute right-3 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-all duration-200
                  ${query.trim() && !isProcessing
                    ? 'bg-teal-600 text-white hover:bg-teal-700 shadow-sm' 
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {isProcessing ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>

            {/* Bottom Toolbar */}
            <div className="flex items-center justify-between mt-3 px-2">
              <div className="flex items-center space-x-2">
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors" disabled={isProcessing}>
                  <Search className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors" disabled={isProcessing}>
                  <Image className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors" disabled={isProcessing}>
                  <MapPin className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors" disabled={isProcessing}>
                  <Paperclip className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors" disabled={isProcessing}>
                  <Mic className="w-4 h-4" />
                </button>
                <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center space-x-1">
                  <div className="w-1 h-2 bg-white rounded-full animate-pulse"></div>
                  <div className="w-1 h-3 bg-white rounded-full animate-pulse" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-1 h-4 bg-white rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-1 h-2 bg-white rounded-full animate-pulse" style={{animationDelay: '0.3s'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Suggested Actions */}
        <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
          {suggestedActions.map((action, index) => {
            const IconComponent = action.icon;
            return (
              <button
                key={index}
                onClick={() => handleSuggestedActionClick(action.label)}
                disabled={isProcessing}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-full border transition-all duration-200 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed
                  ${action.color}
                `}
              >
                <IconComponent className="w-4 h-4" />
                <span className="text-sm font-medium">{action.label}</span>
              </button>
            );
          })}
        </div>

        {/* Processing Status */}
        {isProcessing && (
          <div className="text-center mb-8">
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg border border-blue-200">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm font-medium">Analyzing your business data with multi-chart support...</span>
            </div>
          </div>
        )}

        {/* Feature Highlights */}
        {!isProcessing && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
              Advanced Analytics Features
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <BarChart3 className="h-5 w-5 text-blue-600" />
                </div>
                <div className="text-sm font-medium text-gray-900">Multi-Chart Support</div>
                <div className="text-xs text-gray-500">Bar, Pie, Line Charts</div>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div className="text-sm font-medium text-gray-900">Answer Validation</div>
                <div className="text-xs text-gray-500">Confidence Scoring</div>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Star className="h-5 w-5 text-yellow-600" />
                </div>
                <div className="text-sm font-medium text-gray-900">User Feedback</div>
                <div className="text-xs text-gray-500">Rate & Improve</div>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <TrendingUp className="h-5 w-5 text-purple-600" />
                </div>
                <div className="text-sm font-medium text-gray-900">Real-time Data</div>
                <div className="text-xs text-gray-500">Live MongoDB</div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-xs text-gray-400">
          <p>Analytics AI can make mistakes. Please verify important business decisions with source data.</p>
          <div className="flex items-center justify-center space-x-4 mt-2 text-xs text-gray-300">
            <span className="flex items-center space-x-1">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
              <span>Multi-chart support</span>
            </span>
            <span className="flex items-center space-x-1">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
              <span>Answer validation</span>
            </span>
            <span className="flex items-center space-x-1">
              <div className="w-1.5 h-1.5 bg-purple-400 rounded-full"></div>
              <span>User feedback system</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainChatInterface;