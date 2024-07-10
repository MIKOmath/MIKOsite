function validateDifficulty() {
    var minDifficulty = parseInt(document.getElementById("difficulty_min").value);
    var maxDifficulty = parseInt(document.getElementById("difficulty_max").value);

    // Check if max difficulty is not lower than min difficulty
    if (maxDifficulty < minDifficulty) {
        alert("Maximum difficulty cannot be lower than minimum difficulty.");
        return false; // Prevent form submission
    }
    return true; // Allow form submission
}

// Event listener to validate difficulty before form submission
document.getElementById("filter-form").addEventListener("submit", function(event) {
    if (!validateDifficulty()) {
        event.preventDefault(); // Prevent form submission if difficulty is invalid
    }
});

function updateDifficultyDisplay(inputId, displayId) {
    var input = document.getElementById(inputId);
    var display = document.getElementById(displayId);
    display.textContent = input.value;
}

// Event listeners to update difficulty displays
document.getElementById("difficulty_min").addEventListener("input", function() {
    updateDifficultyDisplay("difficulty_min", "difficulty_min_display");
});

document.getElementById("difficulty_max").addEventListener("input", function() {
    updateDifficultyDisplay("difficulty_max", "difficulty_max_display");
});

document.addEventListener('DOMContentLoaded', function() {
    const difficultyButtons = document.querySelectorAll('.difficulty-btn');
    const difficultyInput = document.getElementById('difficulty');

    difficultyButtons.forEach(button => {
        button.addEventListener('click', function() {
            difficultyButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            console.log("dasdasad")
            difficultyInput.value = this.dataset.value;
        });
    });
});