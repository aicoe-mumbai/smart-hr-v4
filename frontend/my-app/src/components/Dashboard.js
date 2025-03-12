import React from "react";
import Navbar from "./Navbar";
import "./Dashboard.css";
import SmartGoalForm from "./SmartGoalForm";
import { useLocation, useParams } from "react-router-dom";
import PreviousValidations from "./PreviousValidations";
import UpdateSmartGoalForm from "./UpdateSmartGoalForm";


const Dashboard = ({ onLogout }) => {
  const location = useLocation();
  const { goalId } = useParams();

  return (
    <div className="dashboard-container">
      <Navbar onLogout={onLogout} />
      <div className="dashboard-content">
      {location.pathname.startsWith("/update-goal") ? (
          <UpdateSmartGoalForm goalId={goalId} />
        ) : location.pathname === "/previous-validations" ? (
          <PreviousValidations />
        ) : (
          <SmartGoalForm />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
