import React, { useState, useEffect } from "react";
import "./PreviousValidations.css";
import { useNavigate } from "react-router-dom";

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
      const response = await fetch(`${apiUrl}api/user-goals/${goalId}/delete/`, {
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

  
  useEffect(() => {
    fetchUserGoals();
  }, [apiUrl, token, currentPage, fetchUserGoals]);
  
  return (
    <div className="previous-validations-container">
      <h2 className="table-heading">Previous Validations</h2>
      <table className="validations-table">
        <thead>
          <tr>
            <th>S.No</th>
            <th>Goal</th>
            <th>Response</th>
            <th>Final Goal</th> {/* New column */}
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
              <td colSpan="6" className="no-data">No goals found</td>
            </tr>
          )}
        </tbody>
      </table>

      {/* Pagination Controls */}
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
