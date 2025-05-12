import { useEffect, useState, useCallback } from "react";
import { usePlaidLink } from "react-plaid-link";
import ToggleButton from "./togglebutton";
import axios from "axios";
import api from "../../../api";
import plaidLogo from "../../../assets/plaidlogo.png";
import "./settings.scss";

const SettingsBlock = () => {
  const [linkToken, setLinkToken] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [settings, setSettings] = useState({
    email_notifications: false,
    sms_notifications: false,
    push_notifications: false,
  });
  const [userInfo, setUserInfo] = useState({
    username: "",
    email: "",
    phone_number: "",
  });

  // Load from localStorage instantly
  useEffect(() => {
    const savedSettings = localStorage.getItem("userSettings");
    const savedUserInfo = localStorage.getItem("userInfo");

    if (savedSettings) setSettings(JSON.parse(savedSettings));
    if (savedUserInfo) setUserInfo(JSON.parse(savedUserInfo));

    // Silent background refresh (optional but good)
    const fetchFreshData = async () => {
      try {
        const token = localStorage.getItem("token");
        const [settingsResponse, userInfoResponse] = await Promise.all([
          axios.get("http://localhost:8000/user_settings/", {
            headers: { Authorization: `Bearer ${token}` },
            withCredentials: true,
          }),
          axios.get("http://localhost:8000/user_info/", {
            headers: { Authorization: `Bearer ${token}` },
            withCredentials: true,
          }),
        ]);
        setSettings(settingsResponse.data);
        setUserInfo(userInfoResponse.data);
        localStorage.setItem(
          "userSettings",
          JSON.stringify(settingsResponse.data)
        );
        localStorage.setItem("userInfo", JSON.stringify(userInfoResponse.data));
      } catch (error) {
        console.error("Error fetching fresh settings/user info:", error);
      }
    };

    fetchFreshData();
  }, []);

  // Check if user is already linked to Plaid
  useEffect(() => {
    const checkPlaidStatus = async () => {
      try {
        const token = localStorage.getItem("token");
        await api.get("http://localhost:8000/accounts/", {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        });
        setIsLoggedIn(true);
      } catch {
        setIsLoggedIn(false);
      }
    };
    checkPlaidStatus();
  }, []);

  // Fetch link token for Plaid
  useEffect(() => {
    const fetchLinkToken = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:8000/create_link_token/",
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
            withCredentials: true,
          }
        );
        setLinkToken(response.data.link_token);
      } catch (error) {
        console.error("Error fetching Plaid link token:", error);
      }
    };
    fetchLinkToken();
  }, []);

  const onSuccess = useCallback(async (publicToken, metadata) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "http://localhost:8000/exchange_public_token/",
        {
          public_token: publicToken,
          account_type: "bank",
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        }
      );
      setIsLoggedIn(true);
    } catch (error) {
      console.error("Error exchanging public token:", error);
    }
  }, []);

  const handleToggleChange = async (name, value) => {
    try {
      const token = localStorage.getItem("token");
      const updatedSettings = { ...settings, [name]: value };

      setSettings(updatedSettings);
      await axios.post(
        "http://localhost:8000/user_settings/",
        updatedSettings,
        {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        }
      );

      // Update localStorage after saving
      localStorage.setItem("userSettings", JSON.stringify(updatedSettings));
    } catch (error) {
      console.error("Error updating user settings:", error);
    }
  };

  const handleUpdateUser = async (updateData) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post("http://localhost:8000/auth/update/", updateData, {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      alert("User account settings updated successfully");

      const response = await axios.get("http://localhost:8000/user_info/", {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      setUserInfo(response.data);
      localStorage.setItem("userInfo", JSON.stringify(response.data));
    } catch (error) {
      console.error("Error updating user info:", error);
    }
  };

  const config = linkToken ? { token: linkToken, onSuccess } : null;
  const { open, ready } = usePlaidLink(config || {});

  return (
    <div className="settings-content">
      <h2>Settings</h2>
      <AccountSettings userInfo={userInfo} onUpdateUser={handleUpdateUser} />
      <NotificationSettings
        settings={settings}
        onToggleChange={handleToggleChange}
      />
      <FinanceSettings
        isLoggedIn={isLoggedIn}
        linkToken={linkToken}
        open={open}
        ready={ready}
        setIsLoggedIn={setIsLoggedIn}
      />
    </div>
  );
};

export default SettingsBlock;

const AccountSettings = ({ userInfo, onUpdateUser }) => {
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [showPhoneForm, setShowPhoneForm] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const updateData = {};
    if (email) updateData.email = email;
    if (phoneNumber) updateData.phone_number = phoneNumber;
    if (newPassword) updateData.password = newPassword;
    onUpdateUser(updateData);
    setShowEmailForm(false);
    setShowPhoneForm(false);
    setShowPasswordForm(false);
  };

  return (
    <div className="settings-section">
      <h3>Account</h3>
      <div className={`account-block ${showEmailForm ? "expanded" : ""}`}>
        <p>Email: {userInfo.email}</p>
        <button
          onClick={() => setShowEmailForm(!showEmailForm)}
          className={`form-btn ${showEmailForm ? "expanded" : ""}`}
        >
          Edit
          <span className="arrow">▼</span>
        </button>
        <div className="submit-container">
          {showEmailForm && (
            <form onSubmit={handleSubmit}>
              <div className="form-block">
                <label style={{ fontSize: "small" }}>New Email: </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-updated"
                />
                <button type="submit" className="submit-btn">
                  Update
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
      <div className={`account-block ${showPhoneForm ? "expanded" : ""}`}>
        <p>Phone Number: {userInfo.phone_number}</p>
        <button
          onClick={() => setShowPhoneForm(!showPhoneForm)}
          className={`form-btn ${showPhoneForm ? "expanded" : ""}`}
        >
          Edit
          <span className="arrow">▼</span>
        </button>
        <div className="submit-container">
          {showPhoneForm && (
            <form onSubmit={handleSubmit}>
              <div className="form-block">
                <label style={{ fontSize: "small" }}>New Number:</label>
                <input
                  type="text"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                />
                <button type="submit" className="submit-btn">
                  {" "}
                  Update
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
      <div className={`account-block ${showPasswordForm ? "expanded" : ""}`}>
        <p>Password: </p>
        <button
          onClick={() => setShowPasswordForm(!showPasswordForm)}
          className={`form-btn ${showPasswordForm ? "expanded" : ""}`}
        >
          Edit
          <span className="arrow">▼</span>
        </button>
        <div className="submit-container">
          {showPasswordForm && (
            <form onSubmit={handleSubmit}>
              <div className="form-block">
                <label style={{ fontSize: "small" }}>Old Password: </label>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                />
              </div>
              <div className="form-block">
                <label style={{ fontSize: "small" }}>New Password: </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className="form-block">
                <label style={{ fontSize: "small" }}>Confirm Password: </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
              <button type="submit" className="submit-btn">
                Update
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

const NotificationSettings = ({ settings, onToggleChange }) => {
  return (
    <div className="settings-section">
      <h3>Notifications</h3>
      <div className="notif-block">
        <p>Email Notifications:</p>
        <div className="toggle">
          <ToggleButton
            label="Email Notifications"
            checked={settings.email_notifications}
            onChange={(value) => onToggleChange("email_notifications", value)}
          />
        </div>
      </div>
      <div className="notif-block">
        <p>SMS Notifications:</p>
        <div className="toggle">
          <ToggleButton
            label="SMS Notifications"
            checked={settings.sms_notifications}
            onChange={(value) => onToggleChange("sms_notifications", value)}
          />
        </div>
      </div>
      <div className="notif-block">
        <p>Push Notifications:</p>
        <div className="toggle">
          <ToggleButton
            label="Push Notifications"
            checked={settings.push_notifications}
            onChange={(value) => onToggleChange("push_notifications", value)}
          />
        </div>
      </div>
    </div>
  );
};

const FinanceSettings = ({
  isLoggedIn,
  linkToken,
  open,
  ready,
  setIsLoggedIn,
}) => {
  const [brokerageLinkToken, setBrokerageLinkToken] = useState(null);
  const [isBrokerageConnected, setIsBrokerageConnected] = useState(false);

  // Fetch brokerage link token
  useEffect(() => {
    const fetchBrokerageLinkToken = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:8000/create_link_token/",
          { product: "investments" },
          {
            headers: { Authorization: `Bearer ${token}` },
            withCredentials: true,
          }
        );
        setBrokerageLinkToken(response.data.link_token);
      } catch (error) {
        console.error(
          "Error fetching brokerage link token:",
          error.response ? error.response.data : error
        );
      }
    };

    if (isLoggedIn) {
      fetchBrokerageLinkToken();
    }
  }, [isLoggedIn]);

  // Check if brokerage is connected
  useEffect(() => {
    const checkBrokerageStatus = async () => {
      try {
        const token = localStorage.getItem("token");
        await axios.get("http://localhost:8000/investments/", {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        });
        setIsBrokerageConnected(true);
      } catch (error) {
        setIsBrokerageConnected(false);
      }
    };

    if (isLoggedIn) {
      checkBrokerageStatus();
    }
  }, [isLoggedIn]);

  // Merge Item: Function to call the unlink endpoint
  const handleUnlink = async () => {
    try {
      const token = localStorage.getItem("token");
      await axios.delete("http://localhost:8000/unlink", {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      setIsLoggedIn(false);
      setIsBrokerageConnected(false);
    } catch (error) {
      console.error(
        "Error unlinking Plaid account:",
        error.response ? error.response.data : error
      );
    }
  };

  // Function to connect brokerage account
  const handleConnectBrokerage = async () => {
    try {
      const token = localStorage.getItem("token");
      await axios.get("http://localhost:8000/investments/", {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      setIsBrokerageConnected(true);
    } catch (error) {
      console.error(
        "Error connecting brokerage account:",
        error.response ? error.response.data : error
      );
      alert("Error connecting brokerage account. Please try again later.");
    }
  };

  // Configuration for brokerage Plaid Link
  const brokerageConfig = brokerageLinkToken
    ? {
        token: brokerageLinkToken,
        onSuccess: async (publicToken, metadata) => {
          try {
            const token = localStorage.getItem("token");
            await axios.post(
              "http://localhost:8000/exchange_public_token/",
              {
                public_token: publicToken,
                account_type: "brokerage",
              },
              {
                headers: { Authorization: `Bearer ${token}` },
                withCredentials: true,
              }
            );
            setIsBrokerageConnected(true);

            // Fetch investment data after successful brokerage connection
            try {
              await axios.get("http://localhost:8000/investments/", {
                headers: { Authorization: `Bearer ${token}` },
                withCredentials: true,
              });
              console.log("Investment data imported successfully");
            } catch (error) {
              console.error(
                "Error importing investment data:",
                error.response ? error.response.data : error
              );
            }
          } catch (error) {
            console.error(
              "Error exchanging public token:",
              error.response ? error.response.data : error
            );
          }
        },
      }
    : null;

  const { open: openBrokerage, ready: brokerageReady } = usePlaidLink(
    brokerageConfig || {}
  );

  return (
    <div className="settings-section">
      <h3>Connect your Bank Account</h3>
      {/* <p>{isLoggedIn ? "Logged into Plaid" : "Not logged into Plaid"}</p> */}
      <button
        onClick={isLoggedIn ? handleUnlink : () => open()}
        disabled={!ready && !isLoggedIn}
        className="plaid"
      >
        <img src={plaidLogo} alt="Plaid Logo" className="plaid-logo" />
        {isLoggedIn ? "Unlink Plaid" : "Log into Plaid"}
      </button>

      {isLoggedIn && (
        <div className="investment-actions">
          <h4>Connect Brokerage Account</h4>
          <button
            onClick={
              isBrokerageConnected
                ? handleConnectBrokerage
                : () => openBrokerage()
            }
            disabled={!brokerageReady && !isBrokerageConnected}
            className="brokerage-button"
          >
            <img src={plaidLogo} alt="Plaid Logo" className="plaid-logo" />
            {isBrokerageConnected
              ? "Refresh Brokerage Data"
              : "Connect Brokerage"}
          </button>
        </div>
      )}
    </div>
  );
};
