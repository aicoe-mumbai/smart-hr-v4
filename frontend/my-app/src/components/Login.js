import React, { useState } from "react";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./authConfig";
import { useNavigate } from "react-router-dom";
import "./Login.css"; 

const BYPASS_AUTH = true; // Set to false to enable Azure AD

const Login = ({ onLogin }) => {
  const [loading, setLoading] = useState(false); 
  const { instance } = useMsal();
  const navigate = useNavigate();

  const handleLogin = async () => {
    setLoading(true); 
    try {
      if (BYPASS_AUTH) {
        // Bypass authentication for local testing
        const testUsername = "testuser@local.dev";
        const encodedUsername = btoa(testUsername);
        sessionStorage.setItem("username", encodedUsername);
        onLogin();
        navigate("/smarthr-form", { replace: true });
        return;
      }

      if (instance.getActiveAccount()) {
        console.warn("Login already in progress");
        return;
      }
      sessionStorage.clear();
      const response = await instance.loginPopup(loginRequest);
      if (!response) throw new Error("Login response is null");
  
      const username = response.account?.username || "Unknown User";
      const accessToken = response.accessToken;
      const encodedUsername = btoa(username);
      sessionStorage.setItem("username", encodedUsername);
  
      const backendResponse = await fetch(`${process.env.REACT_APP_API_URL}/api/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ encodedUsername }),
      });
  
      if (!backendResponse.ok) {
        console.error("Backend authentication failed");
        throw new Error("Backend authentication failed");
      }
  
      const data = await backendResponse.json();
  
      onLogin();
      navigate("/smarthr-form", { replace: true });
    } catch (error) {
      console.error("Login failed:", error);
      alert("Authentication failed. Please try again.");
    } finally {
      setLoading(false); 
    }
  };

  return (
    <div className={`login-page ${loading ? "loading" : ""}`}>
      <div className={`login-box ${loading ? "loading-box" : ""}`}>
        <h2>Welcome to Goal Assist</h2>
        <p>{BYPASS_AUTH ? "Click to continue (Dev Mode)" : "Sign in using Azure Microsoft Account"}</p>
        <button onClick={handleLogin} className="login-btn">
          {BYPASS_AUTH ? "Continue" : "Sign in with Azure AD"}
        </button>
      </div>
      
      {/* Spinner that appears during loading */}
      {loading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      )}
    </div>
  );
};

export default Login;
