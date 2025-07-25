import React, { useState, useRef, useEffect } from 'react';
import './Controls.css';

function Controls({ user, onNewTranscription, onNewSuggestions }) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  const handleStart = async () => {
    if (!user) return;
    const token = await user.getIdToken();
    const wsUrl = `ws://localhost:8000/ws?token=${token}`;
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onopen = () => {
      console.log("WebSocket connection established.");
      setIsConnected(true);
    };

    socketRef.current.onmessage = (event) => {
      const message = event.data;

      if (message.startsWith("final:")) {
        const transcriptPart = message.substring("final:".length);
        onNewTranscription(transcriptPart);
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify({
            type: "get_suggestions",
            transcript: transcriptPart
          }));
        }
      } else if (message.startsWith("suggestions:")) {
        const suggestionsJSON = message.substring("suggestions:".length);
        try {
          const suggestionsList = JSON.parse(suggestionsJSON);
          onNewSuggestions(suggestionsList);
        } catch (e) {
          console.error("Failed to parse suggestions JSON:", e);
        }
      }
    };

    socketRef.current.onclose = () => {
      console.log("WebSocket connection closed.");
      setIsConnected(false);
      socketRef.current = null;
    };

    socketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };
  };

  const handleStop = () => {
    if (socketRef.current) {
      socketRef.current.close();
    }
  };

  const isUserLoggedIn = !!user;

  return (
    <div className="controls-container">
      <div className="button-group">
        <button onClick={handleStart} disabled={!isUserLoggedIn || isConnected}>
          Start Transcription
        </button>
        <button onClick={handleStop} disabled={!isConnected}>
          Stop Transcription
        </button>
      </div>
      <div className="status">
        Connection Status: {isConnected ? <span className="status-connected">Connected</span> : <span className="status-disconnected">Disconnected</span>}
      </div>
    </div>
  );
}

export default Controls;