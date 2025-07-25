import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebaseConfig';
import Auth from './components/Auth/Auth';
import Controls from './components/Controls/Controls';
import TranscriptionDisplay from './components/TranscriptionDisplay/TranscriptionDisplay';
import Suggestions from './components/Suggestions/Suggestions';
import './App.css';

function App() {
  // The user state is now "lifted" to the App component
  const [user, setUser] = useState(null);

  // This effect hook now runs in App, setting the user for the whole application
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    // Cleanup subscription on component unmount
    return () => unsubscribe();
  }, []);

  return (
    <div className="app-container">
      <header>
        <h1>SignConnect</h1>
        {/* We now pass the user object down to the Auth component as a prop */}
        <Auth user={user} />
      </header>
      <main>
        {/* Later, we can pass the user object to these components as well */}
        <TranscriptionDisplay />
        <Suggestions />
        <Controls user={user} />
      </main>
    </div>
  );
}

export default App;