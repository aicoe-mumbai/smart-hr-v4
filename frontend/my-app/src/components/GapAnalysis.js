import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './GapAnalysis.css';

const GapAnalysis = () => {
  const [goals, setGoals] = useState([]);
  const [selectedGoals, setSelectedGoals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const apiUrl = process.env.REACT_APP_API_URL;
  const encodedUsername = sessionStorage.getItem('username');
  const token = sessionStorage.getItem('access_token');
  const navigate = useNavigate();

  const fetchUserGoals = useCallback(async () => {
    if (!encodedUsername || !apiUrl) {
      setError('Missing authentication or configuration');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Add token if available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // Fetch ALL goals by setting a high page_size
      const response = await fetch(`${apiUrl}/api/user-goals/?loginUser=${encodedUsername}&page_size=1000`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch goals');
      }
      
      const data = await response.json();
      console.log('✅ Goals fetched successfully:', data.results?.length, 'goals');
      console.log('Goals data:', data.results);
      setGoals(data.results || []);
    } catch (err) {
      console.error('Error fetching goals:', err);
      setError('Failed to load goals. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, encodedUsername, token]);

  useEffect(() => {
    console.log('=== GapAnalysis Debug ===');
    console.log('Username:', encodedUsername);
    console.log('API URL:', apiUrl);
    console.log('Token:', token);
    fetchUserGoals();
  }, [fetchUserGoals]);

  const handleGoalSelection = (goalId, event) => {
    // Prevent double-toggle when clicking the checkbox
    if (event) {
      event.stopPropagation();
    }
    setSelectedGoals(prev => {
      if (prev.includes(goalId)) {
        return prev.filter(id => id !== goalId);
      } else {
        return [...prev, goalId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedGoals.length === goals.length) {
      setSelectedGoals([]);
    } else {
      setSelectedGoals(goals.map(g => g.id));
    }
  };

  const analyzeGaps = async () => {
    if (selectedGoals.length === 0) {
      alert('Please select at least one goal to analyze');
      return;
    }

    if (!encodedUsername || !apiUrl) {
      setError('Missing authentication or configuration');
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Add token if available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${apiUrl}/api/goals/gap-analysis/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          loginUser: encodedUsername,
          goal_ids: selectedGoals
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Failed to analyze gaps');
      }
      
      const data = await response.json();
      setAnalysisResult(data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 5000);
    } catch (err) {
      console.error('Error analyzing gaps:', err);
      setError(err.message || 'Failed to analyze gaps. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const getCoverageClass = (percentage) => {
    if (percentage >= 75) return 'high';
    if (percentage >= 50) return 'medium';
    return 'low';
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'success': return '✅';
      default: return 'ℹ️';
    }
  };

  if (loading) {
    return (
      <div className="gap-analysis-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading your goals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="gap-analysis-container">
      <div className="gap-analysis-header">
        <div>
          <h1>📊 Goal Gap Analysis</h1>
          <p>Analyze your goals against company Thrust Areas and Group Objectives</p>
        </div>
        <button 
          onClick={() => navigate('/')}
          style={{
            background: '#2ecc71',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px'
          }}
        >
          🏠 Return to Home
        </button>
      </div>

      {error && (
        <div style={{ 
          background: '#fff5f5', 
          color: '#e74c3c', 
          padding: '15px', 
          borderRadius: '8px', 
          marginBottom: '20px',
          border: '1px solid #fadbd8'
        }}>
          {error}
        </div>
      )}

      {saveSuccess && (
        <div style={{ 
          background: '#d4edda', 
          color: '#155724', 
          padding: '15px', 
          borderRadius: '8px', 
          marginBottom: '20px',
          border: '1px solid #c3e6cb',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '20px' }}>✅</span>
          <span><strong>Gap Analysis Saved Successfully!</strong> Your analysis has been recorded and you can now proceed with your goals.</span>
        </div>
      )}

      {/* Goal Selection Section */}
      <div className="goal-selection-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>Select Goals to Analyze</h2>
          <button 
            onClick={handleSelectAll}
            style={{
              background: 'transparent',
              border: '2px solid #3498db',
              color: '#3498db',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            {selectedGoals.length === goals.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        {goals.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <h3>No Goals Found</h3>
            <p>You haven't submitted any goals yet. Create your first goal to start the analysis.</p>
          </div>
        ) : (
          <>
            <div className="goals-list">
              {goals.map(goal => (
                <div 
                  key={goal.id}
                  className={`goal-item ${selectedGoals.includes(goal.id) ? 'selected' : ''}`}
                >
                  <input
                    type="checkbox"
                    className="goal-checkbox"
                    checked={selectedGoals.includes(goal.id)}
                    onChange={(e) => handleGoalSelection(goal.id, e)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="goal-content" onClick={() => handleGoalSelection(goal.id, null)}>
                    <div className="goal-text">{goal.goal}</div>
                    <div className="goal-meta">
                      <span>🎯 <strong>TA:</strong> {goal.thrust_area || 'N/A'}</span>
                      <span>📋 <strong>GO:</strong> {goal.group_objectives || 'N/A'}</span>
                      <span>🏢 <strong>BU:</strong> {goal.user_bu || 'N/A'}</span>
                      <span>📅 {goal.start_date} to {goal.end_date}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <button 
              className="analyze-button"
              onClick={analyzeGaps}
              disabled={selectedGoals.length === 0 || analyzing}
            >
              {analyzing ? 'Analyzing...' : `Analyze ${selectedGoals.length} Selected Goal${selectedGoals.length !== 1 ? 's' : ''}`}
            </button>
          </>
        )}
      </div>

      {/* Analysis Results */}
      {analyzing && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Analyzing your goals against company objectives...</p>
        </div>
      )}

      {analysisResult && !analyzing && (
        <div className="analysis-results">
          {/* LLM Strategic Insights */}
          {analysisResult.llm_insights && (
            <div className="llm-insights-section">
              <h2>🤖 AI Strategic Analysis</h2>
              
              {/* Overall Assessment */}
              <div className="insight-card">
                <h3>📊 Overall Assessment</h3>
                <p>{analysisResult.llm_insights.overall_assessment}</p>
              </div>

              {/* Strengths and Gaps */}
              <div className="coverage-grid">
                <div className="insight-card">
                  <h3>✅ Strengths</h3>
                  <ul>
                    {analysisResult.llm_insights.strengths?.map((strength, idx) => (
                      <li key={idx}>{strength}</li>
                    ))}
                  </ul>
                </div>
                <div className="insight-card">
                  <h3>⚠️ Critical Gaps</h3>
                  <ul>
                    {analysisResult.llm_insights.critical_gaps?.map((gap, idx) => (
                      <li key={idx}>{gap}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Strategic Recommendations */}
              {analysisResult.llm_insights.strategic_recommendations?.length > 0 && (
                <div className="insight-card">
                  <h3>🎯 Strategic Recommendations</h3>
                  {analysisResult.llm_insights.strategic_recommendations.map((rec, idx) => (
                    <div key={idx} className="strategic-rec-item">
                      <div className="rec-header">
                        <span className={`priority-badge ${rec.priority.toLowerCase()}`}>{rec.priority} Priority</span>
                        <span className="area-badge">{rec.area}</span>
                      </div>
                      <p className="rec-text"><strong>Recommendation:</strong> {rec.recommendation}</p>
                      <p className="rec-rationale"><strong>Rationale:</strong> {rec.rationale}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Balance and Risk Analysis */}
              <div className="coverage-grid">
                <div className="insight-card">
                  <h3>⚖️ Balance Analysis</h3>
                  <p>{analysisResult.llm_insights.balance_analysis}</p>
                </div>
                <div className="insight-card">
                  <h3>🔍 Risk Assessment</h3>
                  <p>{analysisResult.llm_insights.risk_assessment}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GapAnalysis;
