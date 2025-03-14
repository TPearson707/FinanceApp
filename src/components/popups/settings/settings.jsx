import { useEffect, useState, useCallback } from "react";
import { usePlaidLink } from "react-plaid-link";
import ToggleButton from "./togglebutton";
import axios from "axios";

const SettingsBlock = () => {
    const [linkToken, setLinkToken] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        const fetchLinkToken = async () => {
            try {
                const response = await axios.post("http://localhost:8000/create_link_token", {}, { withCredentials: true });
                setLinkToken(response.data.link_token);
            } catch (error) {
                console.error("Error fetching Plaid link token:", error);
            }
        };

        fetchLinkToken();
    }, []);

    const onSuccess = useCallback(async (publicToken) => {
        try {
            await axios.post("http://localhost:8000/exchange_public_token", { public_token: publicToken }, { withCredentials: true });
            setIsLoggedIn(true);
        } catch (error) {
            console.error("Error exchanging public token:", error);
        }
    }, []);

    const config = {
        token: linkToken,
        onSuccess,
    };

    const { open, ready } = usePlaidLink(config);

    return (
        <div className="settings-content">
            <h2>Settings</h2>
            <p>Adjust your preferences here.</p>
            <NotificationSettings />
            <FinanceSettings isLoggedIn={isLoggedIn} linkToken={linkToken} open={open} ready={ready} />
        </div>
    );
};

export default SettingsBlock;

const NotificationSettings = () => {
    return (
        <div className="settings-section">
            <div className="notif-block">
                <ToggleButton label="Email Notifications" />
            </div>
            <div className="notif-block">
                <ToggleButton label="SMS Notifications" />
            </div>
            <div className="notif-block">
                <ToggleButton label="Push Notifications" />
            </div>
        </div>
    );
};

const FinanceSettings = ({ isLoggedIn, linkToken, open, ready }) => {
    return (
        <div className="settings-section">
            <p>{isLoggedIn ? "Logged into Plaid" : "Not logged into Plaid"}</p>
            {!isLoggedIn && linkToken && (
                <button onClick={() => open()} disabled={!ready}>
                    Log into Plaid
                </button>
            )}
        </div>
    );
};


const AccountSettings = () => {
    return (
        <div className="settings-section">
            <h2>empty</h2>
        </div>
    );
};