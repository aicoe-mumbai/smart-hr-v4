import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./SmartGoalForm.css";
import loadingGif from "../assets/__Iphone-spinner-1.gif";
import aicoelogo from "../assets/AICoE logo transparent.png";
import { FaCopy, FaFileAlt } from "react-icons/fa";
import { saveAs } from "file-saver";
import { UserGuideButton } from "./UserGuide";


const SmartGoalForm = () => {
  const navigate = useNavigate();
  const apiUrl = process.env.REACT_APP_API_URL;
  const token = sessionStorage.getItem("access_token");
  const loginUser = sessionStorage.getItem("username");
  
  // Redirect to login if user is not authenticated
  useEffect(() => {
    if (!loginUser || !apiUrl) {
      navigate('/login');
    }
  }, [loginUser, apiUrl, navigate]);
  const [formData, setFormData] = useState({
    goal: "",
    measureOfSuccess: "",
    kpiMetrics: "",
    outcomeDefined: "",
    quantifiableObjective: "",
    skillsAvailable: "",
    obstaclesConsidered: "",
    thrustArea: "",
    subCategory: "",
    userBu: "",
    crosslinkedBus: [],
    startDate: "",
    endDate: ""
  });

  const [availableBUs, setAvailableBUs] = useState([
    "AS-Aerospace",
    "Corporate Center",
    "EPS", 
    "F&A",
    "Hazira Manufacturing",
    "HR",
    "IT & Digital",
    "LPES",
    "MPES",
    "SCM",
    "T&IC"
  ]);


  const thrustAreas = {
    "TA-1 Core Values": [
      "1.1 Conduct business in line with L&T's philosophy of 'Mission Zero Harm' and 'Carbon and Water Neutrality'"
    ],
    "TA-2 Customer Focus": [
      "2.1 Reinforce market credibility by deepening customer relationships, ensuring delivery reliability, and creating superior customer delight"
    ],
    "TA-3 Business Growth": [
      "3.1 Improve on budgeted targets for Order Inflow, Earnings, Cash flow, Working Capital and Revenue",
      "3.2 Prioritize excellence in On-Time Delivery (OTD) while driving sustained YoY improvements in FTR, PEI, and PAT/Manhour",
      "3.3 Focus on improved GWC and FCF through faster Build–Bill–Collect Execution cycle",
      "3.4 Ensure reliable and timely product delivery through accelerated clearance of the past backlog"
    ],
    "TA-4 Strategy and Org Excellence": [
      "4.1 Support Lakshya 31 targets through innovation-led growth by academia & start-up integration and future-focused development in-house",
      "4.2 Productivity and quality improvement driven by automation and structured Organisational Excellence initiatives",
      "4.3 Enable enterprise-wide digital transformation through SAP implementation and large-scale deployment of Gen AI solutions",
      "4.4 Strengthen value chain resilience by developing proprietary IP, advancing indigenization, and ensuring robust and secure sourcing ecosystems. Increase value chain control by at least 10%"
    ],
    "TA-5 Work Culture and Employee Engagement": [
      "5.1 Enable organizational excellence by strengthening overall employee engagement through leadership connect, open communication, recognition and psychologically safe work environment",
      "5.2 Enhance gender diversity and inclusivity across roles while promoting an equitable work environment",
      "5.3 Strengthen workforce readiness by addressing critical skill gaps and scaling capabilities to meet evolving business needs"
    ]
  };

  const groupObjectives = {
    "Environment, Safety, Sustainability & Governance": [
      "1a) Ensure 100% safe operations (nil reportable incidents) across all functions, work centres and sites with focus on Vision Know Harm Campaign",
      "1b) Ensure operations that drive sustainable development of the Organisation, Society & Environment, with a target of 5% improvement Y-o-Y in achieving water consumption, energy efficiency improvement Y-o-Y of 2.5% and achieve renewable energy substitution target of 50%",
      "1c) Strengthen governance through effective implementation of audit recommendations across all operations for sustainable business Excellence",
      "1d) Institute a robust IC-wide review mechanism. Ensure cross-pollination of audit observations across functions to achieve nil High-Risk Observations",
      "1e) Ensure Zero incidents with regards to Information Security Breach and compliance to ILDC security guidelines",
      "1f) Strengthen ESG adoption across the organization through training, awareness, and bring accountability at the team level"
    ],
    "Financial Parameters": [
      "2a) Exceed OI by at least 10% over the budget",
      "2b) Drive Export OI to outperform the budget by a minimum of 10%",
      "2c) Exceed Quarter wise budget of Sales, PAT, Progress billing, Collections, NWC and PAT per man hour",
      "2d) Reduce controllable revenue expenses by 5% as compared to budget",
      "2e) Reduce slow and non-moving inventory, closed project inventory by at least 25%. Ensure liquidation of Inventory for all closed projects within one quarter of the end of warranty period of project",
      "2f) Bring down current average overdue customer outstanding from 44 days to 33 days of Trailing 12 months of sales (25% Improvement)"
    ],
    "Operational Excellence": [
      "3a) Target 100% OTD (zero LD) for all project milestones defined in ERP LN except for developmental projects",
      "3b) Adopt system driven measurement for FTR (in production contracts) and achieve >96% internal FTR and >98% external FTR across all functions. Develop and Institutionalise system driven FTR measurement for all Development Projects",
      "3c) Achieve and sustain a reducing trend in NCR by 15% (YoY)",
      "3d) Institutionalize robust contract, cost and risk management practices by implementing Cost fact and Active risk management (ARM) for all contracts valuing ≥ 50 Crs",
      "3e) Accelerate digitalization and AI adoption by implementing AI interventions across at least five areas in each function, enhancing process efficiency by eliminating non-value-added activities, and achieving a 10% improvement in cycle time and PAT per manhour vis-à-vis budget",
      "3f) Ensure timely closure of projects in ERP system - within 2 months of completion of all contractual obligations"
    ],
    "Technology & Innovation": [
      "4a) Identify and develop roadmaps, backed by business cases, for adoption of new strategic technologies aligned with future business opportunities",
      "4b) Ensure all R&D projects planned for the FY meet defined milestones and are executed within sanctioned budget",
      "4c) Accelerate execution of priority technology programs (e.g., lasers, semiconductors, aero engines, etc.) by defining gated milestones and achieving them in a time-bound manner through partnerships, and prototype development",
      "4d) Strengthen the company's IP portfolio through patents, copyrights, industrial design registrations, and structured knowledge/IP repositories, including at least 4 TIC patents and 1 patent from each BU design Center",
      "4e) Implement Automation and AI driven processes to cut down Design Cycle Time across all projects by 50%",
      "4f) Obtain RDI funding of 100Cr for identified projects"
    ],
    "Organisational Excellence": [
      "5a) Define & Execute Project Sankalp tracks for: 1) Growing Strategic Partnerships with DPSUs, FOEMs & Technology Partners with an impetus on higher workshare, IP creation and enhanced value chain control. 2) Consolidation of domain specific operations for creating Centers of Manufacturing Excellence leading to higher indigenisation / in-house production",
      "5d) Target Role Model category in L&T Business Excellence Model and HR Excellence Model",
      "5e) Sustain and digitalise CMMI practices across organisation, covering all projects with >50 Cr. contract value",
      "5f) Secure Excellence Recognitions in business/ operations from CII, FICCI, etc",
      "5g) Secure at least one international/ national safety excellence award by every work centre"
    ],
    "Customer Delight": [
      "6a) Log all Customer complaints in CFAR system and ensure closure in a focused manner, with 25% Y-o-Y reduction in average cycle time"
    ],
    "Work Culture and Employee Engagement": [
      "7a) Create a conducive culture which enables higher level of engagement and productivity. Improve employee retention by 2%",
      "7b) Implement atleast 80% of plans identified by Abhivyakti Taskforces",
      "7c) Target GPTW score of >90 across the locations and functions by implementation of feedbacks received from workforce",
      "7d) Enhance Gender Diversity to 15% at IC level with focus on work centers, equity and inclusion in the workforce",
      "7e) Focus on upskilling / reskilling to stay ahead in the emerging business environment, including at least 1 course on artificial intelligence by each employee"
    ]
  };

  const [selectedThrust, setSelectedThrust] = useState("");
  const [selectedSubCategory, setSelectedSubCategory] = useState("");
  const [showFinalGoalCheckbox, setShowFinalGoalCheckbox] = useState(false);
  const [isFinalGoal, setIsFinalGoal] = useState(false);
  const [showAllGoalsSubmittedCheckbox, setShowAllGoalsSubmittedCheckbox] = useState(false);
  const [allGoalsSubmitted, setAllGoalsSubmitted] = useState(false);

  const [selectedObjective, setSelectedObjective] = useState("");
  const [selectedObjectiveSubCategory, setSelectedObjectiveSubCategory] = useState("");

  const handleObjectiveChange = (event) => {
    const value = event.target.value;
    setSelectedObjective(value);
    setSelectedObjectiveSubCategory("");  // Reset subcategory

    setFormData((prevData) => ({
      ...prevData,
      groupObjective: value,
      subgroupObjectiveCategory: "",
    }));
  };

  const handleObjectiveSubCategoryChange = (event) => {
    const value = event.target.value;
    setSelectedObjectiveSubCategory(value);

    setFormData((prevData) => ({
      ...prevData,
      subgroupObjectiveCategory: value,
    }));
  };


  const handleThrustChange = (event) => {
    const value = event.target.value;
    setSelectedThrust(value);
    setSelectedSubCategory("");

    setFormData((prevData) => ({
      ...prevData,
      thrustArea: value,
      subCategory: "",
    }));
  };

  const handleSubCategoryChange = (event) => {
    const value = event.target.value;
    setSelectedSubCategory(value);

    setFormData((prevData) => ({
      ...prevData,
      subCategory: value,
    }));
  };


  const [htmlResponse, setHtmlResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [wsError, setWsError] = useState(false);

  useEffect(() => {
    // Listen for WebSocket errors
    const handleWsError = (event) => {
      if (event.message && event.message.includes('wss://goalassist.ltdic.com:3000/ws failed')) {
        setWsError(true);
      }
    };

    window.addEventListener('error', handleWsError);
    
    return () => {
      window.removeEventListener('error', handleWsError);
    };
  }, []);

  useEffect(() => {
    if (htmlResponse && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [htmlResponse]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const copyGoalToClipboard = () => {
    if (!formData.goal) {
      alert("No goal to copy. Please enter a goal first.");
      return;
    }
    
    // Check if clipboard API is available
    if (!navigator.clipboard) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = formData.goal;
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
    
    navigator.clipboard.writeText(formData.goal)
      .then(() => {
        alert("Goal copied to clipboard!");
      })
      .catch((err) => {
        console.error("Error copying text: ", err);
        alert("Failed to copy goal. Please try again.");
      });
  };

  const saveGoalAsText = () => {
    if (!formData.goal) {
      alert("No goal details to save. Please enter goal information first.");
      return;
    }
    
    const goalDetails = `
Goal: ${formData.goal}
Measure of Success: ${formData.measureOfSuccess}
KPI Metrics: ${formData.kpiMetrics}
Outcome Defined: ${formData.outcomeDefined}
Quantifiable Objective: ${formData.quantifiableObjective}
Skills Available: ${formData.skillsAvailable}
Obstacles Considered: ${formData.obstaclesConsidered}
Thrust Area: ${formData.thrustArea}
Sub Category: ${formData.subCategory}
Group Objectives: ${formData.groupObjective}
Sub Category Group Objectives: ${formData.subgroupObjectiveCategory}
Start Date: ${formData.startDate}
End Date: ${formData.endDate}
    `;
    
    const blob = new Blob([goalDetails], { type: "text/plain;charset=utf-8" });
    saveAs(blob, `goal-draft.txt`);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setHtmlResponse("");
    setShowFinalGoalCheckbox(false);
    setLoading(true);
    setIsSubmitting(true);

    // Validate quantifiable objective
    const quantObj = parseFloat(formData.quantifiableObjective);
    if (isNaN(quantObj) || quantObj < 0 || quantObj > 100) {
      setHtmlResponse("<p>Quantifiable Objective must be a number between 0 and 100.</p>");
      setLoading(false);
      setIsSubmitting(false);
      return;
    }

    // Validate dates
    if (formData.startDate && formData.endDate) {
      const start = new Date(formData.startDate);
      const end = new Date(formData.endDate);
      if (end <= start) {
        setHtmlResponse("<p>End date must be after start date.</p>");
        setLoading(false);
        setIsSubmitting(false);
        return;
      }
    }

    const formattedData = {
      loginUser:loginUser,
      goal: formData.goal,
      measure_of_success: formData.measureOfSuccess,
      kpi_metrics: formData.kpiMetrics,
      outcome_defined: formData.outcomeDefined,
      quantifiable_objective: formData.quantifiableObjective,
      skills_available: formData.skillsAvailable,
      obstacles_considered: formData.obstaclesConsidered,
      thrust_area: formData.thrustArea,
      sub_category: formData.subCategory,
      group_objectives: formData.groupObjective,
      additional_sub_category: formData.subgroupObjectiveCategory,
      user_bu: formData.userBu,
      crosslinked_bus: formData.crosslinkedBus,
      start_date: formData.startDate,
      end_date: formData.endDate,
    };

    try {
      const response = await fetch(`${apiUrl}/api/submit-goal/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formattedData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        setHtmlResponse(`<p>Error: ${errorText}</p>`);
        setLoading(false);
        setIsSubmitting(false);
        return;
      }

      // Try to get the full text response first, since streaming might be failing
      try {
        const fullText = await response.text();
        // Remove [DONE] marker if present
        const cleanedText = fullText.replace('[DONE]', '');
        setHtmlResponse(cleanedText);
        setShowFinalGoalCheckbox(true);
        setShowAllGoalsSubmittedCheckbox(true);
        setIsSubmitting(false);
        setLoading(false);
      } catch (streamError) {
        console.error("Error with text response, falling back to stream:", streamError);
        // Fall back to streaming approach if text() fails
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let htmlContent = "";
        setLoading(false);

        while (true) {
          try {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            if (chunk.includes("[DONE]")) break;

            htmlContent += chunk;
            setHtmlResponse(htmlContent);
          } catch (readError) {
            console.error("Error reading stream chunk:", readError);
            break;
          }
        }
        setShowFinalGoalCheckbox(true);
        setShowAllGoalsSubmittedCheckbox(true);
        setIsSubmitting(false);
      }
    } catch (error) {
      console.error("Error submitting form:", error.message);
      setHtmlResponse("<p>An error occurred while submitting the form.</p>");
      setIsSubmitting(false);
      setLoading(false);
    }
  };


  const handleAllGoalsSubmittedChange = (e) => {
    const isChecked = e.target.checked;
    setAllGoalsSubmitted(isChecked);

    if (isChecked) {
      const confirmRedirect = window.confirm(
        "✅ You've indicated that all goals for the upcoming year have been submitted.\n\n" +
        "📊 You will now be redirected to the Gap Analysis page to analyze your goals.\n\n" +
        "⚠️ Note: You can always come back to submit more goals if needed.\n\n" +
        "Click OK to proceed to Gap Analysis, or Cancel to stay on this page."
      );

      if (confirmRedirect) {
        navigate('/gap-analysis');
      } else {
        setAllGoalsSubmitted(false);
      }
    }
  };

  const handleFinalGoalChange = async (e) => {
    const isChecked = e.target.checked;
    setIsFinalGoal(isChecked);


    try {
      const response = await fetch(`${apiUrl}/api/final-goal/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          loginUser: loginUser, 
          goal_id: null,
          final_goal_confirmed: isChecked
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
      }

      if (data.gap_analysis_required) {
        alert(
          "✅ Final goal confirmed successfully!\n\n" +
          "⚠️ IMPORTANT: You have confirmed goals but haven't run Gap Analysis yet.\n\n" +
          "📊 Please navigate to 'Gap Analysis' page to analyze all your confirmed goals against company Thrust Areas and Group Objectives.\n\n" +
          "This is mandatory to ensure comprehensive coverage of organizational priorities."
        );
      } else if (data.has_gap_analysis) {
        alert("✅ Final goal confirmed successfully! Gap Analysis already completed.");
      } else {
        alert("✅ Final goal confirmed successfully!");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to confirm the final goal.");
    }
  };

  return (
    <div className="background-container">
      <h2>Goal Assist</h2>
      <img src={aicoelogo} alt="SmartHR Logo" className="aicoe-img" />

      <div className="action-toolbar">
        <UserGuideButton />
        <button 
          className="modern-button copy-btn" 
          title="Copy Goal"
          onClick={copyGoalToClipboard}>
          <FaCopy size={16} /> <span>Copy Goal</span>
        </button>
        <button 
          className="modern-button save-btn" 
          title="Save Goal as Text"
          onClick={saveGoalAsText}>
          <FaFileAlt size={16} /> <span>Save as Text</span>
        </button>
      </div>
      
      <form onSubmit={handleSubmit} className="smart-form">
        <label>Goal:</label>
        <textarea name="goal" value={formData.goal} onChange={handleChange} rows="3" required />

        <label>Measure of Success:</label>
        <textarea name="measureOfSuccess" value={formData.measureOfSuccess} onChange={handleChange} rows="3" required />

        <label>What metrics or KPI's will be used to evaluate the achievement?</label>
        <textarea name="kpiMetrics" value={formData.kpiMetrics} onChange={handleChange} rows="3" required />

        <label>Can you clearly define the outcome or result?</label>
        <select name="outcomeDefined" value={formData.outcomeDefined} onChange={handleChange} required>
          <option value="">Select</option>
          <option value="Yes">Yes</option>
          <option value="No">No</option>
        </select>

        <label>Can the objective be quantified (Nos., %ages etc.)?</label>
        <input type="number" name="quantifiableObjective" value={formData.quantifiableObjective} onChange={handleChange} required min={0} max={100} step={0.10} />

        <label>Are the necessary skills, knowledge, and expertise available to achieve this objective?</label>
        <select name="skillsAvailable" value={formData.skillsAvailable} onChange={handleChange} required>
          <option value="">Select</option>
          <option value="Yes">Yes</option>
          <option value="No">No</option>
        </select>

        <label>Have you considered any potential obstacles/challenges?</label>
        <select name="obstaclesConsidered" value={formData.obstaclesConsidered} onChange={handleChange} required>
          <option value="">Select</option>
          <option value="Yes">Yes</option>
          <option value="No">No</option>
        </select>

        <div>
          <label>Choose the Thrust Area this objective aligns with:</label>
          <select name="thrustArea" value={selectedThrust} onChange={handleThrustChange} required>
            <option value="">Select</option>
            {Object.keys(thrustAreas).map((thrust, index) => (
              <option key={index} value={thrust}>
                {thrust}
              </option>
            ))}
          </select>

          {selectedThrust && (
            <>
              <label>Select a sub-category for Thrust Area:</label>
              <select
                name="subCategory"
                value={selectedSubCategory}
                onChange={handleSubCategoryChange}
                required
              >
                <option value="">Select</option>
                {thrustAreas[selectedThrust].map((sub, index) => (
                  <option key={index} value={sub}>
                    {sub}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>

        <div>
          <label htmlFor="groupObjective">Group Objective:</label>
          <select id="groupObjective" value={selectedObjective} onChange={handleObjectiveChange}>
            <option value="">Select Group Objective</option>
            {Object.keys(groupObjectives).map((objective) => (
              <option key={objective} value={objective}>{objective}</option>
            ))}
          </select>
        </div>

        {selectedObjective && (
          <div>
            <label htmlFor="objectiveSubCategory">Sub Category for Group Objectives:</label>
            <select
              id="objectiveSubCategory"
              value={selectedObjectiveSubCategory}
              onChange={handleObjectiveSubCategoryChange}
            >
              <option value="">Select Sub Category</option>
              {groupObjectives[selectedObjective].map((sub, index) => (
                <option key={index} value={sub}>{sub}</option>
              ))}
            </select>
          </div>
        )}

        <label>User's BU:</label>
        <select 
          name="userBu" 
          value={formData.userBu} 
          onChange={handleChange} 
          required
        >
          <option value="">Select Your BU</option>
          {availableBUs.map((bu, index) => (
            <option key={index} value={bu}>{bu}</option>
          ))}
        </select>

        <label>Cross-linked BUs (Select BUs with which your goals have cross linkage):</label>
        <div className="checkbox-group">
          {availableBUs.filter(bu => bu !== formData.userBu).map((bu, index) => (
            <div key={index} className="checkbox-item">
              <input
                type="checkbox"
                id={`bu-${index}`}
                value={bu}
                checked={formData.crosslinkedBus.includes(bu)}
                onChange={(e) => {
                  const value = e.target.value;
                  setFormData(prev => ({
                    ...prev,
                    crosslinkedBus: e.target.checked
                      ? [...prev.crosslinkedBus, value]
                      : prev.crosslinkedBus.filter(b => b !== value)
                  }));
                }}
              />
              <label htmlFor={`bu-${index}`}>{bu}</label>
            </div>
          ))}
        </div>

        <label>Start Date of Activity:</label>
        <input type="date" name="startDate" value={formData.startDate} onChange={handleChange} required />

        <label>End Date of Activity:</label>
        <input type="date" name="endDate" value={formData.endDate} onChange={handleChange} required />

        <div className="response">
          {wsError && (
            <div className="message error">
              <p>Note: WebSocket connection failed. Real-time updates may not work correctly. 
              The response will still be displayed when analysis is complete.</p>
            </div>
          )}
          {loading ? (
            <div className="loading-container">
              <img src={loadingGif} alt="Loading..." className="loading-icon" />
              <p>Analyzing your goal, please wait...</p>
            </div>
          ) : (
            <div 
              className="html-response" 
              dangerouslySetInnerHTML={{ __html: htmlResponse }} 
              style={{ 
                overflowY: 'visible', 
                width: '100%', 
                height: 'auto', 
                minHeight: '100px',
                display: 'block',
                wordWrap: 'break-word',
                whiteSpace: 'normal'
              }}
            />
          )}
          <div ref={bottomRef} />

          {showAllGoalsSubmittedCheckbox && (
            <div className="final-goal-checkbox" style={{ marginTop: '20px', padding: '15px', background: '#f0f8ff', borderRadius: '8px', border: '2px solid #3498db' }}>
              <input
                type="checkbox"
                id="allGoalsSubmitted"
                checked={allGoalsSubmitted}
                onChange={handleAllGoalsSubmittedChange}
              />
              <label htmlFor="allGoalsSubmitted" style={{ fontWeight: '600', color: '#2c3e50' }}>
                📊 Have you submitted all goals for the upcoming year?
              </label>
              <p style={{ margin: '10px 0 0 25px', fontSize: '0.9rem', color: '#7f8c8d' }}>
                Check this box if you've completed submitting all your goals. You'll be redirected to Gap Analysis.
              </p>
            </div>
          )}

          {showFinalGoalCheckbox && (
            <div className="final-goal-checkbox">
              <input
                type="checkbox"
                id="finalGoal"
                checked={isFinalGoal}
                onChange={handleFinalGoalChange}
              />
              <label htmlFor="finalGoal">Have you reviewed all the details above and confirmed this as your final goal?</label>
            </div>
          )}
        </div>

        <button 
          type="submit" 
          className="submit-btn" 
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Analyzing...' : 'Analyse Goal'}
        </button>
      </form>
    </div>
  );
};

export default SmartGoalForm;
