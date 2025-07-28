import React, { useState, useEffect, useCallback } from 'react';
import { getPreferences, addPreference, deletePreference } from '../../services/api';
import './Preferences.css';

function Preferences() {
  const [preferences, setPreferences] = useState([]);
  const [newPreferenceText, setNewPreferenceText] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchPreferences = useCallback(async () => {
    try {
      setError('');
      setIsLoading(true);
      const data = await getPreferences();
      setPreferences(data || []);
    } catch (err) {
      console.error("Failed to fetch preferences:", err);
      setError('Could not load preferences.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  const handleAddPreference = async (e) => {
    e.preventDefault();
    if (!newPreferenceText.trim()) return;

    try {
      const newPref = await addPreference(newPreferenceText);
      setPreferences(prev => [...prev, newPref]);
      setNewPreferenceText(''); // Clear input
    } catch (err) {
      console.error("Failed to add preference:", err);
      setError('Could not save new preference.');
    }
  };

  const handleDeletePreference = async (preferenceId) => {
    try {
      await deletePreference(preferenceId);
      setPreferences(prev => prev.filter(p => p.id !== preferenceId));
    } catch (err) {
      console.error("Failed to delete preference:", err);
      setError('Could not delete preference.');
    }
  };

  return (
    <div className="preferences-container">
      <p className="form-description">
        Add details about yourself so the AI can provide more personalized suggestions. For example: "My name is Paulo" or "I am a software engineer."
      </p>
      
      <form onSubmit={handleAddPreference} className="add-preference-form">
        <input
          type="text"
          value={newPreferenceText}
          onChange={(e) => setNewPreferenceText(e.target.value)}
          placeholder="Add a new preference..."
        />
        <button type="submit" disabled={!newPreferenceText.trim()}>Add</button>
      </form>

      {error && <p className="error-message">{error}</p>}

      <div className="preferences-list">
        {isLoading ? (
          <p>Loading...</p>
        ) : (
          preferences.map(pref => (
            <div key={pref.id} className="preference-item">
              <span>{pref.preference_text}</span>
              <button onClick={() => handleDeletePreference(pref.id)}>&times;</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Preferences;