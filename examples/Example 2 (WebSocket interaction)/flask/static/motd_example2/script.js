document.addEventListener("DOMContentLoaded", function (e) {
    var textarea = document.getElementById('events-log');
    var messageBox = document.getElementById('message-box');
    var sendButton = document.getElementById('send-button');

    if (MOTDPlayer.isWSSupported()) {
        textarea.value += "WebSockets are SUPPORTED\n";

        MOTDPlayer.openWSConnection(function () {
            textarea.value += "WebSocket connection established suffessfully!\n";
            sendButton.disabled = false;
        }, function (data) {
            textarea.value += data['name'] + " dies!\n";
        }, function () {
            textarea.value += "WebSocket connection closed!\n";
            sendButton.disabled = true;
        }, function (err) {
            textarea.value += "WebSocket error: " + err + "\n";
            sendButton.disabled = true;
        });

        sendButton.addEventListener('click', function (e) {
            if (!messageBox.value)
                return;

            MOTDPlayer.sendWSData({
                'action': "chat-message",
                'message': messageBox.value
            });

            messageBox.value = "";
        });
    }
    else {
        textarea.value += "WebSockets are NOT SUPPORTED\n";
    }
});
