document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("start-btn");
    const statusDisplay = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");
    const suggestionsContainer = document.getElementById("suggestions-container"); // Get the new container

    let socket;
    let mediaRecorder;
    let interimSpan = null;

    startBtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            startBtn.textContent = "Start Transcription";
        } else {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    setupWebSocket();
                    mediaRecorder = new MediaRecorder(stream, {
                        mimeType: 'audio/webm;codecs=opus',
                    });

                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                            socket.send(event.data);
                        }
                    };

                    mediaRecorder.start(1000);

                    startBtn.textContent = "Stop Transcription";
                    transcriptionDisplay.innerHTML = "";
                    suggestionsContainer.innerHTML = ""; // Clear old suggestions
                })
                .catch(error => {
                    console.error("Error accessing microphone:", error);
                    statusDisplay.textContent = "Error: Microphone access denied.";
                });
        }
    });

    function setupWebSocket() {
        socket = new WebSocket("ws://localhost:8000/ws");

        socket.onopen = () => {
            statusDisplay.textContent = "Connected";
        };

        socket.onmessage = (event) => {
            const message = event.data;
            const [prefix, content] = message.split(/:(.*)/s);

            if (prefix === "interim") {
                if (!interimSpan) {
                    interimSpan = document.createElement('span');
                    interimSpan.style.color = '#888';
                    transcriptionDisplay.appendChild(interimSpan);
                }
                interimSpan.textContent = " " + content;
            } else if (prefix === "final") {
                if (interimSpan) {
                    interimSpan.remove();
                    interimSpan = null;
                }
                const finalPara = document.createElement('p');
                finalPara.textContent = content;
                transcriptionDisplay.appendChild(finalPara);
            } else if (prefix === "suggestions") {
                // NEW: Handle suggestions
                const suggestions = JSON.parse(content);
                suggestionsContainer.innerHTML = ""; // Clear previous suggestions
                suggestions.forEach(suggestion => {
                    const button = document.createElement("button");
                    button.textContent = suggestion;
                    button.onclick = () => {
                        console.log(`Suggestion selected: "${suggestion}"`);
                        // In the future, this button would trigger text-to-speech
                    };
                    suggestionsContainer.appendChild(button);
                });
            }
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            statusDisplay.textContent = "Error";
        };

        socket.onclose = () => {
            statusDisplay.textContent = "Disconnected";
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
            }
        };
    }
});