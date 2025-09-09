import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

/**
 * Asynchronously fetches the Firebase configuration from the backend server.
 * @returns {Promise<object>} A promise that resolves to the Firebase config object.
 * @throws {Error} If the network response is not ok.
 */
const getFirebaseConfig = async () => {
  const response = await fetch('/api/firebase-config');
  if (!response.ok) {
    throw new Error('Failed to fetch Firebase config from backend.');
  }
  return response.json();
};

/**
 * Initializes the Firebase app and returns the auth instance.
 * This function is now the single source for getting the auth object.
 * @returns {Promise<import('firebase/auth').Auth>} A promise that resolves to the auth instance.
 */
const initializeAuth = async () => {
  const firebaseConfig = await getFirebaseConfig();
  const app = initializeApp(firebaseConfig);
  return getAuth(app);
};

// --- THIS IS THE KEY CHANGE ---
// We now export a promise that resolves to the auth object.
// We call our new async function to get it.
export const authPromise = initializeAuth();
