let currentEmail;
let sessionId;
let questionStartTime;


function loadEmail() {
    fetch("/api/email/random")
        .then(response => response.json())
        .then(email => {
            currentEmail = email;
            questionStartTime = Date.now();

            document.getElementById("email").textContent =
                email.text || email.body;
        });
}

function checkAnswer(answer) {
    const correct = answer === currentEmail.label ? 1 : 0;
    const responseTime = (Date.now() - questionStartTime) / 1000; // response time in seconds
    fetch("/api/result", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            sessionId: sessionId,
            emailId: currentEmail.id,
            emailSource: currentEmail.source,
            actualLabel: currentEmail.label,
            userAnswer: answer,
            correct: correct,
            responseTime: responseTime
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log(data);

            if (correct) {
                alert("Correct!");
            } else {
                alert("Incorrect!");
            }

            loadEmail();
        });
}

document.getElementById("phishingButton").addEventListener("click", function () {
    checkAnswer(1);
});

document.getElementById("legitimateButton").addEventListener("click", function () {
    checkAnswer(0);
});

fetch("/api/session", {
    method: "POST"
})
    .then(response => response.json())
    .then(data => {
        sessionId = data.sessionId;
        console.log("Session started:", sessionId);

        loadEmail();
    });