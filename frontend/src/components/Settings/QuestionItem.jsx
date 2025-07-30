import React, { useState } from 'react';
import { createQuestionForScenario, updateQuestion, deleteQuestion } from '../../services/api';
import './QuestionItem.css';

function QuestionItem({ scenarioId, initialQuestions = [] }) {
  const [questions, setQuestions] = useState(initialQuestions);
  const [error, setError] = useState('');
  
  // State for the "add new" form
  const [newQuestion, setNewQuestion] = useState('');
  const [newAnswer, setNewAnswer] = useState('');

  // State for inline editing
  const [editingId, setEditingId] = useState(null);
  const [editQuestionText, setEditQuestionText] = useState('');
  const [editAnswerText, setEditAnswerText] = useState('');

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
  
  const handleEditClick = (question) => {
    setEditingId(question.id);
    setEditQuestionText(question.question_text);
    setEditAnswerText(question.user_answer_text);
  };
  
  const handleUpdateQuestion = async (e) => {
    e.preventDefault();
    if (!editingId) return;
    try {
      const updated = await updateQuestion(editingId, {
        question_text: editQuestionText,
        user_answer_text: editAnswerText
      });
      setQuestions(prev => prev.map(q => q.id === editingId ? updated : q));
      setEditingId(null);
    } catch(err) {
      console.error("Failed to update question:", err);
      setError("Could not update the question.");
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    try {
      await deleteQuestion(questionId);
      setQuestions(prev => prev.filter(q => q.id !== questionId));
    } catch (err) {
      console.error("Failed to delete question:", err);
      setError("Could not delete the question.");
    }
  };

  return (
    <div className="questions-container">
      <h5 className="questions-header">Questions & Answers</h5>
      {questions.length > 0 && (
        <ul className="questions-list">
          {questions.map(q => (
            <li key={q.id} className="question-item">
              {editingId === q.id ? (
                <form onSubmit={handleUpdateQuestion} className="question-edit-form">
                  <input type="text" value={editQuestionText} onChange={(e) => setEditQuestionText(e.target.value)} />
                  <input type="text" value={editAnswerText} onChange={(e) => setEditAnswerText(e.target.value)} />
                  <div className="q-edit-actions">
                    <button type="submit">Save</button>
                    <button type="button" onClick={() => setEditingId(null)}>Cancel</button>
                  </div>
                </form>
              ) : (
                <div className="question-display">
                  <div>
                    <p><strong>Q:</strong> {q.question_text}</p>
                    <p><strong>A:</strong> {q.user_answer_text}</p>
                  </div>
                  <div className="q-actions">
                    <button onClick={() => handleEditClick(q)}>Edit</button>
                    <button onClick={() => handleDeleteQuestion(q.id)}>Delete</button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleAddQuestion} className="question-form">
        <input type="text" value={newQuestion} onChange={(e) => setNewQuestion(e.target.value)} placeholder="Anticipated Question" />
        <input type="text" value={newAnswer} onChange={(e) => setNewAnswer(e.target.value)} placeholder="Your Prepared Answer" />
        <button type="submit">Add Q&A</button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
}

export default QuestionItem;