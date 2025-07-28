import React, { useState } from 'react';
import './Settings.css';

// We will build these sub-components next
// import Preferences from './Preferences';
import Preferences from './Preferences';
// import Scenarios from './Scenarios';

function Settings({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('preferences');

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button onClick={onClose} className="close-button">&times;</button>
        </div>
        <div className="modal-body">
          <div className="tabs">
            <button
              className={`tab-button ${activeTab === 'preferences' ? 'active' : ''}`}
              onClick={() => setActiveTab('preferences')}
            >
              User Preferences
            </button>
            <button
              className={`tab-button ${activeTab === 'scenarios' ? 'active' : ''}`}
              onClick={() => setActiveTab('scenarios')}
            >
              Scenarios
            </button>
          </div>
          <div className="tab-content">
            {activeTab === 'preferences' && <Preferences />}
            {activeTab === 'scenarios' && <p>Scenarios UI will go here.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;