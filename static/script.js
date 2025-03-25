document.addEventListener("DOMContentLoaded", function () {
    const distributionSelect = document.getElementById("distributionSelect");
    const generateButton = document.querySelector("button");
    const pdfImage = document.getElementById("pdfImage");
    const speechButton = document.getElementById("speechBtn");
    const statusMessage = document.getElementById("statusMessage");

    generateButton.addEventListener("click", function () {
        generatePDF(distributionSelect.value);
    });

    speechButton.addEventListener("click", function () {
        startSpeechRecognition();
    });

    function generatePDF(distribution) {
        fetch("/get_pdf", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ distribution: distribution })
        })
        .then(response => response.json())
        .then(data => {
            if (data.image) {
                pdfImage.src = "data:image/png;base64," + data.image;
            } else {
                alert("Invalid distribution selected.");
            }
        })
        .catch(error => console.error("Error:", error));
    }

    function startSpeechRecognition() {
        window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!window.SpeechRecognition) {
            alert("Speech Recognition is not supported in this browser. Please use Google Chrome.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.start();

        recognition.onstart = function () {
            statusMessage.textContent = "Listening...";
        };

        recognition.onspeechend = function () {
            recognition.stop();
            statusMessage.textContent = "Processing...";
        };

        recognition.onresult = function (event) {
            const speechResult = event.results[0][0].transcript.toLowerCase();
            statusMessage.textContent = "Recognized: " + speechResult;

            // Check if the spoken word matches any known distribution
            const validDistributions = ["uniform", "rayleigh", "binomial", "poisson", "laplacian"];
            if (validDistributions.includes(speechResult)) {
                distributionSelect.value = speechResult;
                generatePDF(speechResult);
            } else {
                alert("Could not recognize a valid distribution. Try saying 'Uniform', 'Rayleigh', 'Binomial', 'Poisson', or 'Laplacian'.");
            }
        };

        recognition.onerror = function (event) {
            statusMessage.textContent = "Error: " + event.error;
            alert("Speech recognition error: " + event.error);
        };
    }
});
