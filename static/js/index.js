// Constant loop that gets the statuses of the programs.
// Modifies the statuses of the programs in the DOM.
let program_statuses = {};
setInterval(function () {
    fetch('/status', {
        method: 'GET',
    })
        .then(response => response.json())
        .then(data => {
            program_statuses = data;
            document.getElementById('twitch-bot-status').innerText = "Status: " + program_statuses['Twitch Bot']['state'];
            document.getElementById('tony-meme-generator-status').innerText = "Status: " + program_statuses['Tony Meme Generator']['state'];
        });
}, 1000);

// Buttons to interact with the programs.
// 1. Select the button element
const btn_twitch_start = document.getElementById('twitch-bot-start');
const btn_twitch_stop = document.getElementById('twitch-bot-stop');
const btn_twitch_restart = document.getElementById('twitch-bot-restart');
const btn_tony_meme_generator_start = document.getElementById('tony-meme-generator-start');
const btn_tony_meme_generator_stop = document.getElementById('tony-meme-generator-stop');
const btn_tony_meme_generator_restart = document.getElementById('tony-meme-generator-restart');

btn_twitch_start.onclick = function () {
    // Send POST request to /twitch-bot/start
    fetch('/twitch-bot/start', {
        method: 'POST',
    });
}
btn_twitch_stop.onclick = function () {
    // Send POST request to /twitch-bot/stop
    fetch('/twitch-bot/stop', {
        method: 'POST',
    });
}
btn_twitch_restart.onclick = function () {
    // Send POST request to /twitch-bot/restart
    fetch('/twitch-bot/restart', {
        method: 'POST',
    });
}
btn_tony_meme_generator_start.onclick = function () {
    // Send POST request to /tony-meme-generator/start
    fetch('/tony-meme-generator/start', {
        method: 'POST',
    });
}
btn_tony_meme_generator_stop.onclick = function () {
    // Send POST request to /tony-meme-generator/stop
    fetch('/tony-meme-generator/stop', {
        method: 'POST',
    });
}
btn_tony_meme_generator_restart.onclick = function () {
    // Send POST request to /tony-meme-generator/restart
    fetch('/tony-meme-generator/restart', {
        method: 'POST',
    });
}