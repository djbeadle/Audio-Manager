function showAudioPlayer(filename) {
    document.getElementById(filename).classList.toggle("audio-player");
}

function changeTrack(filename) {
    if (`https://audio-manager.s3.amazonaws.com/${filename}` !== document.getElementById("static-audio-player").src) {
        document.getElementById("static-audio-player").src=`https://audio-manager.s3.amazonaws.com/${filename}`;
    }

    let player = document.getElementById("static-audio-player");

    if (player.paused) {
        player.play();
    } else {
        player.pause();
    }
}