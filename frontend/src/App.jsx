import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebaseConfig';
import Auth from './components/Auth/Auth';
import Controls from './components/Controls/Controls';
// Import our new component and remove the old one
import ConversationView from './components/ConversationView/ConversationView';
import Suggestions from './components/Suggestions/Suggestions';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  
  // Replace transcription state with conversation state
  const [conversation, setConversation] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  // This logic is simplified from your previous file to focus on the conversation
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      if (!currentUser) {
        setConversation([]);
        setSuggestions([]);
      }
    });
    return () => unsubscribe();
  }, []);

  // Renamed from handleNewTranscription
  const handleNewTranscriptPart = (transcriptPart) => {
    const newMessage = { text: transcriptPart, sender: 'other' };
    setConversation(prev => [...prev, newMessage]);
  };

  // Renamed from handleNewSuggestions
  const handleNewSuggestions = (newSuggestions) => {
    setSuggestions(newSuggestions);
  };

  // This is the new handler for when a user clicks a suggestion
  const handleSuggestionSelect = (suggestionText) => {
    const newMessage = { text: suggestionText, sender: 'user' };
    setConversation(prev => [...prev, newMessage]);
    // Clear suggestions after one is selected
    setSuggestions([]);
  };


  return (
    <div className="app-container">
      <header>
        <h1>SignConnect</h1>
        <Auth user={user} />
      </header>
      <main>
        {/* Replace the old display with our new ConversationView */}
        <ConversationView conversation={conversation} />
        
        <Suggestions
          suggestions={suggestions}
          onSelectSuggestion={handleSuggestionSelect}
        />
        
        <Controls
          user={user}
          onNewTranscription={handleNewTranscriptPart}
          onNewSuggestions={handleNewSuggestions}
        />
      </main>
    </div>
  );
}

export default App;