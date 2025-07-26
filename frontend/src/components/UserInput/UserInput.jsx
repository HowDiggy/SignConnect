import React, { useState } from 'react';
import './UserInput.css';

/**
 * A component with a text input and a send button for user messages.
 * @param {{
 * onSendMessage: (message: string) => void,
 * isDisabled: boolean
 * }} props
 */
function UserInput({ onSendMessage, isDisabled }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onSendMessage(text.trim());
      setText(''); // Clear the input after sending
    }
  };

  return (
    <form className="user-input-form" onSubmit={handleSubmit}>
      <input
        type="text"
        className="user-input-field"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type your own response..."
        disabled={isDisabled}
      />
      <button type="submit" className="send-button" disabled={isDisabled || !text.trim()}>
        Send
      </button>
    </form>
  );
}

export default UserInput;