// frontend/src/services/api.js

// --- CHANGE: Import the 'auth' object directly, not the promise ---
import { auth } from '../firebaseConfig';

// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE_URL = '';

/**
 * Retrieves the Firebase authentication token from the currently signed-in user.
 * @returns {Promise<string|null>} A promise that resolves to the user's ID token, or null if no user is signed in.
 */
const getAuthToken = async () => {
  // --- CHANGE: Directly access auth.currentUser, no 'await' is needed here ---
  if (auth && auth.currentUser) {
    return auth.currentUser.getIdToken();
  }
  return null;
};

/**
 * A helper function for making authenticated API requests.
 * @param {string} url - The API endpoint.
 * @param {object} options - Fetch options (method, body, etc.).
 * @returns {Promise<any>} The JSON response from the API.
 */
const fetchAuthenticated = async (url, options = {}) => {
  try {
    const token = await getAuthToken();
    if (!token) {
      // This case should ideally not be hit if the UI prevents actions when logged out,
      // but it's good practice to have it.
      throw new Error("User not authenticated. Cannot make API call.");
    }

    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    console.log('API Call:', fullUrl);

    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    };

    if (options.body) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(fullUrl, { ...options, headers });
    console.log('API Response:', response.status, response.statusText);

    if (!response.ok) {
      const errorBody = await response.text();
      console.error("API Error Response:", errorBody);
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return null;
    }
    return response.json();
  } catch (error) {
    console.error('API Call Failed:', error);
    throw error;
  }
};

// --- No changes are needed to the functions below this line ---
// They will now work correctly because fetchAuthenticated is fixed.

// --- Preferences API ---
export const getPreferences = async () => {
  return await fetchAuthenticated('/api/users/me/preferences/');
};

export const addPreference = async (preferenceText) => {
  const payload = { preference_text: preferenceText };
  return await fetchAuthenticated('/api/users/me/preferences/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
};

export const deletePreference = async (preferenceId) => {
  await fetchAuthenticated(`/api/users/me/preferences/${preferenceId}`, {
    method: 'DELETE'
  });
  return null;
};

// --- Scenarios API ---
export const getScenarios = async () => {
  return await fetchAuthenticated('/api/users/me/scenarios/');
};

export const createScenario = async (scenario) => {
  return await fetchAuthenticated('/api/users/me/scenarios/', {
    method: 'POST',
    body: JSON.stringify(scenario)
  });
};

export const updateScenario = async (id, scenario) => {
  return await fetchAuthenticated(`/api/users/me/scenarios/${id}`, {
    method: 'PUT',
    body: JSON.stringify(scenario)
  });
};

export const deleteScenario = async (scenarioId) => {
  return await fetchAuthenticated(`/api/users/me/scenarios/${scenarioId}`, {
    method: 'DELETE'
  });
};

export const createQuestionForScenario = async (scenarioId, questionData) => {
  return await fetchAuthenticated(`/api/users/me/scenarios/${scenarioId}/questions/`, {
    method: 'POST',
    body: JSON.stringify(questionData)
  });
};

// --- Questions API ---
export const updateQuestion = async (questionId, questionData) => {
  return await fetchAuthenticated(`/api/users/me/questions/${questionId}`, {
    method: 'PUT',
    body: JSON.stringify(questionData)
  });
};

export const deleteQuestion = async (questionId) => {
  await fetchAuthenticated(`/api/users/me/questions/${questionId}`, {
    method: 'DELETE'
  });
  return null;
};

// --- Firebase Config API (Unauthenticated) ---
export const getFirebaseConfig = async () => {
  const response = await fetch(`${API_BASE_URL}/api/firebase-config`);
  if (!response.ok) {
    throw new Error("Could not fetch Firebase config");
  }
  return response.json();
};
