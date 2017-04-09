var MOTDPlayerClass = function (b64InitString) {
    var MOTDPlayer = this;

    var motdVar = JSON.parse(atob(b64InitString));

    var ajaxPostJson = function (url, data, successCallback, errorCallback) {
        var xhr = new XMLHttpRequest();

        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4)
                if (xhr.status == 200)
                    successCallback(JSON.parse(xhr.responseText));
                else
                    errorCallback();
        };

        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.send(JSON.stringify(data, null, '\t'));
    };

    var nodeLoadingScreen;

    this.post = function (data, successCallback, errorCallback) {
        ajaxPostJson("/" + motdVar.serverId + "/" + motdVar.pluginId + "/" + motdVar.pageId + "/" + motdVar.steamid + "/" + motdVar.authMethod + "/" + motdVar.authToken + "/" + motdVar.sessionId + "/", {
                action: "custom-data",
                custom_data: data
            }, function (response) {
                if (response['status'] == "OK") {
                    motdVar.authMethod = 1;
                    motdVar.authToken = response['web_auth_token'];

                    if (nodeLoadingScreen) {
                        nodeLoadingScreen.parentNode.removeChild(nodeLoadingScreen);
                        nodeLoadingScreen = null;
                    }

                    successCallback(response['custom_data']);
                }
                else if (errorCallback)
                    errorCallback(response['status'] + " " + response['error_id']);
            }, function () {
                if (errorCallback)
                    errorCallback("JS_AJAX_FAILURE");
            }
        );
        if (!nodeLoadingScreen) {
            nodeLoadingScreen = document.body.appendChild(document.createElement('div'));
            nodeLoadingScreen.classList.add('motdplayer-ajax-loading-screen');
        }
    };

    var ws;
    this.openWSConnection = function (openCallback, messageCallback, closeCallback, errorCallback) {
        if (ws)
            return;

        ws = new WebSocket("ws://" + location.host + "/ws/" + motdVar.serverId + "/" + motdVar.pluginId + "/" + motdVar.pageId + "/" + motdVar.steamid + "/" + motdVar.authMethod + "/" + motdVar.authToken + "/" + motdVar.sessionId + "/");
        ws.onopen = function(e) {
            if (openCallback)
                openCallback();
        };
        ws.onclose = function(e) {
            MOTDPlayer.closeWSConnection();
            if (closeCallback)
                closeCallback();
        };
        ws.onerror = function(err) {
            if (errorCallback)
                errorCallback("JS_WS_FAILURE");
        };
        ws.onmessage = function(e) {
            var response = JSON.parse(e.data);
            if (response['status'] == "OK") {
                motdVar.authMethod = 1;
                motdVar.authToken = response['web_auth_token'];
            }
            else if (response['status'] = "CUSTOM_DATA")
                messageCallback(response['custom_data']);
            else {
                alert("Error!");
                if (errorCallback)
                    errorCallback(response['status'] + " " + response['error_id']);
            }
        };
    };

    this.closeWSConnection = function () {
        if (!ws)
            return;

        ws.onclose = undefined;
        ws.close();

        ws = undefined;
    };

    this.sendWSData = function (obj) {
        if (!ws)
            return;

        ws.send(JSON.stringify({
            action: "custom-data",
            custom_data: obj
        }));
    };

    this.isWSSupported = function () {
        return window.WebSocket ? true : false;
    };

    this.switchPage = function (newPageId, successCallback, errorCallback) {
        ajaxPostJson("/switch/" + motdVar.serverId + "/" + motdVar.pluginId + "/" + newPageId + "/" + motdVar.pageId + "/" + motdVar.steamid + "/" + motdVar.authMethod + "/" + motdVar.authToken + "/" + motdVar.sessionId + "/",
            {
                action: "switch"
            }, function (response) {
                if (response['status'] == "OK") {
                    motdVar.authMethod = 1;
                    motdVar.authToken = response['web_auth_token'];
                    motdVar.pageId = newPageId;

                    if (nodeLoadingScreen) {
                        nodeLoadingScreen.parentNode.removeChild(nodeLoadingScreen);
                        nodeLoadingScreen = null;
                    }
                }
                else
                    if (errorCallback)
                        errorCallback(response['status'] + " " + response['error_id']);
            }, function () {
                if (errorCallback)
                    errorCallback("JS_AJAX_FAILURE");
            }
        );
        if (!nodeLoadingScreen) {
            nodeLoadingScreen = document.body.appendChild(document.createElement('div'));
            nodeLoadingScreen.classList.add('motdplayer-ajax-loading-screen');
        }
    };
};
