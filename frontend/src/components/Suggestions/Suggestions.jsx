import React from 'react';
import './Suggestions.css';

// Add the onSelectSuggestion prop
function Suggestions({ suggestions, onSelectSuggestion }) {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="suggestions-container">
      <h3>Suggestions:</h3>
      <div className="suggestions-list">
        {suggestions.map((word, index) => (
          // Add the onClick handler here
          <button
            key={index}
            className="suggestion-item"
            onClick={() => onSelectSuggestion(word)}
          >
            {word}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Suggestions;