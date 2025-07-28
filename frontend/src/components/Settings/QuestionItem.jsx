import React, { useState } from 'react';
import { createQuestionForScenario } from '../../services/api';
import './QuestionItem.css';

function QuestionItem({ scenarioId, initialQuestions = [] }) {
  const [questions, setQuestions] = useState(initialQuestions);
  const [newQuestion, setNewQuestion] = useState('');
  const [newAnswer, setNewAnswer] = useState('');
  const [error, setError] = useState('');

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    if (!newQuestion.trim() || !newAnswer.trim()) {
      setError("Both question and answer are required.");
      return;
    }
    setError('');

    try {
      const createdQuestion = await createQuestionForScenario(scenarioId, {
        question_text: newQuestion,
        user_answer_text: newAnswer,
      });
      setQuestions(prev => [...prev, createdQuestion]);
      setNewQuestion('');
      setNewAnswer('');
    } catch (err) {
      console.error("Failed to add question:", err);
      setError("Could not save the new question.");
    }
  };

  return (
    <div className="questions-container">
      <h5 className="questions-header">Questions & Answers</h5>
      {questions.length > 0 && (
        <ul className="questions-list">
          {questions.map(q => (
            <li key={q.id} className="question-item">
              <p><strong>Q:</strong> {q.question_text}</p>
              <p><strong>A:</strong> {q.user_answer_text}</p>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleAddQuestion} className="question-form">
        <input
          type="text"
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          placeholder="Anticipated Question"
        />
        <input
          type="text"
          value={newAnswer}
          onChange={(e) => setNewAnswer(e.target.value)}
          placeholder="Your Prepared Answer"
        />
        <button type="submit">Add Q&A</button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
}

export default QuestionItem;