import React, { useState } from 'react';
import {
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
} from 'firebase/auth';
import { auth } from '../../firebaseConfig';
import './Auth.css';

/**
 * A "presentational" component that displays auth UI.
 * It receives the current user as a prop from its parent and calls
 * auth functions from Firebase.
 * @param {{ user: import('firebase/auth').User | null }} props
 */
function Auth({ user }) {
  // State for the input fields remains local to this component
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Note: The `useEffect` and `onAuthStateChanged` are GONE from this component.

  const handleGoogleSignIn = async () => {
    // ... (This function remains the same)
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error("Google Sign-In Error:", error);
      setError(error.message);
    }
  };

  const handleSignUp = async (e) => {
    // ... (This function remains the same)
    e.preventDefault();
    try {
      await createUserWithEmailAndPassword(auth, email, password);
      setEmail('');
      setPassword('');
    } catch (error) {
      console.error("Sign Up Error:", error);
      setError(error.message);
    }
  };

  const handleEmailSignIn = async (e) => {
    // ... (This function remains the same)
    e.preventDefault();
    try {
      await signInWithEmailAndPassword(auth, email, password);
      setEmail('');
      setPassword('');
    } catch (error) {
      console.error("Email Sign-In Error:", error);
      setError(error.message);
    }
  };

  const handleSignOut = async () => {
    // ... (This function remains the same)
    try {
      await signOut(auth);
    } catch (error) {
      console.error("Sign Out Error:", error);
      setError(error.message);
    }
  };

  // This conditional rendering now uses the `user` PROP
  if (user) {
    return (
      <div className="auth-container">
        <span>Welcome, {user.displayName || user.email}</span>
        <button onClick={handleSignOut} className="auth-button">Sign Out</button>
      </div>
    );
  }

  // The sign-in form remains the same
  return (
    <div className="auth-container">
      <button onClick={handleGoogleSignIn} className="auth-button google-button">Sign In with Google</button>
      <p className="or-divider">----- OR -----</p>
      {error && <p className="error-message">{error}</p>}
      <form className="auth-form">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email Address"
          className="auth-input"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="auth-input"
        />
        <div className="form-buttons">
          <button onClick={handleEmailSignIn} type="submit">Log In</button>
          <button onClick={handleSignUp} type="submit">Sign Up</button>
        </div>
      </form>
    </div>
  );
}

export default Auth;