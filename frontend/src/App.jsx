import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebaseConfig';
import Auth from './components/Auth/Auth';
import Controls from './components/Controls/Controls';
import ConversationView from './components/ConversationView/ConversationView';
import Suggestions from './components/Suggestions/Suggestions';
import UserInput from './components/UserInput/UserInput';
import Settings from './components/Settings/Settings';
import './App.css';

function App() {
  const [user, setUser] = useState(null);

  // Replace transcription state with conversation state
  const [conversation, setConversation] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      console.log("Auth state changed:", currentUser?.email || "No user");
      setUser(currentUser);
      if (!currentUser) {
        setConversation([]);
        setSuggestions([]);
      }
    });
    return () => unsubscribe();
  }, []);

  // Fixed function to handle new transcripts
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

  // Fixed function to handle new suggestions
  const handleNewSuggestions = (newSuggestions) => {
    console.log("App.jsx: Received new suggestions:", newSuggestions);
    setSuggestions(newSuggestions);
  };

  // Fixed function for when a user clicks a suggestion
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

  // Fixed function for the free response input
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
