import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
// --- CHANGE: Import the promise instead of the static object ---
import { authPromise } from './firebaseConfig';
import Auth from './components/Auth/Auth';
import Controls from './components/Controls/Controls';
import ConversationView from './components/ConversationView/ConversationView';
import Suggestions from './components/Suggestions/Suggestions';
import UserInput from './components/UserInput/UserInput';
import Settings from './components/Settings/Settings';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  // --- ADD: State to hold the resolved auth object and loading status ---
  const [auth, setAuth] = useState(null);
  const [loading, setLoading] = useState(true);

  // Replace transcription state with conversation state
  const [conversation, setConversation] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    // --- CHANGE: Wait for the authPromise to resolve ---
    authPromise.then(authInstance => {
      setAuth(authInstance); // Save the resolved auth instance
      const unsubscribe = onAuthStateChanged(authInstance, (currentUser) => {
        console.log("Auth state changed:", currentUser?.email || "No user");
        setUser(currentUser);
        if (!currentUser) {
          setConversation([]);
          setSuggestions([]);
        }
        setLoading(false); // Firebase is initialized and auth state is known
      });
      return () => unsubscribe();
    }).catch(error => {
        console.error("Firebase auth initialization failed", error);
        setLoading(false); // Stop loading even if there's an error
    });
  }, []); // This effect runs only once on mount

  // --- ADD: A loading screen while waiting for Firebase ---
  if (loading) {
    return <div className="loading-container"><h1>Loading...</h1></div>;
  }

  // --- All handler functions (handleNewTranscriptPart, etc.) remain exactly the same ---
  const handleNewTranscriptPart = (transcriptPart) => {
    console.log("App.jsx: Received new transcript:", transcriptPart);
    const newMessage = {
      text: transcriptPart,
      sender: 'other',
      timestamp: new Date().toISOString() // Add timestamp for debugging
    };

    setConversation(prev => {
      const updated = [...prev, newMessage];
      console.log("App.jsx: Updated conversation:", updated);
      return updated;
    });
  };

  const handleNewSuggestions = (newSuggestions) => {
    console.log("App.jsx: Received new suggestions:", newSuggestions);
    setSuggestions(newSuggestions);
  };

  const handleSuggestionSelect = (suggestionText) => {
    console.log("App.jsx: Suggestion selected:", suggestionText);
    const newMessage = {
      text: suggestionText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    setConversation(prev => {
      const updated = [...prev, newMessage];
      console.log("App.jsx: Updated conversation after suggestion:", updated);
      return updated;
    });
    // Clear suggestions after one is selected
    setSuggestions([]);
  };

  const handleUserMessageSend = (messageText) => {
    console.log("App.jsx: User message sent:", messageText);
    const newMessage = {
      text: messageText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    setConversation(prev => {
      const updated = [...prev, newMessage];
      console.log("App.jsx: Updated conversation after user input:", updated);
      return updated;
    });
    // Clear suggestions, as the user has chosen their own path
    setSuggestions([]);
  };

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
          {/* --- CHANGE: Pass the resolved auth object to the Auth component --- */}
          <Auth user={user} auth={auth} />
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
          isDisabled={!user} // Only disable if user is not logged in
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
