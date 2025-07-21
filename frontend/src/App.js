import React, { useState, useEffect } from 'react';
import { BarChart3, ThumbsUp, ThumbsDown, AlertTriangle, CheckCircle, Info, Star, Send, TrendingUp, Users, DollarSign, PieChart } from 'lucide-react';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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

  // Multi-Chart Display Component
  const ChartDisplay = ({ chartData }) => {
    if (!chartData || !chartData.data) return null;

    const { labels, datasets } = chartData.data;
    const data = datasets[0]?.data || [];
    const maxValue = Math.max(...data.filter(val => typeof val === 'number'));
    const chartType = chartData.type || 'bar';

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
      console.log('Rendering chart type:', chartType, 'with data:', data);
      
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
      <div className="mt-4 bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
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
      <div className={`p-4 rounded-lg ${message.type === 'user' ? 'bg-blue-100 ml-12' : 'bg-white border'}`}>
        {message.type === 'user' ? (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
              U
            </div>
            <p className="text-blue-900">{message.content}</p>
          </div>
        ) : (
          <div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                AI
              </div>
              <div className="flex-1">
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
            </div>
          </div>
        )}
      </div>
    );
  };

  // Main query processing function
  const handleSubmit = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!currentQuery.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: currentQuery,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    const queryText = currentQuery;
    setCurrentQuery('');

    (async () => {
      try {
        const response = await fetch('http://localhost:5000/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: queryText })
        });

        const data = await response.json();

        if (response.ok) {
          const aiMessage = {
            type: 'ai',
            content: data.summary,
            chartData: data.chart_data,
            queryId: data.query_id,
            validation: data.validation,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, aiMessage]);
        } else {
          const errorMessage = {
            type: 'ai',
            content: `Error: ${data.error}`,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } catch (error) {
        const errorMessage = {
          type: 'ai',
          content: 'Failed to connect to the server. Please check if the backend is running.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    })();
  };

  // Enhanced suggested queries with chart type indicators
  const suggestedQueries = [
    {
      query: "Compare smartphone vs laptop sales performance",
      type: "bar",
      icon: <BarChart3 className="h-4 w-4" />,
      description: "Bar chart comparison"
    },
    {
      query: "Show me customer distribution by segment",
      type: "pie",
      icon: <PieChart className="h-4 w-4" />,
      description: "Pie chart breakdown"
    },
    {
      query: "Show me sales revenue by category",
      type: "doughnut",
      icon: <PieChart className="h-4 w-4" />,
      description: "Doughnut chart"
    },
    {
      query: "Show me monthly sales trends for 2024",
      type: "line",
      icon: <TrendingUp className="h-4 w-4" />,
      description: "Line chart trends"
    },
    {
      query: "What were our top 5 selling products this quarter?",
      type: "bar",
      icon: <BarChart3 className="h-4 w-4" />,
      description: "Bar chart ranking"
    },
    {
      query: "Show me inventory levels for low-stock products",
      type: "bar",
      icon: <BarChart3 className="h-4 w-4" />,
      description: "Horizontal bars"
    }
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
                <p className="text-sm text-gray-500">Ask questions with multi-chart support and validation</p>
              </div>
            </div>
            
            {/* Stats Display */}
            {stats && (
              <div className="hidden md:flex space-x-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-600 flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 mr-1" />
                    {stats.services?.database === 'available' ? 'Online' : 'Offline'}
                  </div>
                  <div className="text-xs text-gray-500">System Status</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600 flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 mr-1" />
                    AI
                  </div>
                  <div className="text-xs text-gray-500">
                    {stats.services?.gemini === 'available' ? 'Enhanced' : 'Fallback'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Enhanced Suggested Queries Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                <Info className="h-5 w-5 mr-2 text-blue-500" />
                Try These Questions
              </h3>
              <div className="space-y-3">
                {suggestedQueries.map((item, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuery(item.query)}
                    className="w-full text-left p-3 text-sm text-gray-600 hover:bg-blue-50 hover:text-blue-700 rounded-lg border border-transparent hover:border-blue-200 transition-all duration-200 group"
                  >
                    <div className="flex items-start space-x-2">
                      <div className="text-gray-400 group-hover:text-blue-500 mt-0.5">
                        {item.icon}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{item.query}</div>
                        <div className="text-xs text-gray-400 group-hover:text-blue-400 mt-1">
                          {item.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Chart Types Info */}
            <div className="bg-white rounded-lg shadow-sm p-4 mt-4">
              <h4 className="font-medium text-gray-800 mb-3">Supported Chart Types</h4>
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-3">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                  <div>
                    <div className="font-medium text-gray-700">Bar Charts</div>
                    <div className="text-xs text-gray-500">Rankings, comparisons</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <PieChart className="h-4 w-4 text-green-500" />
                  <div>
                    <div className="font-medium text-gray-700">Pie Charts</div>
                    <div className="text-xs text-gray-500">Distributions, breakdowns</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <PieChart className="h-4 w-4 text-purple-500" />
                  <div>
                    <div className="font-medium text-gray-700">Doughnut Charts</div>
                    <div className="text-xs text-gray-500">Category revenue splits</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <TrendingUp className="h-4 w-4 text-orange-500" />
                  <div>
                    <div className="font-medium text-gray-700">Line Charts</div>
                    <div className="text-xs text-gray-500">Trends over time</div>
                  </div>
                </div>
              </div>
            </div>

            {/* System Features */}
            <div className="bg-white rounded-lg shadow-sm p-4 mt-4">
              <h4 className="font-medium text-gray-800 mb-3">System Features</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Multi-chart support</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Answer validation</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Confidence scoring</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>User feedback</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Performance monitoring</span>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm">
              {/* Messages Area - Full height to bottom of screen */}
              <div className="overflow-y-auto p-6 space-y-4" style={{ height: 'calc(100vh - 300px)' }}>
                {messages.length === 0 ? (
                  <div className="text-center text-gray-500 mt-8">
                    <div className="flex justify-center space-x-4 mb-4">
                      <BarChart3 className="h-8 w-8 text-blue-300" />
                      <PieChart className="h-8 w-8 text-green-300" />
                      <TrendingUp className="h-8 w-8 text-orange-300" />
                    </div>
                    <p className="text-lg font-medium">Welcome to Multi-Chart Analytics!</p>
                    <p className="text-sm mt-2">Ask questions about your data and get the perfect chart type automatically.</p>
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-700">
                        <strong>New:</strong> Support for bar charts, pie charts, doughnut charts, and line charts with automated validation.
                      </p>
                    </div>
                    
                    {/* Quick examples */}
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="flex items-center space-x-2 mb-2">
                          <BarChart3 className="h-4 w-4 text-blue-500" />
                          <span className="text-sm font-medium">Bar Charts</span>
                        </div>
                        <p className="text-xs text-gray-600">Try: "Top 5 selling products" or "Sales by region"</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="flex items-center space-x-2 mb-2">
                          <PieChart className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium">Pie Charts</span>
                        </div>
                        <p className="text-xs text-gray-600">Try: "Customer distribution by segment"</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="flex items-center space-x-2 mb-2">
                          <PieChart className="h-4 w-4 text-purple-500" />
                          <span className="text-sm font-medium">Doughnut Charts</span>
                        </div>
                        <p className="text-xs text-gray-600">Try: "Revenue by category"</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="flex items-center space-x-2 mb-2">
                          <TrendingUp className="h-4 w-4 text-orange-500" />
                          <span className="text-sm font-medium">Line Charts</span>
                        </div>
                        <p className="text-xs text-gray-600">Try: "Monthly sales trends"</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  messages.map((message, index) => (
                    <MessageWithFeedback key={index} message={message} />
                  ))
                )}
                
                {isLoading && (
                  <div className="bg-white border rounded-lg p-4">
                    <div className="flex items-center space-x-3">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                      <span className="text-gray-600">Processing your query and selecting the best chart type...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="border-t p-6">
                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={currentQuery}
                    onChange={(e) => setCurrentQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSubmit(e)}
                    placeholder="Ask a question about your data..."
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={isLoading || !currentQuery.trim()}
                    className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                  >
                    <Send className="h-4 w-4" />
                    <span>{isLoading ? 'Processing...' : 'Ask'}</span>
                  </button>
                </div>
                <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span>Multi-chart support</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <BarChart3 className="h-3 w-3 text-blue-500" />
                    <span>Automatic chart selection</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="h-3 w-3 text-yellow-500" />
                    <span>Rate answers to improve quality</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;