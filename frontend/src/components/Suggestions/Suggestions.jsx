import React from 'react';
import './Suggestions.css';

function Suggestions({ suggestions }) {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="suggestions-container">
      <h3>Suggestions:</h3>
      <div className="suggestions-list">
        {suggestions.map((word, index) => (
          <button key={index} className="suggestion-item">
            {word}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Suggestions;