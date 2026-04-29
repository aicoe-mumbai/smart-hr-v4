import React, { useState, useEffect, useCallback } from "react";
import "./PreviousValidations.css";
import { useNavigate } from "react-router-dom";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { FaDownload, FaCopy, FaFileAlt } from "react-icons/fa";
import loadingGif from "../assets/loading-7528_256.gif";
import { UserGuideButton } from './UserGuide';


const PreviousValidations = () => {
  const [activeTab, setActiveTab] = useState('goals');
  const [userGoals, setUserGoals] = useState([]);
  const [gapAnalyses, setGapAnalyses] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const token = sessionStorage.getItem("access_token");
  const apiUrl = process.env.REACT_APP_API_URL;
  const navigate = useNavigate();
  const username = sessionStorage.getItem("username");
  const [loading, setLoading] = useState(false);
  const [gapAnalysisRequired, setGapAnalysisRequired] = useState(false);

  // Debug logging
  useEffect(() => {
    console.log('=== PreviousValidations Debug ===');
    console.log('Username from sessionStorage:', username);
    console.log('API URL:', apiUrl);
    console.log('Token:', token);
    if (!username) {
      console.error('❌ Username is missing! Redirecting to login...');
      navigate('/login');
    }
  }, [username, apiUrl, token, navigate]);

  const fetchGapAnalyses = useCallback(async () => {
    if (!username || !apiUrl) {
      console.log('⚠️ fetchGapAnalyses: Missing required data', { username, apiUrl });
      return;
    }
    setLoading(true);
    console.log('Fetching gap analyses for:', username);
    try {
      const headers = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      
      const response = await fetch(`${apiUrl}/api/gap-analysis-history/?loginUser=${username}`, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        throw new Error("Failed to fetch gap analyses");
      }

      const data = await response.json();
      console.log('✅ Gap analyses fetched:', data.length);
      setGapAnalyses(data);
    } catch (error) {
      console.error("❌ Error fetching gap analyses:", error);
      setGapAnalyses([]);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, username, token]);

  const fetchUserGoals = useCallback(async () => {
    if (!username || !apiUrl) {
      console.log('⚠️ fetchUserGoals: Missing required data', { username, apiUrl });
      return;
    }
    setLoading(true);
    console.log('Fetching user goals for:', username);
    try {
      const headers = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      
      const response = await fetch(`${apiUrl}/api/user-goals/?page=${currentPage}&username=${username}`, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        throw new Error("Failed to fetch user goals");
      }

      const data = await response.json();
      console.log('✅ User goals fetched:', data.count, 'total,', data.results?.length, 'on this page');
      setUserGoals(data.results || []);
      setTotalPages(Math.ceil(data.count / 10)); // Assuming 10 items per page
      
      // Check if gap analysis is required
      const confirmedGoals = (data.results || []).filter(goal => goal.final_goal === "True");
      if (confirmedGoals.length > 0) {
        // Check if gap analysis has been done
        const gapCheckResponse = await fetch(`${apiUrl}/api/gap-analysis-status/?loginUser=${username}`, {
          method: "GET",
          headers,
        });
        if (gapCheckResponse.ok) {
          const gapData = await gapCheckResponse.json();
          setGapAnalysisRequired(!gapData.has_gap_analysis);
        }
      }
    } catch (error) {
      console.error("❌ Error fetching user goals:", error);
      setUserGoals([]);
    } finally {
      setLoading(false);
    }
  }, [currentPage, apiUrl, username, token]);

  const handleDelete = async (goalId) => {
    if (!window.confirm("Are you sure you want to delete this goal?")) return;

    try {
      const response = await fetch(`${apiUrl}/api/user-goals/${goalId}/delete/?loginUser=${encodeURIComponent(username)}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        alert("Goal deleted successfully!");
        setUserGoals((prevGoals) => prevGoals.filter((goal) => goal.id !== goalId));
      } else {
        alert("Failed to delete goal.");
      }
    } catch (error) {
      console.error("Error deleting goal:", error);
      alert("Error deleting goal. Check the console for details.");
    }
  };

  const exportToExcel = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/user-goals/?loginUser=${encodeURIComponent(username)}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`, // Ensure the token is valid
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) throw new Error("Failed to fetch data");

      const data = await response.json();

      if (!data.results || data.results.length === 0) {
        alert("No goals to export.");
        return;
      }

      // Function to strip HTML tags from text
      const stripHtmlTags = (html) => {
        if (!html) return '';
        return html.replace(/<[^>]*>/g, "").trim();
      };

      // Extract the "results" array and modify the structure
      const goals = data.results.map((goal, index) => ({
        "Serial Number": index + 1, // Assign serial number starting from 1
        Goal: goal.goal,
        "Measure of Success": goal.measure_of_success,
        "KPI Metrics": goal.kpi_metrics,
        "Outcome Defined": goal.outcome_defined,
        "Quantifiable Objective": goal.quantifiable_objective,
        "Skills Available": goal.skills_available,
        "Obstacles Considered": goal.obstacles_considered,
        "Thrust Area": goal.thrust_area,
        "Sub Category": goal.sub_category,
        "Group Objectives": goal.group_objectives,
        "Sub Category Group Objectives": goal.additional_sub_category,
        "Start Date": goal.start_date,
        "End Date": goal.end_date,
        "SMARTness Response": stripHtmlTags(goal.response), // Strip HTML tags
        "Final Goal": goal.final_goal,
      }));

      // Convert JSON to a worksheet
      const worksheet = XLSX.utils.json_to_sheet(goals);

      // Set column width to 300px
      worksheet["!cols"] = new Array(Object.keys(goals[0]).length).fill({ wpx: 120 });

      // Set row height to 300px
      worksheet["!rows"] = new Array(goals.length + 1).fill({ hpx: 40 });

      // Apply text wrapping to all cells
      Object.keys(worksheet).forEach((cell) => {
        if (cell[0] !== "!") {
          worksheet[cell].s = {
            alignment: {
              wrapText: true,
              vertical: "center", // Center content vertically
              horizontal: "left", // Align left
            },
          };
        }
      });

      // Create a workbook and add the worksheet
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "User Goals");

      // Convert to a Blob and trigger download
      const excelBuffer = XLSX.write(workbook, { bookType: "xlsx", type: "array" });
      const dataBlob = new Blob([excelBuffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });

      saveAs(dataBlob, "UserGoals.xlsx");
      alert("Goals exported successfully!");
    } catch (error) {
      console.error("Error exporting data:", error);
      alert("Failed to export goals. Please try again.");
    }
  };

  const copyGoalToClipboard = (goalText) => {
    if (!goalText) {
      alert("No goal text to copy.");
      return;
    }
    
    // Check if clipboard API is available
    if (!navigator.clipboard) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = goalText;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        alert("Goal copied to clipboard!");
      } catch (err) {
        console.error("Error copying text: ", err);
        alert("Failed to copy goal. Please try again.");
      }
      document.body.removeChild(textArea);
      return;
    }
    
    navigator.clipboard.writeText(goalText)
      .then(() => {
        alert("Goal copied to clipboard!");
      })
      .catch((err) => {
        console.error("Error copying text: ", err);
        alert("Failed to copy goal. Please try again.");
      });
  };

  const saveGoalAsText = (goal) => {
    const goalDetails = `
Goal: ${goal.goal}
Measure of Success: ${goal.measure_of_success}
KPI Metrics: ${goal.kpi_metrics}
Outcome Defined: ${goal.outcome_defined}
Quantifiable Objective: ${goal.quantifiable_objective}
Skills Available: ${goal.skills_available}
Obstacles Considered: ${goal.obstacles_considered}
Thrust Area: ${goal.thrust_area}
Sub Category: ${goal.sub_category}
Group Objectives: ${goal.group_objectives}
Sub Category Group Objectives: ${goal.additional_sub_category}
Start Date: ${goal.start_date}
End Date: ${goal.end_date}
    `;
    
    const blob = new Blob([goalDetails], { type: "text/plain;charset=utf-8" });
    saveAs(blob, `goal-${goal.id}.txt`);
  };

  useEffect(() => {
    if (activeTab === 'goals') {
      fetchUserGoals();
    } else if (activeTab === 'gap-analysis') {
      fetchGapAnalyses();
    }
  }, [activeTab, currentPage]);

  return (
    <div className="previous-validations-container">
      {gapAnalysisRequired && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '15px 20px',
          borderRadius: '8px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
        }}>
          <div>
            <strong>⚠️ Gap Analysis Required</strong>
            <p style={{ margin: '5px 0 0 0', fontSize: '0.9rem' }}>
              You have confirmed goals but haven't run Gap Analysis yet. Please analyze your goals to ensure comprehensive coverage.
            </p>
          </div>
          <button
            onClick={() => navigate('/gap-analysis')}
            style={{
              background: 'white',
              color: '#667eea',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            Run Gap Analysis
          </button>
        </div>
      )}
      
      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'goals' ? 'active' : ''}`}
          onClick={() => setActiveTab('goals')}
        >
          📋 My Goals
        </button>
        <button 
          className={`tab-btn ${activeTab === 'gap-analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('gap-analysis')}
        >
          📊 Gap Analysis History
        </button>
      </div>

      {activeTab === 'goals' ? (
        <>
          <div className="table-header">
            <h2 className="table-heading">Previous Validations</h2>
            <div className="actions-container">
              <UserGuideButton />
              <button className="export-btn" onClick={exportToExcel}>
                <FaDownload size={20} />
              </button>
            </div>
          </div>
          <table className="validations-table">
        <thead>
          <tr>
            <th>S.No</th>
            <th>Goal</th>
            <th>Response</th>
            <th>Final</th>
            <th>Edit</th>
            <th>Delete</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan="7" className="no-data">
                <img src={loadingGif} alt="Loading..." className="loading-icon-table" />
              </td>
            </tr>
          ) : userGoals.length === 0 ? (
            <tr>
              <td colSpan="7" className="no-data">No Validations Found</td>
            </tr>
          ) : (
            userGoals.map((goal, index) => (
              <tr key={goal.id}>
                <td>{(currentPage - 1) * 10 + index + 1}</td>
                <td className="goal-text">{goal.goal}</td>
                <td className="response-text">
                  <div dangerouslySetInnerHTML={{ __html: goal.response }} />
                </td>
                <td className="final-goal">
                  {goal.final_goal === "True" ? (
                    <span className="checkmark">✔️</span>
                  ) : (
                    <span className="crossmark">❌</span>
                  )}
                </td>
                <td>
                  <button className="edit-btn" onClick={() => navigate(`/update-goal/${goal.id}`)}>
                    Edit
                  </button>
                </td>
                <td>
                  <button className="delete-btn" onClick={() => handleDelete(goal.id)}>
                    Delete
                  </button>
                </td>
                <td className="action-buttons">
                  <button 
                    className="copy-btn" 
                    title="Copy Goal"
                    onClick={() => copyGoalToClipboard(goal.goal)}>
                    <FaCopy size={16} />
                  </button>
                  <button 
                    className="save-text-btn" 
                    title="Save Goal as Text"
                    onClick={() => saveGoalAsText(goal)}>
                    <FaFileAlt size={16} />
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
          </table>

          {/* Pagination & Export Buttons */}
          <div className="pagination">
            <button
              className="pagination-btn"
              onClick={() => {
                setCurrentPage((prev) => Math.max(prev - 1, 1));
                window.scrollTo({ top: 0, behavior: "smooth" }); // Scroll to top
              }}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <span>Page {currentPage} of {totalPages}</span>
            <button
              className="pagination-btn"
              onClick={() => {
                setCurrentPage((prev) => Math.min(prev + 1, totalPages));
                window.scrollTo({ top: 0, behavior: "smooth" }); // Scroll to top
              }}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="gap-analysis-history">
          <div className="table-header">
            <h2 className="table-heading">Gap Analysis History</h2>
            <button 
              className="new-analysis-btn"
              onClick={() => navigate('/gap-analysis')}
            >
              + New Analysis
            </button>
          </div>
          
          {loading ? (
            <div className="no-data">
              <img src={loadingGif} alt="Loading..." className="loading-icon-table" />
            </div>
          ) : gapAnalyses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No Gap Analysis Found</h3>
              <p>You haven't run any gap analysis yet.</p>
              <button 
                className="run-analysis-btn"
                onClick={() => navigate('/gap-analysis')}
              >
                Run Your First Analysis
              </button>
            </div>
          ) : (
            <div className="gap-analysis-cards">
              {gapAnalyses.map((analysis, index) => (
                <div key={analysis.id} className="gap-analysis-card">
                  <div className="card-header">
                    <div className="card-title">
                      <span className="analysis-number">Analysis #{gapAnalyses.length - index}</span>
                      <span className="analysis-date">{new Date(analysis.analysis_date).toLocaleString()}</span>
                    </div>
                    <div className="card-stats">
                      <span className="stat-badge goals-badge">{analysis.goals_count} Goals</span>
                    </div>
                  </div>
                  
                  <div className="coverage-summary">
                    <div className="coverage-item">
                      <span className="coverage-label">TA Coverage</span>
                      <div className="coverage-bar-container">
                        <div 
                          className="coverage-bar" 
                          style={{
                            width: `${analysis.ta_coverage}%`,
                            background: analysis.ta_coverage >= 75 ? '#27ae60' : analysis.ta_coverage >= 50 ? '#f39c12' : '#e74c3c'
                          }}
                        ></div>
                      </div>
                      <span className="coverage-percentage">{analysis.ta_coverage.toFixed(1)}%</span>
                    </div>
                    
                    <div className="coverage-item">
                      <span className="coverage-label">GO Coverage</span>
                      <div className="coverage-bar-container">
                        <div 
                          className="coverage-bar" 
                          style={{
                            width: `${analysis.go_coverage}%`,
                            background: analysis.go_coverage >= 75 ? '#27ae60' : analysis.go_coverage >= 50 ? '#f39c12' : '#e74c3c'
                          }}
                        ></div>
                      </div>
                      <span className="coverage-percentage">{analysis.go_coverage.toFixed(1)}%</span>
                    </div>
                  </div>
                  
                  {analysis.analysis_result?.llm_insights && (
                    <div className="insights-preview">
                      <h4>🤖 AI Insights</h4>
                      <p className="insight-text">
                        {analysis.analysis_result.llm_insights.overall_assessment?.substring(0, 150)}...
                      </p>
                      <details className="insights-details">
                        <summary>View Full Analysis</summary>
                        <div className="full-insights">
                          <div className="insight-section">
                            <strong>Overall Assessment:</strong>
                            <p>{analysis.analysis_result.llm_insights.overall_assessment}</p>
                          </div>
                          
                          {analysis.analysis_result.llm_insights.strengths?.length > 0 && (
                            <div className="insight-section">
                              <strong>✅ Strengths:</strong>
                              <ul>
                                {analysis.analysis_result.llm_insights.strengths.map((s, i) => (
                                  <li key={i}>{s}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {analysis.analysis_result.llm_insights.critical_gaps?.length > 0 && (
                            <div className="insight-section">
                              <strong>⚠️ Critical Gaps:</strong>
                              <ul>
                                {analysis.analysis_result.llm_insights.critical_gaps.map((g, i) => (
                                  <li key={i}>{g}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {analysis.analysis_result.llm_insights.strategic_recommendations?.length > 0 && (
                            <div className="insight-section">
                              <strong>🎯 Strategic Recommendations:</strong>
                              {analysis.analysis_result.llm_insights.strategic_recommendations.map((rec, i) => (
                                <div key={i} className="recommendation-item">
                                  <span className={`priority-tag ${rec.priority.toLowerCase()}`}>{rec.priority}</span>
                                  <span className="area-tag">{rec.area}</span>
                                  <p><strong>Recommendation:</strong> {rec.recommendation}</p>
                                  <p><strong>Rationale:</strong> {rec.rationale}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PreviousValidations;
