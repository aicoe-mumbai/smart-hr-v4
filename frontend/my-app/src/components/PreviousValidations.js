// import React, { useState, useEffect } from "react";
// import "./PreviousValidations.css";
// import { useNavigate } from "react-router-dom";

// const PreviousValidations = () => {
//   const [userGoals, setUserGoals] = useState([]);
//   const [currentPage, setCurrentPage] = useState(1);
//   const [totalPages, setTotalPages] = useState(1);
//   const token = sessionStorage.getItem("access_token");
//   const apiUrl = process.env.REACT_APP_API_URL;
//   const navigate = useNavigate();


//   const fetchUserGoals = async () => {
//     try {
//       const response = await fetch(`${apiUrl}/api/user-goals/?page=${currentPage}`, {
//         method: "GET",
//         headers: {
//           Authorization: `Bearer ${token}`,
//           "Content-Type": "application/json",
//         },
//       });

//       if (!response.ok) {
//         throw new Error("Failed to fetch user goals");
//       }

//       const data = await response.json();
//       setUserGoals(data.results);
//       setTotalPages(Math.ceil(data.count / 10)); // Assuming 10 items per page
//     } catch (error) {
//       console.error("Error:", error);
//       setUserGoals([]);
//     }
//   };

//   const handleDelete = async (goalId) => {
//     if (!window.confirm("Are you sure you want to delete this goal?")) return;

//     try {
//       const response = await fetch(`${apiUrl}api/user-goals/${goalId}/delete/`, {
//         method: "DELETE",
//         headers: {
//           Authorization: `Bearer ${token}`,
//           "Content-Type": "application/json",
//         },
//       });

//       if (response.ok) {
//         alert("Goal deleted successfully!");
//         setUserGoals((prevGoals) => prevGoals.filter((goal) => goal.id !== goalId));
//       } else {
//         alert("Failed to delete goal.");
//       }
//     } catch (error) {
//       console.error("Error deleting goal:", error);
//       alert("Error deleting goal. Check the console for details.");
//     }
//   };

  
//   useEffect(() => {
//     fetchUserGoals();
//   }, [apiUrl, token, currentPage, fetchUserGoals]);
  
//   return (
//     <div className="previous-validations-container">
//       <h2 className="table-heading">Previous Validations</h2>
//       <table className="validations-table">
//         <thead>
//           <tr>
//             <th>S.No</th>
//             <th>Goal</th>
//             <th>Response</th>
//             <th>Final Goal</th> {/* New column */}
//             <th>Edit</th>
//             <th>Delete</th>
//           </tr>
//         </thead>
//         <tbody>
//           {userGoals.length > 0 ? (
//             userGoals.map((goal, index) => (
//               <tr key={goal.id}>
//                 <td>{(currentPage - 1) * 10 + index + 1}</td>
//                 <td className="goal-text">{goal.goal}</td>
//                 <td className="response-text">
//                   <div dangerouslySetInnerHTML={{ __html: goal.response }} />
//                 </td>
//                 <td className="final-goal">
//                   {goal.final_goal === "True" ? (
//                     <span className="checkmark">✔️</span>
//                   ) : (
//                     <span className="crossmark">❌</span>
//                   )}

//                 </td>
//                 <td>
//                   <button className="edit-btn" onClick={() => navigate(`/update-goal/${goal.id}`)}>
//                     Edit
//                   </button>
//                 </td>
//                 <td>
//                   <button className="delete-btn" onClick={() => handleDelete(goal.id)}>
//                     Delete
//                   </button>
//                 </td>
//               </tr>
//             ))
//           ) : (
//             <tr>
//               <td colSpan="6" className="no-data">No goals found</td>
//             </tr>
//           )}
//         </tbody>
//       </table>

//       {/* Pagination Controls */}
//       <div className="pagination">
//         <button
//           className="pagination-btn"
//           onClick={() => {
//             setCurrentPage((prev) => Math.max(prev - 1, 1));
//             window.scrollTo({ top: 0, behavior: "smooth" }); // Scroll to top
//           }}
//           disabled={currentPage === 1}
//         >
//           Previous
//         </button>
//         <span>Page {currentPage} of {totalPages}</span>
//         <button
//           className="pagination-btn"
//           onClick={() => {
//             setCurrentPage((prev) => Math.min(prev + 1, totalPages));
//             window.scrollTo({ top: 0, behavior: "smooth" }); // Scroll to top
//           }}
//           disabled={currentPage === totalPages}
//         >
//           Next
//         </button>
//       </div>
//     </div>
//   );
// };

// export default PreviousValidations;



import React, { useState, useEffect } from "react";
import "./PreviousValidations.css";
import { useNavigate } from "react-router-dom";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { FaDownload } from "react-icons/fa";
import loadingGif from "../assets/loading-7528_256.gif";


const PreviousValidations = () => {
  const [userGoals, setUserGoals] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const token = sessionStorage.getItem("access_token");
  const apiUrl = process.env.REACT_APP_API_URL;
  const navigate = useNavigate();
  
  const fetchUserGoals = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/user-goals/?page=${currentPage}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch user goals");
      }

      const data = await response.json();
      setUserGoals(data.results);
      setTotalPages(Math.ceil(data.count / 10)); // Assuming 10 items per page
    } catch (error) {
      console.error("Error:", error);
      setUserGoals([]);
    }
  };

  const handleDelete = async (goalId) => {
    if (!window.confirm("Are you sure you want to delete this goal?")) return;

    try {
      const response = await fetch(`${apiUrl}/api/user-goals/${goalId}/delete/`, {
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
    const response = await fetch(`${apiUrl}/api/user-goals/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`, // Ensure the token is valid
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) throw new Error("Failed to fetch data");

    const data = await response.json();

    // Function to strip HTML tags from text
    const stripHtmlTags = (html) => html.replace(/<[^>]*>/g, "").trim();

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
  } catch (error) {
    console.error("Error exporting data:", error);
  }
};


  useEffect(() => {
    fetchUserGoals();
  }, [currentPage]);

  return (
    <div className="previous-validations-container">
      <div className="table-header">
        <h2 className="table-heading">Previous Validations</h2>
        <button className="export-btn" onClick={exportToExcel}>
        <FaDownload size={20} />
        </button>
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
          </tr>
        </thead>
        <tbody>
          {userGoals.length > 0 ? (
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
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6" className="no-data"> <img src={loadingGif} alt="Loading..." className="loading-icon-table" /></td>
            </tr>
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
    </div>
  );
};

export default PreviousValidations;
