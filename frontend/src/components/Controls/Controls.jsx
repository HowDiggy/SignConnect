import React, { useState, useRef, useEffect } from 'react';
import './Controls.css';

function Controls({ user, onNewTranscription, onNewSuggestions }) {
  const [isConnected, setIsConnected] = useState(false);
  
  // Refs for the WebSocket, MediaRecorder, and audio stream
  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioStreamRef = useRef(null);

  const handleStart = async () => {
    if (!user) return;

    // --- 1. Establish WebSocket Connection (Your existing logic) ---
    const token = await user.getIdToken();
    const wsUrl = `ws://localhost:8000/ws?token=${token}`;
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onopen = () => {
      console.log("WebSocket connection established.");
      setIsConnected(true);

      // --- 2. Start Audio Recording (New Logic) ---
      startRecording(); 
    };

    socketRef.current.onmessage = (event) => {
      const message = event.data;

      if (message.startsWith("final:")) {
        const transcriptPart = message.substring("final:".length);
        onNewTranscription(transcriptPart); // Pass data up to App.jsx
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
          onNewSuggestions(suggestionsList); // Pass data up to App.jsx
        } catch (e) {
          console.error("Failed to parse suggestions JSON:", e);
        }
      }
    };

    socketRef.current.onclose = () => {
      console.log("WebSocket connection closed.");
      setIsConnected(false);
      stopRecordingCleanup(); // Ensure recorder is stopped if connection closes
      socketRef.current = null;
    };

    socketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };
  };

  const startRecording = async () => {
    try {
      audioStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access is required for transcription.");
      handleStop(); // Stop everything if mic access is denied
      return;
    }

    mediaRecorderRef.current = new MediaRecorder(audioStreamRef.current, {
      mimeType: 'audio/webm;codecs=opus',
    });

    mediaRecorderRef.current.addEventListener('dataavailable', (event) => {
      if (event.data.size > 0 && socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64String = reader.result.split(',')[1];
          const message = JSON.stringify({ type: "audio", data: base64String });
          socketRef.current.send(message);
        };
        reader.readAsDataURL(event.data);
      }
    });

    mediaRecorderRef.current.start(1000); // Capture 1-second chunks
    console.log("MediaRecorder started.");
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
  }

  const handleStop = () => {
    stopRecordingCleanup();
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
        Connection Status: {isConnected ? <span className="status-connected">Connected</span> : <span className="status-disconnected">Disconnected</span>}
      </div>
    </div>
  );
}

export default Controls;