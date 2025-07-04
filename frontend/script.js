document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("start-btn");
    const statusDisplay = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");

    let socket;
    let mediaRecorder;
    let interimSpan = null; // To hold the element for interim results

    startBtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            // The socket will be closed by the server or on its own
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
            console.log("WebSocket connection opened.");
            statusDisplay.textContent = "Connected";
        };

        socket.onmessage = (event) => {
            const message = event.data;

            if (message.startsWith("interim:")) {
                // If it's an interim result, update the temporary span
                if (!interimSpan) {
                    // Create the span if it doesn't exist
                    interimSpan = document.createElement('span');
                    interimSpan.style.color = '#888'; // Make it grey
                    transcriptionDisplay.appendChild(interimSpan);
                }
                interimSpan.textContent = " " + message.substring(8); // Get text after "interim:"
            } else if (message.startsWith("final:")) {
                // If it's a final result, make the interim span permanent and clear it
                if (interimSpan) {
                    interimSpan.remove();
                    interimSpan = null;
                }
                const finalPara = document.createElement('p');
                finalPara.textContent = message.substring(7); // Get text after "final:"
                transcriptionDisplay.appendChild(finalPara);
            }
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            statusDisplay.textContent = "Error";
        };

        socket.onclose = () => {
            console.log("WebSocket connection closed.");
            statusDisplay.textContent = "Disconnected";
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
            }
        };
    }
});