import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Navbar.css";
import lntlogo from "../assets/L_T_PES_-_Linear_Logo_-_Black-removebg-preview.png";

const Navbar = ({ onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const apiUrl = process.env.REACT_APP_API_URL;
  const token = sessionStorage.getItem("access_token");

  const handleLogout = async () => {
    const refreshToken = sessionStorage.getItem("refresh_token");

    if (!refreshToken) {
      console.error("No refresh token found");
      sessionStorage.clear();
      navigate("/login");
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/api/logout/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        sessionStorage.clear();
        onLogout();
        navigate("/login");
      } else {
        console.error("Logout failed");
      }
    } catch (error) {
      console.error("Error logging out:", error);
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
        <li className="logout-btn" onClick={handleLogout}>Logout</li>
      </ul>
    </nav>
  );
};

export default Navbar;
