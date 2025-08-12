// frontend/src/components/Controls/Controls.jsx
import React, { useState, useRef, useEffect } from 'react';
import config from '../../config/environment.js';
import './Controls.css';

function Controls({ user, onNewTranscription, onNewSuggestions }) {
  const [isConnected, setIsConnected] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Refs for the WebSocket, MediaRecorder, and audio stream
  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioStreamRef = useRef(null);

  const handleStart = async () => {
    if (!user) return;

    try {
      // 1. Get the Firebase ID token
      const token = await user.getIdToken();

      // 2. Connect to WebSocket WITHOUT token in URL (security fix)
      const wsUrl = `${config.wsBaseUrl}/ws`;
      console.log('Connecting to WebSocket:', wsUrl);

      socketRef.current = new WebSocket(wsUrl);

      socketRef.current.onopen = () => {
        console.log("WebSocket connection established, sending authentication...");
        setIsConnected(true);

        // 3. Send authentication handshake after connection
        const authMessage = {
          type: "authenticate",
          token: token
        };
        socketRef.current.send(JSON.stringify(authMessage));
      };

      socketRef.current.onmessage = (event) => {
        const message = event.data;

        // Handle authentication response
        if (message === "auth_success") {
          console.log("WebSocket authentication successful");
          setIsAuthenticated(true);
          // Start audio recording only after successful authentication
          startRecording();
          return;
        }

        if (message === "auth_failed") {
          console.error("WebSocket authentication failed");
          setIsAuthenticated(false);
          handleStop();
          return;
        }

        // Handle transcription messages
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
        setIsAuthenticated(false);
        stopRecordingCleanup();
        socketRef.current = null;
      };

      socketRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnected(false);
        setIsAuthenticated(false);
      };

    } catch (error) {
      console.error("Error starting WebSocket connection:", error);
      setIsConnected(false);
      setIsAuthenticated(false);
    }
  };

  const startRecording = async () => {
    try {
      audioStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access is required for transcription.");
      handleStop();
      return;
    }

    mediaRecorderRef.current = new MediaRecorder(audioStreamRef.current, {
      mimeType: 'audio/webm;codecs=opus',
    });

    mediaRecorderRef.current.addEventListener('dataavailable', (event) => {
      if (event.data.size > 0 && socketRef.current && socketRef.current.readyState === WebSocket.OPEN && isAuthenticated) {
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64String = reader.result.split(',')[1];
          const message = JSON.stringify({ type: "audio", data: base64String });
          socketRef.current.send(message);
        };
        reader.readAsDataURL(event.data);
      }
    });

    mediaRecorderRef.current.start(250); // Capture smaller chunks more frequently (250ms instead of 1000ms)
    console.log("MediaRecorder started with 250ms intervals.");
  };

  const stopRecordingCleanup = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      console.log("MediaRecorder stopped.");
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      console.log("Microphone stream stopped.");
    }
    mediaRecorderRef.current = null;
    audioStreamRef.current = null;
  };

  const handleStop = () => {
    stopRecordingCleanup();
    setIsAuthenticated(false);
    if (socketRef.current) {
      socketRef.current.close();
    }
  };

  // Cleanup effect for when the component unmounts
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      stopRecordingCleanup();
    };
  }, []);

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
        Connection Status: {
          isConnected ? (
            isAuthenticated ? (
              <span className="status-connected">Connected & Authenticated</span>
            ) : (
              <span className="status-connecting">Connected (Authenticating...)</span>
            )
          ) : (
            <span className="status-disconnected">Disconnected</span>
          )
        }
      </div>
    </div>
  );
}

export default Controls;
