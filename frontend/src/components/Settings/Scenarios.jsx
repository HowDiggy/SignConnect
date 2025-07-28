import React, { useState, useEffect, useCallback } from 'react';
import { getScenarios, createScenario, updateScenario, deleteScenario } from '../../services/api';
import QuestionItem from './QuestionItem'; // Import the new component
import './Scenarios.css';

function Scenarios() {
  const [scenarios, setScenarios] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // State for forms
  const [newScenarioName, setNewScenarioName] = useState('');
  const [newScenarioDesc, setNewScenarioDesc] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [editingDesc, setEditingDesc] = useState('');

  // State to track which scenario is expanded
  const [activeScenarioId, setActiveScenarioId] = useState(null);

  const fetchScenarios = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await getScenarios();
      setScenarios(data || []);
    } catch (err) {
      console.error("Failed to fetch scenarios:", err);
      setError('Could not load scenarios.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  const handleCreateScenario = async (e) => {
    e.preventDefault();
    if (!newScenarioName.trim()) return;
    try {
      const newScenario = await createScenario({
        name: newScenarioName,
        description: newScenarioDesc,
      });
      setScenarios(prev => [newScenario, ...prev]);
      setNewScenarioName('');
      setNewScenarioDesc('');
    } catch (err) {
      console.error("Failed to create scenario:", err);
      setError("Could not create the new scenario.");
    }
  };

  const handleDeleteScenario = async (scenarioId) => {
    if (window.confirm("Are you sure you want to delete this scenario?")) {
      try {
        await deleteScenario(scenarioId);
        setScenarios(prev => prev.filter(s => s.id !== scenarioId));
      } catch (err) {
        console.error("Failed to delete scenario:", err);
        setError("Could not delete the scenario.");
      }
    }
  };

  const handleEditClick = (scenario) => {
    setEditingId(scenario.id);
    setEditingName(scenario.name);
    setEditingDesc(scenario.description || '');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
  };

  const handleUpdateScenario = async (e) => {
    e.preventDefault();
    if (!editingId || !editingName.trim()) return;
    try {
      const updated = await updateScenario(editingId, {
        name: editingName,
        description: editingDesc,
      });
      setScenarios(prev => prev.map(s => s.id === editingId ? updated : s));
      setEditingId(null);
    } catch (err) {
      console.error("Failed to update scenario:", err);
      setError("Could not update the scenario.");
    }
  };

  const toggleScenario = (scenarioId) => {
    setActiveScenarioId(prevId => (prevId === scenarioId ? null : scenarioId));
  };

  return (
    <div className="scenarios-container">
      <form onSubmit={handleCreateScenario} className="scenario-form">
        <h3>Create New Scenario</h3>
        <input
          type="text"
          value={newScenarioName}
          onChange={(e) => setNewScenarioName(e.target.value)}
          placeholder="Scenario Name (e.g., Hotel Check-in)"
          required
        />
        <textarea
          value={newScenarioDesc}
          onChange={(e) => setNewScenarioDesc(e.target.value)}
          placeholder="Description (optional)"
          rows="2"
        />
        <button type="submit">Create Scenario</button>
      </form>
      <hr className="divider" />

      {error && <p className="error-message">{error}</p>}
      
      <div className="scenarios-list">
        {isLoading ? <p>Loading...</p> : scenarios.map(scenario => (
          <div key={scenario.id} className="scenario-item-container">
            <div className="scenario-item">
              {editingId === scenario.id ? (
                <form onSubmit={handleUpdateScenario} className="edit-form">
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                  />
                  <textarea
                    value={editingDesc}
                    onChange={(e) => setEditingDesc(e.target.value)}
                    rows="2"
                  />
                  <div className="edit-actions">
                    <button type="submit">Save</button>
                    <button type="button" onClick={handleCancelEdit}>Cancel</button>
                  </div>
                </form>
              ) : (
                <>
                  <div className="scenario-details" onClick={() => toggleScenario(scenario.id)}>
                    <h4 className="scenario-name">{scenario.name}</h4>
                    <p className="scenario-description">{scenario.description}</p>
                  </div>
                  <div className="scenario-actions">
                    <button onClick={() => handleEditClick(scenario)}>Edit</button>
                    <button onClick={() => handleDeleteScenario(scenario.id)} className="delete-button">Delete</button>
                  </div>
                </>
              )}
            </div>
            {activeScenarioId === scenario.id && (
              <QuestionItem
                scenarioId={scenario.id}
                initialQuestions={scenario.questions}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default Scenarios;