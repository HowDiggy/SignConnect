// frontend/script.js

// Declare global variables for state management
let socket;
let mediaRecorder;
let currentUserToken = null;
let lastFinalTranscript = "";
let availableScenarios = [];
let userStream;

/**
 * Initializes the entire frontend logic after Firebase has been configured.
 */
export function initializeFrontendLogic() {
    // Get all necessary DOM elements
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const signUpBtn = document.getElementById("signup-btn");
    const logInBtn = document.getElementById("login-btn");
    const logOutBtn = document.getElementById("logout-btn");
    const userStatus = document.getElementById("user-status");
    const toggleViewBtn = document.getElementById("toggle-view-btn");
    const authContainer = document.getElementById("auth-container");
    const userInfoContainer = document.getElementById("user-info-container");
    const transcriptionContainer = document.getElementById("transcription-container");
    const managementContainer = document.getElementById("management-container");
    const startBtn = document.getElementById("start-btn");
    const statusDisplay = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");
    const suggestionsContainer = document.getElementById("suggestions-container");
    const scenarioNameInput = document.getElementById("scenario-name");
    const addScenarioBtn = document.getElementById("add-scenario-btn");
    const scenariosListDiv = document.getElementById("scenarios-list");
    const addPreferenceBtn = document.getElementById('add-preference-btn');
    const scenarioSelectForQa = document.getElementById("scenario-select-for-qa");

    const { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged, signOut } = window.firebaseAuth;
    const auth = getAuth(window.firebaseApp);

    // --- Authentication Logic ---
    onAuthStateChanged(auth, user => {
        if (user) {
            user.getIdToken().then(token => {
                currentUserToken = token;
                userStatus.textContent = `Logged in as ${user.email}`;
                authContainer.style.display = "none";
                userInfoContainer.style.display = "block";
                transcriptionContainer.style.display = "block";
                managementContainer.style.display = "none";
                populateScenarioSelect();
            });
        } else {
            currentUserToken = null;
            authContainer.style.display = "block";
            userInfoContainer.style.display = "none";
            transcriptionContainer.style.display = "none";
            managementContainer.style.display = "none";
            scenarioSelectForQa.innerHTML = '<option value="">Login to load scenarios</option>';
        }
    });

    signUpBtn.addEventListener("click", () => {
        const email = emailInput.value;
        const password = passwordInput.value;
        createUserWithEmailAndPassword(auth, email, password)
            .then(userCredential => console.log("Signed up successfully:", userCredential.user))
            .catch(error => {
                console.error("Sign up error:", error);
                alert(error.message);
            });
    });

    logInBtn.addEventListener("click", () => {
        const email = emailInput.value;
        const password = passwordInput.value;
        signInWithEmailAndPassword(auth, email, password)
            .then(userCredential => console.log("Logged in successfully:", userCredential.user))
            .catch(error => {
                console.error("Log in error:", error);
                alert(error.message);
            });
    });

    logOutBtn.addEventListener("click", () => {
        signOut(auth).catch(error => console.error("Logout error:", error));
    });

    // --- View Toggling Logic ---
    toggleViewBtn.addEventListener("click", () => {
        const isManagementView = managementContainer.style.display === "block";
        if (isManagementView) {
            managementContainer.style.display = "none";
            transcriptionContainer.style.display = "block";
            toggleViewBtn.textContent = "Manage Scenarios & Preferences";
            populateScenarioSelect();
        } else {
            managementContainer.style.display = "block";
            transcriptionContainer.style.display = "none";
            toggleViewBtn.textContent = "Back to Transcription";
            fetchAndDisplayScenarios();
            fetchAndDisplayPreferences();
        }
    });

    // --- Helper to convert Blob to Base64 ---
    function blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64String = reader.result.split(',')[1];
                resolve(base64String);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    // --- Transcription Logic ---
    startBtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        } else {
            if (!currentUserToken) return alert("You must be logged in to start.");
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    userStream = stream;
                    mediaRecorder = new MediaRecorder(userStream, { mimeType: 'audio/webm;codecs=opus' });

                    mediaRecorder.ondataavailable = async (event) => {
                        if (event.data.size > 0 && socket && socket.readyState === WebSocket.OPEN) {
                            const audioBase64 = await blobToBase64(event.data);
                            socket.send(JSON.stringify({ type: "audio", data: audioBase64 }));
                        }
                    };

                    mediaRecorder.onstop = () => {
                        if (userStream) {
                            userStream.getTracks().forEach(track => track.stop());
                        }
                        if (socket) socket.close();
                        startBtn.textContent = "Start Transcription";
                        statusDisplay.textContent = "Idle";
                    };

                    transcriptionDisplay.innerHTML = "";
                    suggestionsContainer.innerHTML = "";

                    setupWebSocket(currentUserToken);
                    mediaRecorder.start(1000);
                    startBtn.textContent = "Stop Transcription";
                })
                .catch(error => console.error("Microphone access error:", error));
        }
    });

    function setupWebSocket(token) {
        const wsUrl = `ws://localhost:8000/ws?token=${token}`;
        socket = new WebSocket(wsUrl);
        socket.onopen = () => statusDisplay.textContent = "Connected";
        socket.onclose = () => {
            statusDisplay.textContent = "Disconnected";
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
            }
        };
        socket.onerror = (error) => console.error("WebSocket error:", error);
        socket.onmessage = (event) => {
            const message = event.data;
            const [prefix, content] = message.split(/:(.*)/s);

            if (prefix === "interim") {
                let liveBubble = transcriptionDisplay.querySelector('.live-transcript');
                if (!liveBubble) {
                    liveBubble = document.createElement('div');
                    liveBubble.classList.add('transcript-message', 'message-them', 'live-transcript');
                    transcriptionDisplay.appendChild(liveBubble);
                }
                liveBubble.textContent = content;
                transcriptionDisplay.scrollTop = transcriptionDisplay.scrollHeight;
            } else if (prefix === "final") {
                let liveBubble = transcriptionDisplay.querySelector('.live-transcript');
                if (liveBubble) {
                    liveBubble.textContent = content;
                    liveBubble.classList.remove('live-transcript');
                } else {
                    appendMessageToTranscript(content, 'them');
                }
                lastFinalTranscript = content;
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ type: "get_suggestions", transcript: lastFinalTranscript }));
                }
            } else if (prefix === "suggestions") {
                const suggestions = JSON.parse(content);
                suggestionsContainer.innerHTML = "";
                suggestions.forEach(suggestion => {
                    const button = document.createElement("button");
                    button.textContent = suggestion;
                    button.addEventListener('click', () => {
                        appendMessageToTranscript(suggestion, 'me');
                        suggestionsContainer.innerHTML = '';
                    });
                    suggestionsContainer.appendChild(button);
                });
                const typeCustomAnswerButton = document.createElement('button');
                typeCustomAnswerButton.textContent = 'Type Custom Answer';
                typeCustomAnswerButton.id = 'type-custom-answer-btn';
                typeCustomAnswerButton.addEventListener('click', showMyAnswerInput);
                suggestionsContainer.appendChild(typeCustomAnswerButton);
            }
        };
    }

    function appendMessageToTranscript(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('transcript-message', `message-${sender}`);
        messageDiv.textContent = text;
        transcriptionDisplay.appendChild(messageDiv);
        transcriptionDisplay.scrollTop = transcriptionDisplay.scrollHeight;
    }

    function showMyAnswerInput() {
        suggestionsContainer.innerHTML = "";
        let myAnswerInput = document.createElement('textarea');
        myAnswerInput.id = 'my-answer-input';
        myAnswerInput.placeholder = 'My Answer';
        suggestionsContainer.appendChild(myAnswerInput);
        let sendMyAnswerButton = document.createElement('button');
        sendMyAnswerButton.id = 'send-my-answer-btn';
        sendMyAnswerButton.textContent = 'Send';
        sendMyAnswerButton.addEventListener('click', sendMyAnswer);
        suggestionsContainer.appendChild(sendMyAnswerButton);
        myAnswerInput.focus();
    }

    async function sendMyAnswer() {
        const myAnswerInput = document.getElementById('my-answer-input');
        const userAnswer = myAnswerInput ? myAnswerInput.value.trim() : "";
        if (!userAnswer) return alert("Please enter your answer.");

        appendMessageToTranscript(userAnswer, 'me');
        suggestionsContainer.innerHTML = "";

        const selectedScenarioId = scenarioSelectForQa.value;
        const questionText = lastFinalTranscript.trim();
        if (!currentUserToken || !selectedScenarioId || !questionText) {
            return console.warn("Could not save Q&A due to missing data.");
        }

        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${selectedScenarioId}/questions/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentUserToken}` },
                body: JSON.stringify({ question_text: questionText, user_answer_text: userAnswer })
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to save.");
            console.log("Custom Q&A saved successfully!");
            if (managementContainer.style.display === "block") fetchAndDisplayScenarios();
        } catch (error) {
            console.error("Error saving custom answer:", error);
        }
    }

    // --- All Scenario and Preference Management functions follow ---
    addScenarioBtn.addEventListener("click", addScenario);
    addPreferenceBtn.addEventListener('click', addPreference);

    function attachScenarioEventListeners() {
        document.querySelectorAll('.edit-scenario-btn').forEach(b => b.addEventListener('click', toggleScenarioEditMode));
        document.querySelectorAll('.save-scenario-btn').forEach(b => b.addEventListener('click', updateScenario));
        document.querySelectorAll('.cancel-scenario-edit-btn').forEach(b => b.addEventListener('click', toggleScenarioEditMode));
        document.querySelectorAll('.delete-scenario-btn').forEach(b => b.addEventListener('click', deleteScenario));
        document.querySelectorAll('.add-question-btn').forEach(b => b.addEventListener('click', addQuestionToScenario));
        document.querySelectorAll('.delete-question-btn').forEach(b => b.addEventListener('click', deleteQuestion));
        document.querySelectorAll('.edit-question-btn').forEach(b => b.addEventListener('click', toggleQuestionEditMode));
        document.querySelectorAll('.cancel-edit-btn').forEach(b => b.addEventListener('click', toggleQuestionEditMode));
        document.querySelectorAll('.save-question-btn').forEach(b => b.addEventListener('click', updateQuestion));
    }

    function attachPreferenceEventListeners() {
        document.querySelectorAll('.edit-preference-btn').forEach(btn => btn.addEventListener('click', togglePreferenceEditMode));
        document.querySelectorAll('.save-preference-btn').forEach(btn => btn.addEventListener('click', updatePreference));
        document.querySelectorAll('.cancel-preference-edit-btn').forEach(btn => btn.addEventListener('click', togglePreferenceEditMode));
        document.querySelectorAll('.delete-preference-btn').forEach(btn => btn.addEventListener('click', deletePreference));
    }

    async function populateScenarioSelect() {
        if (!currentUserToken) return;
        try {
            const response = await fetch("http://localhost:8000/users/me/scenarios/", { headers: { "Authorization": `Bearer ${currentUserToken}` } });
            if (!response.ok) throw new Error("Failed to fetch scenarios");
            availableScenarios = await response.json();
            scenarioSelectForQa.innerHTML = '';
            const freestyleScenarioName = "Freestyle";
            let freestyleScenario = availableScenarios.find(s => s.name === freestyleScenarioName);

            if (!freestyleScenario) {
                try {
                    const createResponse = await fetch("http://localhost:8000/users/me/scenarios/", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentUserToken}`},
                        body: JSON.stringify({ name: freestyleScenarioName, description: "A default scenario for general conversations." })
                    });
                    if (!createResponse.ok) {
                        const errorData = await createResponse.json();
                        if (!errorData.detail?.includes("already exists")) throw new Error(errorData.detail || "Failed to create 'Freestyle' scenario.");
                    }
                    const reFetchResponse = await fetch("http://localhost:8000/users/me/scenarios/", { headers: { "Authorization": `Bearer ${currentUserToken}` } });
                    if (!reFetchResponse.ok) throw new Error("Failed to re-fetch.");
                    availableScenarios = await reFetchResponse.json();
                    freestyleScenario = availableScenarios.find(s => s.name === freestyleScenarioName);
                } catch (createError) { console.error("Error creating 'Freestyle' scenario:", createError); }
            }
            availableScenarios.forEach(scenario => {
                const option = document.createElement("option");
                option.value = scenario.id;
                option.textContent = scenario.name;
                scenarioSelectForQa.appendChild(option);
            });
            if (freestyleScenario) scenarioSelectForQa.value = freestyleScenario.id;
        } catch (error) { console.error("Error populating scenarios:", error); }
    }

    async function fetchAndDisplayScenarios() {
        if (!currentUserToken) return;
        scenariosListDiv.innerHTML = '<h3>Your Scenarios</h3>';
        try {
            const response = await fetch("http://localhost:8000/users/me/scenarios/", { headers: { "Authorization": `Bearer ${currentUserToken}` } });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to fetch");
            const scenarios = await response.json();
            if (scenarios.length === 0) return scenariosListDiv.innerHTML += "<p>You haven't created any scenarios yet.</p>";

            scenarios.forEach(scenario => {
                const scenarioDiv = document.createElement("div");
                scenarioDiv.className = "scenario-item";
                scenarioDiv.innerHTML = `<div class="scenario-header" data-scenario-id="${scenario.id}"><h4>${scenario.name}</h4><div class="edit-form"><input type="text" class="edit-scenario-name-input" value="${scenario.name}"></div><button class="edit-scenario-btn">Edit Name</button><button class="save-scenario-btn">Save</button><button class="cancel-scenario-edit-btn">Cancel</button><button class="delete-scenario-btn">Delete Scenario</button></div><p>${scenario.description || 'No description'}</p><ul>${scenario.questions.map(q => `<li data-question-id="${q.id}"><div class="qa-text"><span><b>Q:</b> ${q.question_text}</span><br><span><b>A:</b> ${q.user_answer_text}</span></div><div class="edit-form"><input type="text" class="edit-question-input" value="${q.question_text}"><input type="text" class="edit-answer-input" value="${q.user_answer_text}"></div><button class="edit-question-btn">Edit</button><button class="save-question-btn">Save</button><button class="cancel-edit-btn">Cancel</button><button class="delete-question-btn">Delete Q</button></li>`).join('')}</ul><div class="add-question-form"><input type="text" placeholder="Question" class="scenario-question-text"><input type="text" placeholder="Your Answer" class="scenario-answer-text"><button class="add-question-btn" data-scenario-id="${scenario.id}">Add Question</button></div>`;
                scenariosListDiv.appendChild(scenarioDiv);
            });
            attachScenarioEventListeners();
        } catch (error) {
            console.error("Error fetching scenarios:", error);
            scenariosListDiv.innerHTML += `<p style="color:red;">Error: ${error.message}</p>`;
        }
    }

    async function addScenario(event) {
        event.preventDefault();
        const scenarioName = scenarioNameInput.value;
        if (!scenarioName.trim()) return alert("Please enter a scenario name.");
        try {
            const response = await fetch("http://localhost:8000/users/me/scenarios/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentUserToken}`},
                body: JSON.stringify({ name: scenarioName, description: "" })
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to create");
            scenarioNameInput.value = "";
            fetchAndDisplayScenarios();
            populateScenarioSelect();
        } catch (error) {
            console.error("Error creating scenario:", error);
            alert(error.message);
        }
    }

    function toggleScenarioEditMode(event) {
        event.target.closest('.scenario-header').classList.toggle('editing');
    }

    async function updateScenario(event) {
        const headerDiv = event.target.closest('.scenario-header');
        const scenarioId = headerDiv.dataset.scenarioId;
        const newName = headerDiv.querySelector('.edit-scenario-name-input').value;
        if (!newName.trim()) return alert("Scenario name cannot be empty.");
        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${scenarioId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${currentUserToken}` },
                body: JSON.stringify({ name: newName })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update');
            fetchAndDisplayScenarios();
            populateScenarioSelect();
        } catch (error) {
            console.error('Error updating scenario:', error);
            alert(error.message);
        }
    }

    async function deleteScenario(event) {
        const scenarioId = event.target.closest('.scenario-header').dataset.scenarioId;
        if (!confirm("Delete this scenario and all its questions?")) return;
        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${scenarioId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${currentUserToken}` }
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to delete');
            fetchAndDisplayScenarios();
            populateScenarioSelect();
        } catch (error) {
            console.error('Error deleting scenario:', error);
            alert(error.message);
        }
    }

    async function addQuestionToScenario(event) {
        const button = event.target;
        const scenarioId = button.dataset.scenarioId;
        const form = button.closest('.add-question-form');
        const questionText = form.querySelector('.scenario-question-text').value;
        const userAnswerText = form.querySelector('.scenario-answer-text').value;
        if (!questionText.trim() || !userAnswerText.trim()) return alert("Please fill in both fields.");
        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${scenarioId}/questions/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentUserToken}`},
                body: JSON.stringify({ question_text: questionText, user_answer_text: userAnswerText })
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to add question");
            fetchAndDisplayScenarios();
        } catch (error) {
            console.error("Error adding question:", error);
            alert(error.message);
        }
    }

    function toggleQuestionEditMode(event) {
        event.target.closest('li').classList.toggle('editing');
    }

    async function updateQuestion(event) {
        const questionLi = event.target.closest('li');
        const questionId = questionLi.dataset.questionId;
        const newQuestionText = questionLi.querySelector('.edit-question-input').value;
        const newAnswerText = questionLi.querySelector('.edit-answer-input').value;
        try {
            const response = await fetch(`http://localhost:8000/users/me/questions/${questionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${currentUserToken}`},
                body: JSON.stringify({ question_text: newQuestionText, user_answer_text: newAnswerText })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update');
            fetchAndDisplayScenarios();
        } catch (error) {
            console.error('Error updating question:', error);
            alert(error.message);
        }
    }

    async function deleteQuestion(event) {
        const questionId = event.target.closest('li').dataset.questionId;
        if (!confirm("Delete this question?")) return;
        try {
            const response = await fetch(`http://localhost:8000/users/me/questions/${questionId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${currentUserToken}` }
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to delete');
            fetchAndDisplayScenarios();
        } catch (error) {
            console.error('Error deleting question:', error);
            alert(error.message);
        }
    }

    async function fetchAndDisplayPreferences() {
        if (!currentUserToken) return;
        const preferencesListDiv = document.getElementById('preferences-list');
        try {
            const response = await fetch("http://localhost:8000/users/me/preferences/", { headers: { 'Authorization': `Bearer ${currentUserToken}` } });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to fetch");
            const preferences = await response.json();
            preferencesListDiv.innerHTML = '';
            const ul = document.createElement('ul');
            if (preferences.length > 0) {
                preferences.forEach(pref => {
                    const li = document.createElement('li');
                    li.dataset.preferenceId = pref.id;
                    li.innerHTML = `<span class="preference-text">${pref.preference_text}</span><div class="edit-form"><textarea class="edit-preference-textarea">${pref.preference_text}</textarea></div><button class="edit-preference-btn">Edit</button><button class="save-preference-btn">Save</button><button class="cancel-preference-edit-btn">Cancel</button><button class="delete-preference-btn">Delete</button>`;
                    ul.appendChild(li);
                });
            }
            preferencesListDiv.appendChild(ul);
            attachPreferenceEventListeners();
        } catch (error) {
            console.error("Error fetching preferences:", error);
            preferencesListDiv.innerHTML = `<p style="color:red;">${error.message}</p>`;
        }
    }

    async function addPreference(event) {
        event.preventDefault();
        const textInput = document.getElementById('preference-text-input');
        const preferenceText = textInput.value.trim();
        if (!preferenceText) return alert("Please enter a preference.");
        try {
            const response = await fetch("http://localhost:8000/users/me/preferences/", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${currentUserToken}`},
                body: JSON.stringify({ preference_text: preferenceText })
            });
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.detail?.[0]?.msg || errorData.detail || "Failed to add";
                throw new Error(errorMessage);
            }
            textInput.value = '';
            fetchAndDisplayPreferences();
        } catch (error) {
            console.error("Error adding preference:", error);
            alert(error.message);
        }
    }

    function togglePreferenceEditMode(event) {
        event.target.closest('li').classList.toggle('editing');
    }

    async function updatePreference(event) {
        const preferenceLi = event.target.closest('li');
        const preferenceId = preferenceLi.dataset.preferenceId;
        const newText = preferenceLi.querySelector('.edit-preference-textarea').value;
        if (!newText.trim()) return alert("Preference text cannot be empty.");
        try {
            const response = await fetch(`http://localhost:8000/users/me/preferences/${preferenceId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${currentUserToken}` },
                body: JSON.stringify({ preference_text: newText })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update');
            fetchAndDisplayPreferences();
        } catch (error) {
            console.error('Error updating preference:', error);
            alert(error.message);
        }
    }

    async function deletePreference(event) {
        const preferenceId = event.target.closest('li').dataset.preferenceId;
        if (!confirm("Are you sure?")) return;
        try {
            const response = await fetch(`http://localhost:8000/users/me/preferences/${preferenceId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${currentUserToken}` }
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to delete');
            fetchAndDisplayPreferences();
        } catch (error) {
            console.error('Error deleting preference:', error);
            alert(error.message);
        }
    }
}