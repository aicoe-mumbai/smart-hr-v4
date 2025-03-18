// import React, { useState, useEffect } from "react";
// import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
// import Login from "./components/Login";
// import NotFound from "./components/NotFound";
// import Dashboard from "./components/Dashboard";

// function App() {
//   const [isAuthenticated, setIsAuthenticated] = useState(false);

//   useEffect(() => {
//     const token = sessionStorage.getItem("access_token");
//     setIsAuthenticated(!!token);
//   }, []);

//   const handleLogin = () => {
//     setIsAuthenticated(true);
//   };

//   const handleLogout = () => {
//     setIsAuthenticated(false);
//   };

//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={isAuthenticated ? <Navigate to="/smarthr-form" replace /> : <Navigate to="/login" replace />} />
//         <Route path="/login" element={isAuthenticated ? <Navigate to="/smarthr-form" replace /> : <Login onLogin={handleLogin} />} />
        
//         {/* Use Dashboard for both SmartGoalForm and Previous Validations */}
//         <Route path="/smarthr-form" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
//         <Route path="/previous-validations" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
//         <Route path="/update-goal/:goalId" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />

//         <Route path="*" element={<NotFound />} />
//       </Routes>
//     </Router>
//   );
// }

// export default App;

import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./components/authConfig";
import Login from "./components/Login";
import NotFound from "./components/NotFound";
import Dashboard from "./components/Dashboard";

function App() {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthWrapper />
    </MsalProvider>
  );
}

function AuthWrapper() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    setIsAuthenticated(!!token); // Set to true if token exists, false otherwise
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={isAuthenticated ? <Navigate to="/smarthr-form" replace /> : <Navigate to="/login" replace />}
        />
        <Route path="/login" element={isAuthenticated ? <Navigate to="/smarthr-form" replace /> : <Login onLogin={handleLogin} />} />
        <Route path="/smarthr-form" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
        <Route path="/previous-validations" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
        <Route path="/update-goal/:goalId" element={isAuthenticated ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
