const playButton = document.getElementById('play-button');
const backgroundMusic = document.getElementById('background-music');
let isPlaying = false;

playButton.addEventListener('click', () => {
    if (isPlaying) {
        backgroundMusic.pause();
        playButton.innerHTML = '&#9658;'; // Play icon
    } else {
        backgroundMusic.play();
        playButton.innerHTML = '&#10074;&#10074;'; // Pause icon
    }
    isPlaying = !isPlaying;
});