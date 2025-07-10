document.addEventListener("DOMContentLoaded", () => {
    // Get references to all the new UI elements
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const signUpBtn = document.getElementById("signup-btn");
    const logInBtn = document.getElementById("login-btn");
    const logOutBtn = document.getElementById("logout-btn");
    const userStatus = document.getElementById("user-status");

    const authContainer = document.getElementById("auth-container");
    const transcriptionContainer = document.getElementById("transcription-container");

    const startBtn = document.getElementById("start-btn");
    const statusDisplay = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");
    const suggestionsContainer = document.getElementById("suggestions-container");

    // Get Firebase auth functions from the window object
    const { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged, signOut } = window.firebaseAuth;
    const auth = getAuth(window.firebaseApp);

    let socket;
    let mediaRecorder;
    let currentUserToken = null;

    // --- Authentication Logic ---

    // Listener for authentication state changes
    onAuthStateChanged(auth, user => {
        if (user) {
            // User is signed in
            user.getIdToken().then(token => {
                currentUserToken = token;
                userStatus.textContent = `Logged in as ${user.email}`;
                authContainer.style.display = "none";
                transcriptionContainer.style.display = "block";
                logOutBtn.style.display = "inline";
            });
        } else {
            // User is signed out
            currentUserToken = null;
            userStatus.textContent = "Logged Out";
            authContainer.style.display = "block";
            transcriptionContainer.style.display = "none";
            logOutBtn.style.display = "none";
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
        // Append the token as a query parameter
        const wsUrl = `ws://localhost:8000/ws?token=${token}`;
        socket = new WebSocket(ws_url);

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
                // Handle final and interim text
                let p = transcriptionDisplay.querySelector(`[data-final='false']`) || document.createElement('p');
                p.textContent = content;

                if (prefix === "final") {
                    p.dataset.final = 'true';
                } else {
                    p.dataset.final = 'false';
                    p.style.color = '#888';
                }
                transcriptionDisplay.appendChild(p);
            }
        };
    }
});