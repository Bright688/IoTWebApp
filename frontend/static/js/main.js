// Function to handle the form submission for the assessment
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("assessment-form");
    const feedbackContainer = document.getElementById("feedback-container");

    // Function to display feedback for each question
    function showFeedback(questionId, userAnswer, correctAnswer) {
        const feedback = document.createElement("div");
        feedback.classList.add("mt-2", "text-sm");
        if (userAnswer === correctAnswer) {
            feedback.classList.add("text-green-600");
            feedback.innerText = "Correct!";
        } else {
            feedback.classList.add("text-red-600");
            feedback.innerText = "Incorrect. The correct answer is: " + correctAnswer;
        }
        document.getElementById(questionId).appendChild(feedback);
    }

    // Function to handle form submission
    form.addEventListener("submit", async function(e) {
        e.preventDefault();

        const formData = new FormData(form);
        const userAnswers = {};
        formData.forEach((value, key) => {
            userAnswers[key] = value;
        });

        try {
            // Send the answers to the backend for evaluation
            const response = await fetch("/submit-assessment", {
                method: "POST",
                body: JSON.stringify({ answers: userAnswers }),
                headers: {
                    "Content-Type": "application/json"
                }
            });

            const result = await response.json();

            // Display real-time feedback for each question
            Object.keys(userAnswers).forEach((questionId) => {
                const userAnswer = userAnswers[questionId];
                const correctAnswer = result.correct_answers[questionId];
                showFeedback(questionId, userAnswer, correctAnswer);
            });

            // Show the total score and other feedback
            const score = result.score;
            feedbackContainer.innerHTML = `
                <div class="text-xl font-semibold text-blue-600">
                    Your Total Score: ${score}/10
                </div>
                <div class="mt-4 text-gray-700">
                    ${score >= 8 ? "Great job!" : "Try to review the best practices."}
                </div>
            `;
        } catch (error) {
            console.error("Error submitting assessment:", error);
            feedbackContainer.innerHTML = `
                <div class="text-red-600">
                    Something went wrong. Please try again later.
                </div>
            `;
        }
    });
});

// Function to handle real-time font resizing (accessibility feature)
const fontSizeButtons = document.querySelectorAll(".font-size-btn");

fontSizeButtons.forEach((button) => {
    button.addEventListener("click", function() {
        const size = button.dataset.size;
        document.body.style.fontSize = size;
    });
});