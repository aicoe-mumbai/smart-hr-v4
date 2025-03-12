import React, { useState, useRef, useEffect } from "react";
import "./SmartGoalForm.css";
import loadingGif from "../assets/__Iphone-spinner-1.gif";
import aicoelogo from "../assets/AICoE logo transparent.png";


const SmartGoalForm = () => {
  const apiUrl = process.env.REACT_APP_API_URL;
  const token = sessionStorage.getItem("access_token");
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
    startDate: "",
    endDate: ""
  });


  const thrustAreas = {
    "TA-1 Core Values": [
      "1.1 Conduct business in line with L&T’s philosophy of “Mission Zero Harm” and “Carbon and Water Neutrality”"
    ],
    "TA-2 Customer Focus": [
      "2.1 Nurture customer relationship through engagement at multiple levels"
    ],
    "TA-3 Business Growth": [
      "3.1 Improve on budgeted targets for Order Inflow, Earnings, Cash flow, Working Capital and Revenue",
      "3.2 Achieve significant YoY improvement in key performance metrics - OTD, FTR, PEI, PAT/Manhour"
    ],
    "TA-4 Strategy and Org Excellence": [
      "4.1 Implement Sankalp roadmaps and arrive at strategic plans for Lakshya 31 for business transformation and growth",
      "4.2 Productivity and quality improvement through Organisational excellence initiatives",
      "4.3 Proliferate use of AI and advanced digital technologies in our products and day to day processes",
      "4.4 Value chain control through IP creation, indigenization and building robust supply chain"
    ],
    "TA-5 Work Culture and Employee Engagement": [
      "5.1 Enable culture of openness, inclusivity and psychologically safe work environment",
      "5.2 Enhance employee engagement to drive high performance and productivity",
      "5.3 Focus on upskilling / reskilling to stay ahead in the emerging business environment"
    ]
  };

  const [selectedThrust, setSelectedThrust] = useState("");
  const [selectedSubCategory, setSelectedSubCategory] = useState("");
  const [showFinalGoalCheckbox, setShowFinalGoalCheckbox] = useState(false);
  const [isFinalGoal, setIsFinalGoal] = useState(false);


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

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [htmlResponse]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setHtmlResponse("");
    setShowFinalGoalCheckbox(false);
    setLoading(true);

    // Ensure quantifiableObjective does not exceed 100%
    if (formData.quantifiableObjective > 100) {
      setHtmlResponse("<p>Quantifiable Objective cannot exceed 100%.</p>");
      setLoading(false);
      return;
    }

    const formattedData = {
      goal: formData.goal,
      measure_of_success: formData.measureOfSuccess,
      kpi_metrics: formData.kpiMetrics,
      outcome_defined: formData.outcomeDefined,
      quantifiable_objective: formData.quantifiableObjective,
      skills_available: formData.skillsAvailable,
      obstacles_considered: formData.obstaclesConsidered,
      thrust_area: formData.thrustArea,
      sub_category: formData.subCategory,
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
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let htmlContent = "";
      setLoading(false);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        if (chunk.includes("[DONE]")) break;

        htmlContent += chunk;
        setHtmlResponse(htmlContent);
      }
      setShowFinalGoalCheckbox(true);

    } catch (error) {
      console.error("Error submitting form:", error.message);
      setHtmlResponse("<p>An error occurred while submitting the form.</p>");
    } finally {
      setLoading(false);
    }
  };



// const handleFinalGoalChange = async (event) => {
//   const checked = event.target.checked;
//   setIsFinalGoal(checked);

//   if (checked) {
//     try {
//       const response = await fetch(`${apiUrl}/api/final-goal/`, {
//         method: "POST",
//         headers: {
//           Authorization: `Bearer ${token}`,
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ final_goal_confirmed: true }), 
//       });

//       if (!response.ok) {
//         console.error("Error confirming final goal:", await response.text());
//       }
//     } catch (error) {
//       console.error("Error:", error);
//     }
//   }
// };
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
        goal_id: null, 
        final_goal_confirmed: isChecked 
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Something went wrong");
    }

    alert("Final goal confirmed successfully!");
  } catch (error) {
    console.error("Error:", error);
    alert("Failed to confirm the final goal.");
  }
};

  return (
    <div className="background-container">

      <div className="smart-form-container">
        <h2>Goal Assist</h2>
        <img src={aicoelogo} alt="SmartHR Logo" className="aicoe-img" />

        <form onSubmit={handleSubmit} className="smart-form">
          <label>Goal:</label>
          <textarea name="goal" value={formData.goal} onChange={handleChange} rows="3" required></textarea>

          <label>Measure of Success:</label>
          <textarea name="measureOfSuccess" value={formData.measureOfSuccess} onChange={handleChange} rows="3" required></textarea>

          <label>What metrics or KPI’s will be used to evaluate the achievement?</label>
          <textarea name="kpiMetrics" value={formData.kpiMetrics} onChange={handleChange} rows="3" required></textarea>

          <label>Can you clearly define the outcome or result?</label>
          <select name="outcomeDefined" value={formData.outcomeDefined} onChange={handleChange} required>
            <option value="">Select</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>

          <label>Can the objective be quantified (Nos., %ages etc.)?</label>
          <input
            type="number"
            name="quantifiableObjective"
            value={formData.quantifiableObjective}
            onChange={handleChange}
            required
            min={0}
            max={100}
            step={0.10}
          />

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

          {/* <label>Choose the Thrust Area this objective aligns with:</label>
        <select name="thrustArea" value={formData.thrustArea} onChange={handleChange} required>
          <option value="">Select</option>
          <option value="Innovation">Innovation</option>
          <option value="Customer Satisfaction">Customer Satisfaction</option>
          <option value="Operational Efficiency">Operational Efficiency</option>
        </select> */}


          <div>
            {/* Main Thrust Area Dropdown */}
            <label>Choose the Thrust Area this objective aligns with:</label>
            <select name="thrustArea" value={selectedThrust} onChange={handleThrustChange} required>
              <option value="">Select</option>
              {Object.keys(thrustAreas).map((thrust, index) => (
                <option key={index} value={thrust}>
                  {thrust}
                </option>
              ))}
            </select>

            {/* Dynamic Subcategory Dropdown */}
            {selectedThrust && (
              <>
                <label>Select a sub-category:</label>
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

          <label>Start Date of Activity:</label>
          <input type="date" name="startDate" value={formData.startDate} onChange={handleChange} required />

          <label>End Date of Activity:</label>
          <input type="date" name="endDate" value={formData.endDate} onChange={handleChange} required />

          <div className="response">
            {loading ? (
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
                <img src={loadingGif} alt="Loading..." style={{ width: "50px", height: "50px" }} />
              </div>

            ) : (
              <div
                className="html-response"

                dangerouslySetInnerHTML={{ __html: htmlResponse }}
              />
            )}
            <div ref={bottomRef} />

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
          <button type="submit" className="submit-btn">Analyse Goal</button>
        </form>
      </div>
    </div>
  );
};

export default SmartGoalForm;
