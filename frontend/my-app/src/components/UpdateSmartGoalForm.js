import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import loadingGif from "../assets/__Iphone-spinner-1.gif";


const UpdateSmartGoalForm = () => {
  const { goalId } = useParams();
  const navigate = useNavigate();
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
    endDate: "",
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

  const groupObjectives = {
    "Environment, Safety, Sustainability & Governance": [
      "Ensure 100% safe operations (nil reportable incidents) across all functions and work centres, with focus on RSC and BBS.",
      "Ensure operations that drive sustainable development of the Organisation, Society & Environment, with a target of 5% improvement Y-o-Y in achieving water consumption, energy efficiency improvement Y-o-Y of 2.5% and achieve renewable energy substitution target of 50%.",
      "Effective implementation of Audit recommendations.",
      "Ensure Zero incidents with regards to Information Security Breach and compliance to ILDC security guidelines.",
      "Uphold highest standards of governance across all operations for sustainable business excellence."
    ],
    "Financial Parameters": [
      "Exceed OI by at least 10% over the budget.",
      "Target Exports at 10% of Total Budgeted OI.",
      "Meet/Exceed Quarter wise budget of Sales, PAT, Progress billing, Collections, NWC, Revenue per employee and PAT per man hour.",
      "Reduce controllable revenue expenses by 5% as compared to budget.",
      "Reduce slow and non-moving inventory by at least 25%. Liquidation of Inventory for all closed projects within one quarter of the end of warranty period of project.",
      "Collect all overdue customer outstanding more than 90 days."
    ],
    "Operational Excellence": [
      "Target 100% OTD (zero LD) for all project milestones defined in ERP LN.",
      "Establish a system driven measurement for FTR and achieve >96% internal FTR and >98% external FTR across all functions.",
      "Achieve and sustain a reducing trend in NCR by 15% (YoY).",
      "Institutionalize robust contract, cost and risk management practices by implementing Cost fact and Active risk management (ARM) for all contracts valuing ≥ 50 Crs.",
      "Leverage Digitalization and Industry 4.0 to drive efficiency and business growth to achieve ROI and Cycle Time reduction.",
      "Implementation of AI interventions in at least 5 identified areas in each function.",
      "Ensure timely closure of projects in ERP system - within 2 months of completion of all contractual obligations."
    ],
    "R&D and Design": [
      "Develop roadmaps and business cases for new technology adoption.",
      "Ensure all R&D projects planned for the FY meet defined milestones and are executed within sanctioned budget.",
      "File at least 4 patents in TIC and 1 each in every D&DC.",
      "Implement Automation and AI driven processes to cut down Design Cycle Time across all projects by 50%.",
      "Strengthen R&D through crowdsourcing, collaborative research, and partnerships with start-ups and academia to drive innovation and accelerate development."
    ],
    "Organisational Excellence": [
      "Project Sankalp: Implement business roadmaps with focus on Internationalisation and Value chain control.",
      "Project Parivartan: Synergize existing and initiate new Parivartan initiatives in line with Sankalp roadmaps and implement the same.",
      "Design and Deliver Lakshya-31 plan for achieving business growth objectives and creating sustainable value through Innovation and Market leadership.",
      "Target 'Role Model' category in L&T Business Excellence Model and HR Excellence Model.",
      "Sustain and digitalise CMMI practices across organisation, covering all projects with >50 Cr. contract value.",
      "Secure ‘Excellence Recognitions’ in business/ operations from CII, FICCI, etc.",
      "Secure at least one international/ national safety excellence award by every work centre."
    ],
    "Customer Delight": [
      "Log all Customer complaints in CFAR system and ensure closure in a focused manner, with 25% Y-o-Y reduction in average cycle time.",
      "Implementation of CRM system - Track and achieve an increasing trend in number of customer interactions/meetings for proactively understanding their needs and acting upon them.",
      "Continue to register all Customers Feedbacks in Pratibimbh quarterly and achieve increasing trend in customer centricity."
    ],
    "Work Culture and Employee Engagement": [
      "Create a conducive culture which enables higher level of engagement and reduce attrition by 25% YoY across departments.",
      "Achieve GPTW score of >85 and Amber score of >82 across the locations and functions, by implementation of feedbacks received from workforce.",
      "Enhance Gender Diversity to 14% at IC level with focus on work centers, Equity and Inclusion in the workforce.",
      "Focus on upskilling / reskilling to stay ahead in the emerging business environment, including at least 1 course on artificial intelligence by each employee."
    ]
  };

  
    const [selectedObjective, setSelectedObjective] = useState("");
    const [selectedObjectiveSubCategory, setSelectedObjectiveSubCategory] = useState("");
  
  const [loading, setLoading] = useState(true);
  const [loadingforGif, setLoadingforGif] = useState(false);
  const [htmlResponse, setHtmlResponse] = useState("");
  const bottomRef = useRef(null);
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [htmlResponse]);


  const [selectedThrust, setSelectedThrust] = useState("");
  const [selectedSubCategory, setSelectedSubCategory] = useState("");
  const [showFinalGoalCheckbox, setShowFinalGoalCheckbox] = useState(false);
  const [isFinalGoal, setIsFinalGoal] = useState(false);

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

  useEffect(() => {
    const fetchGoalData = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/update-goals/${goalId}/`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) throw new Error("Failed to fetch goal");

        const data = await response.json();
        setFormData({
          goal: data.goal,
          measureOfSuccess: data.measure_of_success,
          kpiMetrics: data.kpi_metrics,
          outcomeDefined: data.outcome_defined,
          quantifiableObjective: data.quantifiable_objective,
          skillsAvailable: data.skills_available,
          obstaclesConsidered: data.obstacles_considered,
          thrustArea: data.thrust_area,
          subCategory: data.sub_category,
          groupObjective: data.group_objectives,
          subgroupObjectiveCategory: data.additional_sub_category,
          startDate: data.start_date,
          endDate: data.end_date,
        });
        setSelectedThrust(data.thrust_area || "");
        setSelectedSubCategory(data.sub_category || "");
        setSelectedObjective(data.group_objectives || "");
        setSelectedObjectiveSubCategory(data.additional_sub_category || "");
        setLoading(false);
      } catch (error) {
        console.error("Error fetching goal data:", error);
      }
    };

    fetchGoalData();
  }, [apiUrl, goalId, token]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setHtmlResponse("");
    setShowFinalGoalCheckbox(false);
    setLoadingforGif(true);

    // Ensure quantifiableObjective does not exceed 100%
    if (formData.quantifiableObjective > 100) {
      setHtmlResponse("<p>Quantifiable Objective cannot exceed 100%.</p>");
      setLoadingforGif(false);
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
      group_objectives: formData.groupObjective,
      additional_sub_category: formData.subgroupObjectiveCategory,
      start_date: formData.startDate,
      end_date: formData.endDate,
      goalId: goalId || "",
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
      setLoadingforGif(false);

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
      setLoadingforGif(false);
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
        goal_id: goalId, 
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
    <div className="smart-form-container">
      <h2>Edit Goal Assist</h2>
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
          <img src={loadingGif} alt="Loading..." style={{ width: "50px", height: "50px" }} />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="smart-form">
          <label>Goal:</label>
          <textarea name="goal" value={formData.goal} onChange={handleChange} rows="3" required />

          <label>Measure of Success:</label>
          <textarea name="measureOfSuccess" value={formData.measureOfSuccess} onChange={handleChange} rows="3" required />

          <label>What metrics or KPI’s will be used to evaluate the achievement?</label>
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

          <label>Start Date of Activity:</label>
          <input type="date" name="startDate" value={formData.startDate} onChange={handleChange} required />

          <label>End Date of Activity:</label>
          <input type="date" name="endDate" value={formData.endDate} onChange={handleChange} required />


          <div className="response">
            {loadingforGif ? (
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
      )}
    </div>
  );
};

export default UpdateSmartGoalForm;
