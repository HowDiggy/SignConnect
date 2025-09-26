// frontend/src/firebaseConfig.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

let app;
let auth;

/**
 * Initializes the Firebase application by fetching configuration from the backend.
 * This function ensures that Firebase is only initialized once.
 *
 * Pre-conditions:
 * - The backend endpoint '/api/firebase-config' must be available and return a valid Firebase config object.
 *
 * Post-conditions:
 * - The 'app' and 'auth' variables are initialized with the Firebase app and auth instances.
 * - If called again, the function will not re-initialize the app.
 *
 * @returns {Promise<void>} A promise that resolves when initialization is complete.
 * @throws {Error} Throws an error if the configuration cannot be fetched or if initialization fails.
 */
export const initializeFirebase = async () => {
  // Prevent re-initialization
  if (app) {
    return;
  }

  try {
    // 1. Fetch the configuration from our secure backend endpoint
    const response = await fetch('/api/firebase-config');
    if (!response.ok) {
      throw new Error('Failed to fetch Firebase config from the backend.');
    }
    const firebaseConfig = await response.json();
    console.log("1. [firebaseConfig.js] Received config from backend:", firebaseConfig);

    // 2. Initialize the app and auth services using ONLY the fetched config
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    console.log("2. [firebaseConfig.js] Firebase Initialized. The 'auth' object is:", auth);

  } catch (error) {
    console.error("Firebase initialization failed:", error);
    throw error;
  }
};

// Export the auth object. It will be undefined until initializeFirebase() completes.
export { auth };
