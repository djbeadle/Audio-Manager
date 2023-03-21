function showAudioPlayer(filename) {
    document.getElementById(filename).classList.toggle("audio-player");
}

function changeTrack(filename, wavesurfer) {
    document.querySelector('[data-action="play"]').innerText = "Loading...";

    wavesurfer.pause();
    wavesurfer.load(`https://audio-manager.s3.amazonaws.com/${filename}`);
}

