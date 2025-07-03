// Wait for the HTML document to be fully loaded before running the script
document.addEventListener("DOMContentLoaded", () => {
    // Get references to the HTML elements we'll need to interact with
    const startBtn = document.getElementById("start-btn");
    const statusDisplay = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");

    let socket; // Variable to hold the WebSocket object

    // Add a click event listener to the "Start" button
    startBtn.addEventListener("click", () => {
        // If the socket is already open, do nothing
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log("WebSocket is already open.");
            return;
        }

        // Create a new WebSocket connection to our FastAPI server
        // Note: Use 'ws://' for http and 'wss://' for https
        socket = new WebSocket("ws://localhost:8000/ws");

        // --- WebSocket Event Handlers ---

        // This function runs when the connection is successfully opened
        socket.onopen = (event) => {
            console.log("WebSocket connection opened:", event);
            statusDisplay.textContent = "Connected";
            // Send a test message to the server once connected
            socket.send("Hello, Server!");
        };

        // This function runs when a message is received from the server
        socket.onmessage = (event) => {
            console.log("Message from server:", event.data);
            // Create a new paragraph element for the message and append it
            const newTranscription = document.createElement("p");
            newTranscription.textContent = event.data;
            transcriptionDisplay.appendChild(newTranscription);
        };

        // This function runs if there's an error with the connection
        socket.onerror = (event) => {
            console.error("WebSocket error observed:", event);
            statusDisplay.textContent = "Error";
        };

        // This function runs when the connection is closed
        socket.onclose = (event) => {
            console.log("WebSocket connection closed:", event);
            statusDisplay.textContent = "Disconnected";
        };
    });
});