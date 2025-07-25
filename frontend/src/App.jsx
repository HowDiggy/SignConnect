import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebaseConfig';
import Auth from './components/Auth/Auth';
import Controls from './components/Controls/Controls';
import TranscriptionDisplay from './components/TranscriptionDisplay/TranscriptionDisplay';
import Suggestions from './components/Suggestions/Suggestions';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      if (!currentUser) {
        setTranscription('');
        setSuggestions([]);
      }
    });
    return () => unsubscribe();
  }, []);

  const handleNewTranscription = (transcriptPart) => {
    setTranscription(prev => prev + transcriptPart + ' ');
  };

  const handleNewSuggestions = (newSuggestions) => {
    setSuggestions(newSuggestions);
  };

  return (
    <div className="app-container">
      <header>
        <h1>SignConnect</h1>
        <Auth user={user} />
      </header>
      <main>
        <TranscriptionDisplay transcription={transcription} />
        <Suggestions suggestions={suggestions} />
        <Controls
          user={user}
          onNewTranscription={handleNewTranscription}
          onNewSuggestions={handleNewSuggestions}
        />
      </main>
    </div>
  );
}

export default App;