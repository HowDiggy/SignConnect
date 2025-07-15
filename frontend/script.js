document.addEventListener("DOMContentLoaded", () => {
    // Get all DOM elements
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

    // Firebase and State Variables
    const { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged, signOut } = window.firebaseAuth;
    const auth = getAuth(window.firebaseApp);
    let socket;
    let mediaRecorder;
    let currentUserToken = null;

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
            });
        } else {
            currentUserToken = null;
            authContainer.style.display = "block";
            userInfoContainer.style.display = "none";
            transcriptionContainer.style.display = "none";
            managementContainer.style.display = "none";
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
        } else {
            managementContainer.style.display = "block";
            transcriptionContainer.style.display = "none";
            toggleViewBtn.textContent = "Back to Transcription";
            fetchAndDisplayScenarios();
            fetchAndDisplayPreferences();
        }
    });

    // --- Event Listener Setup ---
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

    // --- Scenario Management ---
    async function fetchAndDisplayScenarios() {
        if (!currentUserToken) return;
        scenariosListDiv.innerHTML = '<h3>Your Scenarios</h3>';
        try {
            const response = await fetch("http://localhost:8000/users/me/scenarios/", {
                method: "GET",
                headers: { "Authorization": `Bearer ${currentUserToken}` }
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to fetch");

            const scenarios = await response.json();
            if (scenarios.length === 0) {
                scenariosListDiv.innerHTML += "<p>You haven't created any scenarios yet.</p>";
                return;
            }

            scenarios.forEach(scenario => {
                const scenarioDiv = document.createElement("div");
                scenarioDiv.className = "scenario-item";
                scenarioDiv.innerHTML = `
                    <div class="scenario-header" data-scenario-id="${scenario.id}">
                        <h4>${scenario.name}</h4>
                        <div class="edit-form">
                            <input type="text" class="edit-scenario-name-input" value="${scenario.name}">
                        </div>
                        <button class="edit-scenario-btn">Edit Name</button>
                        <button class="save-scenario-btn">Save</button>
                        <button class="cancel-scenario-edit-btn">Cancel</button>
                        <button class="delete-scenario-btn">Delete Scenario</button>
                    </div>
                    <p>${scenario.description || 'No description'}</p>
                    <ul>
                        ${scenario.questions.map(q => `
                            <li data-question-id="${q.id}">
                                <div class="qa-text">
                                    <span><b>Q:</b> ${q.question_text}</span><br>
                                    <span><b>A:</b> ${q.user_answer_text}</span>
                                </div>
                                <div class="edit-form">
                                    <input type="text" class="edit-question-input" value="${q.question_text}">
                                    <input type="text" class="edit-answer-input" value="${q.user_answer_text}">
                                </div>
                                <button class="edit-question-btn">Edit</button>
                                <button class="save-question-btn">Save</button>
                                <button class="cancel-edit-btn">Cancel</button>
                                <button class="delete-question-btn">Delete Q</button>
                            </li>`).join('')}
                    </ul>
                    <div class="add-question-form">
                        <input type="text" placeholder="Question" class="scenario-question-text">
                        <input type="text" placeholder="Your Answer" class="scenario-answer-text">
                        <button class="add-question-btn" data-scenario-id="${scenario.id}">Add Question</button>
                    </div>`;
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
        if (!scenarioName.trim()) {
            alert("Please enter a scenario name.");
            return;
        }
        try {
            const response = await fetch("http://localhost:8000/users/me/scenarios/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentUserToken}`},
                body: JSON.stringify({ name: scenarioName, description: "" })
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to create scenario");
            scenarioNameInput.value = "";
            fetchAndDisplayScenarios();
        } catch (error) {
            console.error("Error creating scenario:", error);
            alert(error.message);
        }
    }

    function toggleScenarioEditMode(event) {
        const headerDiv = event.target.closest('.scenario-header');
        if (headerDiv) {
            headerDiv.classList.toggle('editing');
        }
    }

    async function updateScenario(event) {
        const headerDiv = event.target.closest('.scenario-header');
        const scenarioId = headerDiv.dataset.scenarioId;
        const newName = headerDiv.querySelector('.edit-scenario-name-input').value;
        if (!newName.trim()) {
            alert("Scenario name cannot be empty.");
            return;
        }
        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${scenarioId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentUserToken}` },
                body: JSON.stringify({ name: newName })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update scenario.');
            fetchAndDisplayScenarios();
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
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to delete scenario.');
            fetchAndDisplayScenarios();
        } catch (error) {
            console.error('Error deleting scenario:', error);
            alert(error.message);
        }
    }

    // --- Question Management ---
    async function addQuestionToScenario(event) {
        const button = event.target;
        const scenarioId = button.dataset.scenarioId;
        const form = button.closest('.add-question-form');
        const questionText = form.querySelector('.scenario-question-text').value;
        const userAnswerText = form.querySelector('.scenario-answer-text').value;

        if (!questionText.trim() || !userAnswerText.trim()) {
            alert("Please fill in both the question and answer.");
            return;
        }
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
        const questionLi = event.target.closest('li');
        if (questionLi) {
            questionLi.classList.toggle('editing');
        }
    }

    async function updateQuestion(event) {
        const questionLi = event.target.closest('li');
        const questionId = questionLi.dataset.questionId;
        const newQuestionText = questionLi.querySelector('.edit-question-input').value;
        const newAnswerText = questionLi.querySelector('.edit-answer-input').value;

        try {
            const response = await fetch(`http://localhost:8000/users/me/questions/${questionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentUserToken}`},
                body: JSON.stringify({ question_text: newQuestionText, user_answer_text: newAnswerText })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update question.');
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
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to delete question.');
            fetchAndDisplayScenarios();
        } catch (error) {
            console.error('Error deleting question:', error);
            alert(error.message);
        }
    }

    // --- Preference Management ---
    async function fetchAndDisplayPreferences() {
        if (!currentUserToken) return;
        const preferencesListDiv = document.getElementById('preferences-list');
        try {
            const response = await fetch("http://localhost:8000/users/me/preferences/", {
                headers: { 'Authorization': `Bearer ${currentUserToken}` }
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Failed to fetch preferences");
            const preferences = await response.json();
            preferencesListDiv.innerHTML = '';
            const ul = document.createElement('ul');
            if (preferences.length > 0) {
                preferences.forEach(pref => {
                    const li = document.createElement('li');
                    li.dataset.preferenceId = pref.id;
                    li.innerHTML = `
                        <span class="preference-text"><strong>${pref.category}:</strong> ${pref.preference_text}</span>
                        <div class="edit-form">
                            <input type="text" class="edit-preference-key-input" value="${pref.category}">
                            <input type="text" class="edit-preference-value-input" value="${pref.preference_text}">
                        </div>
                        <button class="edit-preference-btn">Edit</button>
                        <button class="save-preference-btn">Save</button>
                        <button class="cancel-preference-edit-btn">Cancel</button>
                        <button class="delete-preference-btn">Delete</button>
                    `;
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
        const keyInput = document.getElementById('preference-key');
        const valueInput = document.getElementById('preference-value');
        const key = keyInput.value.trim();
        const value = valueInput.value.trim();
        if (!key || !value) {
            alert("Please provide both a key and a value for the preference.");
            return;
        }
        try {
            const response = await fetch("http://localhost:8000/users/me/preferences/", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentUserToken}`},
                body: JSON.stringify({ category: key, preference_text: value })
            });
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.detail?.[0]?.msg || errorData.detail || "Failed to add preference";
                throw new Error(errorMessage);
            }
            keyInput.value = '';
            valueInput.value = '';
            fetchAndDisplayPreferences();
        } catch (error) {
            console.error("Error adding preference:", error);
            alert(error.message);
        }
    }

    function togglePreferenceEditMode(event) {
        const preferenceLi = event.target.closest('li');
        if (preferenceLi) {
            preferenceLi.classList.toggle('editing');
        }
    }

    async function updatePreference(event) {
        const preferenceLi = event.target.closest('li');
        const preferenceId = preferenceLi.dataset.preferenceId;
        const newKey = preferenceLi.querySelector('.edit-preference-key-input').value;
        const newValue = preferenceLi.querySelector('.edit-preference-value-input').value;

        try {
            const response = await fetch(`http://localhost:8000/users/me/preferences/${preferenceId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentUserToken}` },
                body: JSON.stringify({ category: newKey, preference_text: newValue })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update preference.');
            fetchAndDisplayPreferences();
        } catch (error) {
            console.error('Error updating preference:', error);
            alert(error.message);
        }
    }

    async function deletePreference(event) {
        const preferenceId = event.target.dataset.preferenceId;
        if (!confirm("Are you sure you want to delete this preference?")) return;
        try {
            const response = await fetch(`http://localhost:8000/users/me/preferences/${preferenceId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${currentUserToken}` }
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Failed to delete preference.');
            fetchAndDisplayPreferences();
        } catch (error) {
            console.error('Error deleting preference:', error);
            alert(error.message);
        }
    }

    // --- Transcription Logic ---
    startBtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            startBtn.textContent = "Start Transcription";
        } else {
            if (!currentUserToken) {
                alert("You must be logged in to start transcription.");
                return;
            }
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    setupWebSocket(currentUserToken);
                    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0 && socket && socket.readyState === WebSocket.OPEN) {
                            socket.send(event.data);
                        }
                    };
                    mediaRecorder.start(1000);
                    startBtn.textContent = "Stop Transcription";
                    transcriptionDisplay.innerHTML = "";
                    suggestionsContainer.innerHTML = "";
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
                startBtn.textContent = "Start Transcription";
            }
        };
        socket.onerror = (error) => console.error("WebSocket error:", error);
        socket.onmessage = (event) => {
            const message = event.data;
            const [prefix, content] = message.split(/:(.*)/s);
            if (prefix === "suggestions") {
                const suggestions = JSON.parse(content);
                suggestionsContainer.innerHTML = "";
                suggestions.forEach(suggestion => {
                    const button = document.createElement("button");
                    button.textContent = suggestion;
                    suggestionsContainer.appendChild(button);
                });
            } else {
                let p = transcriptionDisplay.querySelector(`p[data-final='false']`);
                if (!p) {
                    p = document.createElement('p');
                    p.dataset.final = 'false';
                    p.style.color = '#888';
                    transcriptionDisplay.appendChild(p);
                }
                p.textContent = content;
                if (prefix === "final") {
                    p.dataset.final = 'true';
                    p.style.color = '#000';
                }
            }
        };
    }
});