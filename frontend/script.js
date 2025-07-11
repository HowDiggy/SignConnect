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
    const scenariosListDiv = document.getElementById("suggestions-container");

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
        // NOTE: In the future, this will fetch scenarios. For now, it's a placeholder.
        scenariosListDiv.innerHTML = "<p>Scenario display coming soon.</p>";
    }

    addScenarioBtn.addEventListener("click", async () => {
        const scenarioName = scenarioNameInput.value;
        if (!scenarioName.trim() || !currentUserToken) {
            alert("Please enter a scenario name or log in.");
            return;
        }

        try {
            const response = await fetch("/scenarios/", {
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