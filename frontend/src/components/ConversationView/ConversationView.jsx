import React, { useEffect, useRef } from 'react';
import './ConversationView.css';

/**
 * Displays a list of conversation messages in a chat-like view.
 * @param {{ conversation: {text: string, sender: 'user' | 'other'}[] }} props
 */
function ConversationView({ conversation }) {
  const endOfMessagesRef = useRef(null);

  // Automatically scroll to the bottom when new messages are added
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  return (
    <div className="conversation-container">
      {conversation.length === 0 ? (
        <p className="placeholder-text">Transcription will appear here...</p>
      ) : (
        conversation.map((message, index) => (
          <div key={index} className={`message-bubble ${message.sender === 'user' ? 'user-message' : 'other-message'}`}>
            {message.text}
          </div>
        ))
      )}
      <div ref={endOfMessagesRef} />
    </div>
  );
}

export default ConversationView;