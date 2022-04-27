function showAudioPlayer(filename) {
    document.getElementById(filename).classList.toggle("audio-player");
}

function changeTrack(filename, wavesurfer) {
    wavesurfer.load(`https://audio-manager.s3.amazonaws.com/${filename}`);

    let player = document.getElementById("static-audio-player");

    wavesurfer.play();

}