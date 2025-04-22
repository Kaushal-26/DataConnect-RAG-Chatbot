// notion.js

import { useState, useEffect } from "react";
import { Box, Button, CircularProgress } from "@mui/material";
import axios from "axios";

export const NotionIntegration = ({
  user,
  org,
  integrationConnected,
  setIntegrationConnected,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Function to open OAuth in a new window
  const handleConnectClick = async () => {
    try {
      setIsConnecting(true);
      const formData = new FormData();
      formData.append("user_id", user);
      formData.append("org_id", org);
      const response = await axios.post(
        `http://localhost:8000/integrations/notion/authorize`,
        formData
      );
      console.log(response);
      const authURL = response?.data;

      const newWindow = window.open(
        authURL,
        "Notion Authorization",
        "width=600, height=600"
      );

      // Polling for the window to close
      const pollTimer = window.setInterval(() => {
        if (newWindow?.closed !== false) {
          window.clearInterval(pollTimer);
          handleWindowClosed();
        }
      }, 200);
    } catch (e) {
      setIsConnecting(false);
      alert(e?.response?.data?.detail);
    }
  };

  // Function to handle logic when the OAuth window closes
  const handleWindowClosed = async () => {
    try {
      const formData = new FormData();
      formData.append("user_id", user);
      formData.append("org_id", org);
      const response = await axios.post(
        `http://localhost:8000/integrations/notion/credentials`,
        formData
      );
      const isConnected = response.data;
      if (isConnected) {
        setIsConnecting(false);
        setIsConnected(true);
        setIntegrationConnected(true);
      }
      setIsConnecting(false);
    } catch (e) {
      setIsConnecting(false);
      alert(e?.response?.data?.detail);
    }
  };

  useEffect(() => {
    setIsConnected(integrationConnected ? true : false);
  }, [integrationConnected]);

  return (
    <>
      <Box sx={{ mt: 2 }}>
        Parameters
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          sx={{ mt: 2 }}
        >
          <Button
            variant="contained"
            onClick={isConnected ? () => {} : handleConnectClick}
            color={isConnected ? "success" : "primary"}
            disabled={isConnecting}
            style={{
              pointerEvents: isConnected ? "none" : "auto",
              cursor: isConnected ? "default" : "pointer",
              opacity: isConnected ? 1 : undefined,
            }}
          >
            {isConnected ? (
              "Notion Connected"
            ) : isConnecting ? (
              <CircularProgress size={20} />
            ) : (
              "Connect to Notion"
            )}
          </Button>
        </Box>
      </Box>
    </>
  );
};
