document.addEventListener("DOMContentLoaded", () => {
    // Get references to all UI elements, including the new container
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const signUpBtn = document.getElementById("signup-btn");
    const logInBtn = document.getElementById("login-btn");
    const logOutBtn = document.getElementById("logout-btn");
    const userStatus = document.getElementById("user-status");

    const authContainer = document.getElementById("auth-container");
    const userInfoContainer = document.getElementById("user-info-container");
    const transcriptionContainer = document.getElementById("transcription-container");

    const startBtn = document.getElementById("start-btn");
    const statusDisplay = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");
    const suggestionsContainer = document.getElementById("suggestions-container");

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
                transcriptionContainer.style.display = "block";
            });
        } else {
            // User is signed out, update UI accordingly
            currentUserToken = null;

            // Show login form, hide user info and transcription sections
            authContainer.style.display = "block";
            userInfoContainer.style.display = "none";
            transcriptionContainer.style.display = "none";
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