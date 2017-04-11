var MOTDPlayerClass = function (b64InitString) {
    var MOTDPlayer = this;

    var authVar = JSON.parse(atob(b64InitString));

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
        ajaxPostJson("/" + authVar.serverId + "/" + authVar.pluginId + "/" + authVar.pageId + "/" + authVar.steamid + "/" + authVar.authMethod + "/" + authVar.authToken + "/" + authVar.sessionId + "/", {
                action: "custom-data",
                custom_data: data
            }, function (response) {
                if (response['status'] == "OK") {
                    authVar.authMethod = 1;
                    authVar.authToken = response['web_auth_token'];

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
    this.openWSConnection = function (successCallback, messageCallback, closeCallback, errorCallback) {
        if (ws) {
            if (errorCallback)
                errorCallback("WS_ALREADY_OPENED");
            return;
        }

        if (!MOTDPlayer.isWSSupported()) {
            if (errorCallback)
                errorCallback("WS_NO_BROWSER_SUPPORT");
            return;
        }

        ws = new WebSocket("ws://" + location.host + "/ws/" + authVar.serverId + "/" + authVar.pluginId + "/" + authVar.pageId + "/" + authVar.steamid + "/" + authVar.authMethod + "/" + authVar.authToken + "/" + authVar.sessionId + "/");
        ws.onclose = function(e) {
            MOTDPlayer.closeWSConnection();
            if (closeCallback)
                closeCallback();
        };
        ws.onerror = function(err) {
            if (errorCallback)
                errorCallback("WS_ONERROR_EVENT");
        };
        ws.onmessage = function(e) {
            var response = JSON.parse(e.data);
            if (response['status'] == "OK") {
                authVar.authMethod = 1;
                authVar.authToken = response['web_auth_token'];

                if (successCallback)
                    successCallback();
            }
            else if (response['status'] == "CUSTOM_DATA") {
                console.log(response);
                messageCallback(response['custom_data']);
            }
            else if (errorCallback)
                errorCallback(response['status'] + " " + response['error_id']);
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
        ajaxPostJson("/switch/" + authVar.serverId + "/" + authVar.pluginId + "/" + newPageId + "/" + authVar.pageId + "/" + authVar.steamid + "/" + authVar.authMethod + "/" + authVar.authToken + "/" + authVar.sessionId + "/",
            {
                action: "switch"
            }, function (response) {
                if (response['status'] == "OK") {
                    authVar.authMethod = 1;
                    authVar.authToken = response['web_auth_token'];
                    authVar.pageId = newPageId;

                    if (nodeLoadingScreen) {
                        nodeLoadingScreen.parentNode.removeChild(nodeLoadingScreen);
                        nodeLoadingScreen = null;
                    }

                    if (successCallback)
                        successCallback();
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

    this.reloadPage = function () {
        location.href = "/" + authVar.serverId + "/" + authVar.pluginId + "/" + authVar.pageId + "/" + authVar.steamid + "/" + authVar.authMethod + "/" + authVar.authToken + "/" + authVar.sessionId + "/";
    };

    this.getPlayerSteamID64 = function () {
        return authVar.steamid;
    };

    this.getPageId = function () {
        return authVar.pageId;
    };
};
