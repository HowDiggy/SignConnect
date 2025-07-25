import React, { useState, useRef, useEffect } from 'react';
import './Controls.css';

/**
 * Renders the main action buttons and manages the WebSocket connection.
 * @param {{ user: import('firebase/auth').User | null }} props
 */
function Controls({ user }) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // useRef is used to hold a mutable value that does not cause a re-render when changed.
  // We use it to store the WebSocket instance.
  const socketRef = useRef(null);

  // This useEffect hook is for cleanup.
  // It ensures that if the component is ever removed from the page,
  // we close any active WebSocket connection to prevent memory leaks.
  useEffect(() => {
    // The return function from useEffect is called on component unmount
    return () => {
      if (socketRef.current) {
        console.log("Component unmounting, closing WebSocket.");
        socketRef.current.close();
      }
    };
  }, []); // The empty dependency array means this effect runs only once on mount/unmount

  const handleStart = async () => {
    // Pre-condition: User must be logged in. This is already handled by the disabled button.
    if (!user) {
      console.error("Cannot start, user is not logged in.");
      return;
    }
    setIsConnecting(true);

    try {
      // Get the Firebase auth token for the current user.
      const token = await user.getIdToken();
      // NOTE: Replace with your actual WebSocket URL if different.
      const wsUrl = `ws://localhost:8000/api/v1/ws/transcribe?token=${token}`;

      console.log("Connecting to WebSocket...");
      socketRef.current = new WebSocket(wsUrl);

      socketRef.current.onopen = () => {
        console.log("WebSocket connection established.");
        setIsConnected(true);
        setIsConnecting(false);
      };

      socketRef.current.onmessage = (event) => {
        // For now, we just log the message. Later, we'll lift this state up.
        console.log("Received message:", event.data);
      };

      socketRef.current.onclose = () => {
        console.log("WebSocket connection closed.");
        setIsConnected(false);
        setIsConnecting(false);
        socketRef.current = null;
      };

      socketRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnected(false);
        setIsConnecting(false);
        socketRef.current = null;
      };

    } catch (error) {
      console.error("Failed to get auth token:", error);
      setIsConnecting(false);
    }
  };

  const handleStop = () => {
    if (socketRef.current) {
      console.log("Closing WebSocket connection.");
      socketRef.current.close();
    }
  };

  const isUserLoggedIn = !!user;
  const canStart = isUserLoggedIn && !isConnected && !isConnecting;
  const canStop = isConnected;

  return (
    <div className="controls-container">
      <div className="button-group">
        <button onClick={handleStart} disabled={!canStart}>
          {isConnecting ? 'Connecting...' : 'Start Transcription'}
        </button>
        <button onClick={handleStop} disabled={!canStop}>
          Stop Transcription
        </button>
      </div>
      <div className="status">
        Connection Status: {isConnected ? <span className="status-connected">Connected</span> : <span className="status-disconnected">Disconnected</span>}
      </div>
      {!isUserLoggedIn && (
        <p className="disabled-message">Please log in to start.</p>
      )}
    </div>
  );
}

export default Controls;