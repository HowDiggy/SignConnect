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

    // --- Firebase and State Variables
    const { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged, signOut } = window.firebaseAuth;
    const auth = getAuth(window.firebaseApp);

    let socket;
    let mediaRecorder;
    let currentUserToken = null;

    // --- Authentication Logic ---

    onAuthStateChanged(auth, user => {
        if (user) {
            // User is signed in, update UI accordingly
            user.getIdToken().then(token => {
                currentUserToken = token;
                userStatus.textContent = `Logged in as ${user.email}`;

                // Hide login form, show user info and transcription sections
                authContainer.style.display = "none";
                userInfoContainer.style.display = "block";
                transcriptionContainer.style.display = "block";    // Show transcription view by default
                managementContainer.style.display = "none";
            });
        } else {
            // User is signed out, update UI accordingly
            currentUserToken = null;

            // Show login form, hide user info and transcription sections
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
            .then(userCredential => {
                console.log("Signed up successfully:", userCredential.user);
            })
            .catch(error => {
                console.error("Sign up error:", error);
                alert(error.message);
            });
    });

    logInBtn.addEventListener("click", () => {
        const email = emailInput.value;
        const password = passwordInput.value;
        signInWithEmailAndPassword(auth, email, password)
            .then(userCredential => {
                console.log("Logged in successfully:", userCredential.user);
            })
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
            toggleViewBtn.textContent = "Manage Scenarios";
        } else {
            managementContainer.style.display = "block";
            transcriptionContainer.style.display = "none";
            toggleViewBtn.textContent = "Back to Transcription";
            // Fetch and display scenarios when switching to this view
            fetchAndDisplayScenarios();
        }
    });

    // --- Scenario Management Logic ---

async function fetchAndDisplayScenarios() {
    if (!currentUserToken) return;

    try {
        // This URL MUST match the path in your router file
        const response = await fetch("http://localhost:8000/users/me/scenarios/", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${currentUserToken}`
            }
        });

        if (!response.ok) {
            // This will now throw the error because of the 404
            throw new Error("Failed to fetch scenarios. Check the URL.");
        }

        const scenarios = await response.json();
        scenariosListDiv.innerHTML = "<h3>Your Scenarios</h3>";

        if (scenarios.length === 0) {
            scenariosListDiv.innerHTML += "<p>You haven't created any scenarios yet.</p>";
            return;
        }

        scenarios.forEach(scenario => {
            const scenarioDiv = document.createElement("div");
            scenarioDiv.className = "scenario-item";
            scenarioDiv.innerHTML = `
                <div class="scenario-header">
                    <h4>${scenario.name}</h4>
                    <button class="delete-scenario-btn" data-scenario-id="${scenario.id}">Delete</button>
                </div>
                <p>${scenario.description || 'No Description'}</p>
                <ul>
                    ${scenario.questions.map(q => `<li><b>Q:</b> ${q.question_text} <br> <b>A:</b> ${q.user_answer_text}</li>`).join('')}
                </ul>
                <div class="add-question-form">
                    <input type="text" placeholder="Question" class="scenario-question-text">
                    <input type="text" placeholder="Your Answer" class="scenario-answer-text">
                    <button class="add-question-btn" data-scenario-id="${scenario.id}">Add Question</button>
                </div>
            `;
            scenariosListDiv.appendChild(scenarioDiv);
        });

        document.querySelectorAll('.delete-scenario-btn').forEach(button => {
            button.addEventListener('click', deleteScenario);
        })

        document.querySelectorAll('.add-question-btn').forEach(button => {
            button.addEventListener('click', addQuestionToScenario);
        });

    } catch (error) {
        console.error("Error fetching scenarios:", error);
        scenariosListDiv.innerHTML += `<p style="color:red;">Error: ${error.message}</p>`;
    }
}

        async function deleteScenario(event) {
        const scenarioId = event.target.dataset.scenarioId;

        // Confirm with the user before deleting
        if (!confirm("Are you sure you want to delete this scenario and all its questions?")) {
            return;
        }

        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${scenarioId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${currentUserToken}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete scenario.');
            }

            // Refresh the list of scenarios to show the change
            fetchAndDisplayScenarios();

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

        if (!questionText.trim() || !userAnswerText.trim() || !currentUserToken) {
            alert("Please fill in both the question and answer.");
            return;
        }

        try {
            const response = await fetch(`http://localhost:8000/users/me/scenarios/${scenarioId}/questions/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentUserToken}`
                },
                body: JSON.stringify({ question_text: questionText, user_answer_text: userAnswerText })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to add question");
            }

            fetchAndDisplayScenarios(); // Refresh the entire list to show the new question

        } catch (error) {
            console.error("Error adding question:", error);
            alert(error.message);
        }
    }

    addScenarioBtn.addEventListener("click", async (event) => {
        event.preventDefault(); // Prevent from submission
        const scenarioName = scenarioNameInput.value;
        if (!scenarioName.trim() || !currentUserToken) {
            alert("Please enter a scenario name or log in.");
            return;
        }

        try {
            const response = await fetch("http://localhost:8000/users/me/scenarios/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentUserToken}`
                },
                body: JSON.stringify({ name: scenarioName, description: "" })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to create scenario");
            }

            scenarioNameInput.value = ""; // Clear input
            fetchAndDisplayScenarios(); // Refresh the list
            alert("Scenario created successfully!");

        } catch (error) {
            console.error("Error creating scenario:", error);
            alert(error.message);
        }
    });

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