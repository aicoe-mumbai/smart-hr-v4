// import React, { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import "./Login.css";

// const Login = ({ onLogin }) => {
//   const [formData, setFormData] = useState({ username: "", password: "" });
//   const [message, setMessage] = useState("");
//   const navigate = useNavigate();

//   const handleChange = (e) => {
//     setFormData({ ...formData, [e.target.name]: e.target.value });
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();

//     if (!formData.username || !formData.password) {
//       setMessage("Both fields are required!");
//       return;
//     }

//     try {
//       const response = await fetch(`${process.env.REACT_APP_API_URL}/api/login/`, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify(formData),
//       });

//       const data = await response.json();

//       if (response.ok) {
//         sessionStorage.setItem("access_token", data.tokens.access);
//         sessionStorage.setItem("refresh_token", data.tokens.refresh);
//         setMessage("Login successful!");
//         onLogin(); 
//         navigate("/dashoard");
//       } else {
//         setMessage(data.message || "Invalid credentials");
//       }
//     } catch (error) {
//       setMessage("Something went wrong! Please try again.");
//       console.error("Login Error:", error);
//     }
//   };

//   return (
//     <div className="login-container-main">
//       <div className="login-container">
//         <h2>Login</h2>
//         <form onSubmit={handleSubmit} className="login-form">
//           <label>Username:</label>
//           <input
//             type="text"
//             name="username"
//             value={formData.username}
//             onChange={handleChange}
//             placeholder="Enter username"
//             required
//           />

//           <label>Password:</label>
//           <input
//             type="password"
//             name="password"
//             value={formData.password}
//             onChange={handleChange}
//             placeholder="Enter password"
//             required
//           />

//           {message && <p className="message-login">{message}</p>}

//           <button type="submit" className="login-btn">Login</button>
//         </form>
//       </div>
//     </div>
//   );
// };

// export default Login;


import React from "react";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./authConfig";
import { useNavigate } from "react-router-dom";

const Login = ({onLogin}) => {
  const { instance } = useMsal();
  const navigate = useNavigate();

  const handleLogin = async () => { 
    try {
      const loginResponse = await instance.loginPopup(loginRequest);
      sessionStorage.setItem("access_token", loginResponse.accessToken); // Store token
      navigate("/smarthr-form");
    } catch (error) {
      console.error("Login failed:", error);
    }
  };

  // const handleLogin = async () => {
  //   try {
  //     const loginResponse = await instance.loginPopup(loginRequest);
      
  //     // Store access token
  //     sessionStorage.setItem("access_token", loginResponse.accessToken);
  
  //     // Extract user details from login response
  //     const username = loginResponse.account.username; // Get user email (username)
  
  //     // Send the username to the backend
  //     const response = await fetch(`${process.env.REACT_APP_API_URL}/api/login/`, {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //         Authorization: `Bearer ${loginResponse.accessToken}`, 
  //       },
  //       body: JSON.stringify({ username: username }), 
  //     });
  
  //     if (response.ok) {
  //       console.log("User successfully authenticated in backend");
  //       onLogin();
  //       navigate("/smarthr-form"); 
  //     } else {
  //       console.error("Backend authentication failed:", response.statusText);
  //     }
  
  //   } catch (error) {
  //     console.error("Login failed:", error);
  //   }
  // };
  
  return (
    <div>
      <h2>Azure AD Login</h2>
      <button onClick={handleLogin}>Sign in with Azure</button>
    </div>
  );
};

export default Login;
