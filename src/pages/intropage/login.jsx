import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./login.scss";

const LoginBlock = ({
  toggleLoginBlock,
  isSigningUp: initialSigningUp,
  setIsAuthenticated,
}) => {
  const [isSigningUp, setIsSigningUp] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [number, setNumber] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    setIsSigningUp(initialSigningUp);
  }, [initialSigningUp]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (isSigningUp && password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    try {
      if (isSigningUp) {
        await axios.post("http://localhost:8000/auth/", {
          first_name: firstName,
          last_name: lastName,
          email: email,
          username: username,
          phone_number: number,
          password: password,
        });
        console.log("Sign-up successful");
      }

      const loginResponse = await axios.post(
        "http://localhost:8000/auth/token",
        new URLSearchParams({
          username: username,
          password: password,
        }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      const token = loginResponse.data.access_token;
      localStorage.setItem("token", token);

      // ✨ Immediately fetch user settings and user info
      const [settingsRes, userInfoRes] = await Promise.all([
        axios.get("http://localhost:8000/user_settings/", {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        }),
        axios.get("http://localhost:8000/user_info/", {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        }),
      ]);

      localStorage.setItem("userSettings", JSON.stringify(settingsRes.data));
      localStorage.setItem("userInfo", JSON.stringify(userInfoRes.data));

      setIsAuthenticated(true);
      navigate("/dashboard");
    } catch (error) {
      console.error(
        "Authentication error:",
        error.response ? error.response.data : error.message
      );
      if (error.response && error.response.status === 400) {
        const detail = error.response.data.detail;
        if (detail === "User with this email already exists") {
          alert(
            "User with this email already exists. Please log in or use a different email."
          );
        } else if (detail === "User with this phone number already exists") {
          alert(
            "User with this phone number already exists. Please log in or use a different phone number."
          );
        } else {
          alert(
            "Authentication failed. Please check your credentials and try again."
          );
        }
      } else {
        alert("Authentication failed. Please try again.");
      }
    }
  };

  return (
    <div className="login-block">
      <div className="login">
        <button className="close-btn" onClick={toggleLoginBlock}>
          x
        </button>
        <h2>{isSigningUp ? "Sign Up" : "Log In"}</h2>
        <div
          className={`login-container ${
            isSigningUp ? "expanded" : "collapsed"
          }`}
        >
          <form onSubmit={handleSubmit}>
            {!isSigningUp && (
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            )}
            {isSigningUp && (
              <>
                <input
                  type="text"
                  placeholder="First Name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
                <input
                  type="text"
                  placeholder="Last Name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
                <input
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <input
                  type="tel"
                  placeholder="Phone Number"
                  value={number}
                  onChange={(e) => setNumber(e.target.value)}
                  required
                />
              </>
            )}
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {isSigningUp && (
              <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            )}
            <button type="submit" className="submit-btn">
              {isSigningUp ? "Sign Up" : "Log In"}
            </button>
          </form>
        </div>
        <p onClick={() => setIsSigningUp(!isSigningUp)} className="toggle-text">
          {isSigningUp
            ? "Already have an account? Log In"
            : "Don't have an account? Sign Up"}
        </p>
      </div>
    </div>
  );
};

export default LoginBlock;
