// frontend/src/firebaseConfig.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import config from './config/environment.js';

// Initialize Firebase using environment configuration
const app = initializeApp(config.firebase);

// Export the auth service to be used in other components
export const auth = getAuth(app);
