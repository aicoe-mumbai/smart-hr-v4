import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./components/authConfig";
import Login from "./components/Login";
import NotFound from "./components/NotFound";
import Dashboard from "./components/Dashboard";
import GapAnalysis from "./components/GapAnalysis";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check both token and MSAL account (bypass MSAL check for local dev)
    const checkAuth = async () => {
      const token = sessionStorage.getItem("username");
      setIsAuthenticated(!!token);
    };
    
    checkAuth();
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    sessionStorage.clear();
    setIsAuthenticated(false);
  };

  return (
    <MsalProvider instance={msalInstance}>
      <Router>
        <Routes>
          <Route 
            path="/" 
            element={
              isAuthenticated ? 
                <Navigate to="/smarthr-form" replace /> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/login" 
            element={
              isAuthenticated ? 
                <Navigate to="/smarthr-form" replace /> : 
                <Login onLogin={handleLogin} />
            } 
          />
          <Route 
            path="/smarthr-form" 
            element={
              isAuthenticated ? 
                <Dashboard onLogout={handleLogout} /> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route path="/previous-validations" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
          <Route path="/update-goal/:goalId" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
          <Route path="/gap-analysis" element={isAuthenticated ? <GapAnalysis /> : <Navigate to="/login" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </MsalProvider>
  );
}

export default App;
