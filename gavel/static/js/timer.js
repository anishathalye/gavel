const button = document.getElementById('startButton');
const timerDisplay = document.getElementById('timer');
const minutesRange = document.getElementById('minutesRange');
const minutesLabel = document.getElementById('minutesLabel');

let ping;
let intervalId;
let totalSeconds = 0;

window.addEventListener('DOMContentLoaded', () => {
  ping = new Audio(pingSoundPath); // defined in HTML
});

minutesRange.addEventListener('input', () => {
  minutesLabel.textContent = `${minutesRange.value} min`;
});

button.addEventListener('click', () => {
    if (intervalId) return;
    const selectedMinutes = parseInt(minutesRange.value);
    totalSeconds = selectedMinutes * 60;
    
    updateDisplay();

    intervalId = setInterval(() => {
        totalSeconds--;
        updateDisplay();
    
        if (totalSeconds <= 0) {
            clearInterval(intervalId);
            intervalId = null;
            ping.play().catch(err => console.log("Audio play blocked:", err));
            //alert("Time's up"); this is in case everything goes wrong :(

            timerDisplay.textContent = "0:00";
            button.disabled = false;
        }
    }, 1000);

    button.disabled = true;
});

function updateDisplay() {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
}