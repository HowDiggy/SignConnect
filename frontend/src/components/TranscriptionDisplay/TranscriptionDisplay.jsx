import React from 'react';
import './TranscriptionDisplay.css';

/**
 * Displays the real-time transcription text.
 * @param {{ transcription: string }} props
 */
function TranscriptionDisplay({ transcription }) {
  return (
    <div className="transcription-display-container">
      <textarea
        value={transcription}
        readOnly
        placeholder="Transcription will appear here..."
      />
    </div>
  );
}

export default TranscriptionDisplay;