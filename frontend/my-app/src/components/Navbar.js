import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Navbar.css";
import lntlogo from "../assets/L_T_PES_-_Linear_Logo_-_Black-removebg-preview.png";
import loadingGif from "../assets/loading-7528_256.gif";
import { useState } from "react";
import { useMsal } from "@azure/msal-react";


const Navbar = ({ onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const apiUrl = process.env.REACT_APP_API_URL;
  const token = sessionStorage.getItem("access_token");
  const [loading, setLoading] = useState(false);
  const { instance } = useMsal();


  const handleLogout = async () => {
  try {
    await instance.logoutRedirect({postLogoutRedirectUri: window.location.origin,}); // Ensure logout completes before proceeding
    sessionStorage.clear();
    onLogout();
    navigate("/login");
  } catch (error) {
    console.error("Logout failed:", error);
    alert("Logout failed. Please try again.");
  }
};


  return (
    <nav className="navbar">
      <div className="nav-logo">
        <img src={lntlogo} alt="SmartHR Logo" className="logo-img" />
      </div>
      <ul className="nav-links">
        <li
          className={`nav-item ${location.pathname === "/smarthr-form" ? "active" : ""}`}
          onClick={() => navigate("/smarthr-form")}
        >
          My Form
        </li>
        <li
          className={`nav-item ${location.pathname === "/previous-validations" ? "active" : ""}`}
          onClick={() => navigate("/previous-validations")}
        >
          Previous Validations
        </li>
        {/* <li className="logout-btn" onClick={handleLogout}>Logout</li> */}
        <li className="logout-btn" onClick={handleLogout} disabled={loading}>
          {loading ? (
            <img src={loadingGif} alt="Logging out..." className="loading-icon" />
          ) : (
            "Logout"
          )}
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
