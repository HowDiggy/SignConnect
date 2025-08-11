// frontend/src/services/api.js
import { auth } from '../firebaseConfig';
import config from '../config/environment.js';

// Use environment configuration instead of hardcoded URL
const API_BASE_URL = config.apiBaseUrl;

// A helper function to get the user's auth token
const getAuthToken = async () => {
  if (!auth.currentUser) throw new Error("User not authenticated");
  return await auth.currentUser.getIdToken();
};

// A helper for making authenticated requests
const fetchAuthenticated = async (url, options = {}) => {
  const token = await getAuthToken();
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };

  // Only add Content-Type header if there is a body
  if (options.body) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const errorBody = await response.text();
    console.error("API Error Response:", errorBody);
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  // Handle cases with no JSON response body (like DELETE)
  if (response.status === 204 || response.headers.get("content-length") === "0") {
      return null;
  }
  return response.json();
};

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
  // DELETE requests don't have a body, so we return null on success
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
