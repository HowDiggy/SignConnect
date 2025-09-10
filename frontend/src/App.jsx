import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
// --- CHANGE: Import the initializer and the (initially undefined) auth object ---
import { auth, initializeFirebase } from './firebaseConfig';
import Auth from './components/Auth/Auth';
import Controls from './components/Controls/Controls';
import ConversationView from './components/ConversationView/ConversationView';
import Suggestions from './components/Suggestions/Suggestions';
import UserInput from './components/UserInput/UserInput';
import Settings from './components/Settings/Settings';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  // --- CHANGE: Use a boolean to track if Firebase is ready ---
  const [isFirebaseInitialized, setIsFirebaseInitialized] = useState(false);

  const [conversation, setConversation] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Effect to initialize Firebase ONCE when the app component mounts
  useEffect(() => {
    const initFirebase = async () => {
      try {
        await initializeFirebase();
        setIsFirebaseInitialized(true); // Mark Firebase as ready
      } catch (error) {
        console.error("Fatal: Could not initialize Firebase. App cannot function.", error);
        // You could render an error message to the user here
      }
    };

    initFirebase();
  }, []); // Empty dependency array ensures this runs only once.

  // Effect to set up the authentication listener AFTER Firebase is initialized
  useEffect(() => {
    // --- CHANGE: Do not run this effect until initialization is complete ---
    if (isFirebaseInitialized) {
      const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
        console.log("Auth state changed:", currentUser?.email || "No user");
        setUser(currentUser);
        if (!currentUser) {
          setConversation([]);
          setSuggestions([]);
        }
      });
      // Cleanup the listener when the component unmounts
      return () => unsubscribe();
    }
  }, [isFirebaseInitialized]); // This effect now depends on the initialization status

  const handleNewTranscriptPart = (transcriptPart) => {
    const newMessage = {
      text: transcriptPart,
      sender: 'other',
      timestamp: new Date().toISOString()
    };
    setConversation(prev => [...prev, newMessage]);
  };

  const handleNewSuggestions = (newSuggestions) => {
    setSuggestions(newSuggestions);
  };

  const handleSuggestionSelect = (suggestionText) => {
    const newMessage = {
      text: suggestionText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    setConversation(prev => [...prev, newMessage]);
    setSuggestions([]);
  };

  const handleUserMessageSend = (messageText) => {
    const newMessage = {
      text: messageText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    setConversation(prev => [...prev, newMessage]);
    setSuggestions([]);
  };

  // --- CHANGE: Render a loading state until Firebase is ready ---
  if (!isFirebaseInitialized) {
    return <div className="loading-container"><h1>Initializing Authentication System...</h1></div>;
  }

  return (
    <div className="app-container">
      <header>
        <h1>SignConnect</h1>
        <div className="header-controls">
          {user && (
            <button onClick={() => setIsSettingsOpen(true)} className="settings-button">
              Settings
            </button>
          )}
          {/* The Auth component now implicitly uses the imported 'auth' object */}
          <Auth user={user} />
        </div>
      </header>
      <main>
        <ConversationView conversation={conversation} />

        <Suggestions
          suggestions={suggestions}
          onSelectSuggestion={handleSuggestionSelect}
        />

        <UserInput
          onSendMessage={handleUserMessageSend}
          isDisabled={!user}
        />

        <Controls
          user={user}
          onNewTranscription={handleNewTranscriptPart}
          onNewSuggestions={handleNewSuggestions}
        />
      </main>
      <Settings isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </div>
  );
}

export default App;
