MOTDPlayer v2
=============
Contents
--------
1. Contents
1. Introduction
1. Examples
1. Plugin API (Source.Python counterpart)
1. Web-application API (Flask counterpart)
1. JavaScript library


Introduction
------------

__MOTDPlayer__ is a software for Source-powered games that allows plugin creators to send interactive _Message of The Day_ screens to their players.

MOTDPlayer consists of:
* [Source.Python](http://sourcepython.com/) custom package
* Flask web-application
* JavaScript library

MOTDPlayer automatically authorizes the user behind the scenes, so your MoTD web-page will know which of your players exactly is viewing it. All auth details are secured with a SHA-512 hash, so it's impossible to view the page as another player.

MOTDPlayer provides an interface that lets the MoTD page send data to the game server and get something in return. Two types of such interaction is possible:

#### Default
The page sends data to the server and gets data back only once, during loading process. Consequent AJAX requests can broaden the possibilities of this approach.

#### WebSocket-powered (currently supported on [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) only)
This extends the previous approach: the page establishes a WebSocket-connection and is able to send the data to the game server without AJAX requests. What is more important is that the game server itself is now able to push data to such MoTD pages at any time.

One important thing to keep in mind is that you don't directly expose your game server to the public - all data transmissions are proxied (and filtered, if needed) by the Flask application that runs on the web-server.


Examples
--------
Examples of complete applications (Source.Python plugin + Flask MOTDPlayer application + static web files) can be found [here](https://github.com/KirillMysnik/SP-MOTDPlayer2/tree/master/examples).


Plugin API (Source.Python counterpart)
--------------------------------------
##### motdplayer.errors.SessionError
Enumeration of possible reasons of why the current page instance invalidates:
* __TAKEN_OVER__ - The page is shadowed by another page. In some games only one MoTD page can be shown at a time, and if you send multiple, you never know which one will make it to the player's screen. For this reason all pages are initialized, but when one actually displays, all others receive __TAKEN_OVER__ error.
* __PLAYER_DROP__ - Player to which this page instance was sent has disconnected.
* __UNKNOWN_PLAYER__ - Page is sent to a non-existing player. This is going to be changed in the future version. Instead of initializing the page and immediately sending __UNKNOWN_PLAYER__ to it, MOTDPlayer will avoid initializing the page at all and will raise an exception.
* __WS_TRANSMISSION_END__ - This can only be received by a WebSocket-instance of the Page and is sent by MOTDPlayer when a WebSocket communication ends.
```python
class SessionError(IntEnum):
    TAKEN_OVER = 0
    PLAYER_DROP = 1
    UNKNOWN_PLAYER = 2
    WS_TRANSMISSION_END = 3
```

##### motdplayer.Page
Main class that describes a page instance. For each page your plugin needs to provide, subclass this class. To send it to a player, use its `send` class method. When MOTDPlayer sends your page, your subclass will get instantiated.

_Class attributes (override them when subclassing):_
* __page_id__ - Your page ID. Should be unique in your plugin.
* __plugin_id__ - Your plugin ID. Should be unique in Source.Python namespace. The best choice is your main module basename.
* __ws_support__ - Whether or not this page should support WebSocket protocol.

_Methods:_

```python
def __init__(self, index, ws_instance):
```
Called when your page is instantiated. One instance of your page is created instantly when you send it, and `ws_instance` argument is `False`. Another one may be created if MoTD establishes WebSocket connection. In the latter case the instance will be initialized with `ws_instance` set to `True`.
The `index` argument is player's index.


```python
def on_error(self, error):
```
Called when page instance invalidates for some reason. See `motdplayer.errors.SessionError` for more details.


```python
def on_switch_requested(self, new_page_id):
```
Called when scripts in MoTD screen request so-called "page switch".
Due to how MOTDPlayer auth system works, one cannot simply replace Page ID in page url with another Page ID as it will break SHA-512 hash. To be able to perform AJAX-requests with another Page ID, scripts must first request a page switch.
`on_switch_requested` is called in this case. Its only argument, `new_page_id`, is the requested new Page ID. If your implementation of this method returns False, the switch will not be allowed. Default implementation always returns True.


```python
def on_data_received(self, data):
```
Called when the data is being sent from MoTD page to your plugin.
For a WebSocket-instance of the Page this can occur at any time.
For a regular instance this only occurs when MoTD is being loaded into player's screen.
The `data` argument is a Python dictionary.


```python
def send_data(self, data):
```
Call this to send data to the MoTD page. The `data` argument should be a Python dictionary you want to send to the MoTD page.
For a WebSocket-instance of the Page you can call this method at any time.
For a regular instance of the Page you can call this method only inside of `on_data_received` callback, and ONLY ONCE.


```python
def stop_ws_transmission(self):
```
Call this to manually abort WebSocket-communication. You can only call this method for WebSocket-instances of the Page.


```python
@classmethod
def send(cls, index):
```
Sends the page to a player with the specified `index`.


Web-application API (Flask counterpart)
---------------------------------------
##### motdplayer.WebRequestProcessor
This class stores attributes and callbacks used by MOTDPlayer to handle data transmission between your MoTD page and the game server.

_Methods:_

```python
def __init__(self, plugin_id, page_id):
```
When initializing a Web Request Processor, provide two arguments:
`plugin_id` - Plugin ID;
`page_id` - Page ID.
This should correspond to the class attributes on Page subclasses in your game server plugin.


```python
def register_regular_callback(self, callback):
```
Intended to be used as a decorator. Registers a callback you want to handle data transmission that occurs when the MoTD page is being loaded.
Your callback will receive only one argument - "data exchanging" function. You can call this function as many times as you want and pass a Python dictionary to it. Data exchanging function will every time return another Python dictionary - data sent back to you by the game server. Every time you can data exchanging function, the `on_data_received` callback is called on the Page instance in your plugin.
Your callback must return two values: the name of the template to render and a context (Python dictionary) to render that template with. Your context dictionary will be available in Jinja2 template as a `context` variable.
E.g. to access the `key` from the context dictionary your callback returns, you write this piece of code in your template:
```html
<h1>Here's a key from the context my callback returned: {{ context.key }}</h1>
```
Other words, your callback performs 2-way communication: it sends and receives the data to and from the game server.


```python
def register_ajax_callback(self, callback):
```
Intended to be used as a decorator. Registers a callback you want to handle data transmission that occurs when your script makes an AJAX call.
This time your callback will receive two arguments: data exchanging function and a dictionary. The dictionary is actually the data sent by AJAX call.
Your callback must return only one value: the dictionary to send back to your JavaScript-application that made an AJAX call.
For more information on data exchanging function, refer to the previous method (`register_regular_callback`).
Other words, your callback performs 2-way communication: it sends and receives the data to and from the game server.


```python
def register_ws_callback(self, callback):
```
Intended to be used as a decorator. Registers a callback you want to handle WebSocket data transmission.
Your callback will receive only one value: a dictionary of data sent by JavaScript-application through WebSocket protocol.
Your callback must return a dictionary of data to send to the game server.
Your callback acts as a filter that may prevent corrupt/large/incorrect data from reaching the game server, as the game server has other more important things to do rather than to handle such data.
Other words, your callback performs 1-way communication: it only processes the data that is sent to the game server.


JavaScript library (optional - only for WebSockets and AJAX)
------------------------------------------------------------
The library only includes one class called __MOTDPlayerClass__.
To instantiate this class, pass a magic initialization string that MOTDPlayer Flask counterpart inserts into every template context this way:
```html
<script type="application/javascript" src="/static/motdplayer/motdplayer.js"></script>
<script type="application/javascript">
    var MOTDPlayer = new MOTDPlayerClass("{{ base64_init_string }}");
</script>
```

Then you get a `MOTDPlayer` instance that provides the following _methods_:

```javascript
post = function (data, successCallback, errorCallback)
```
This function makes an AJAX call. Second and third arguments are optional.
The `data` argument is a dictionary (JavaScript object) to send to.
The `successCallback` argument must be a function receiving the object that Flask application sends back to you.
The `errorCallback` argument must be a function that receives a string briefly describing an error (if any) - be it a network error or some MOTDPlayer-specific error (failed auth, for example).


```javascript
isWSSupported = function ()
```
Use this function to determine whether or not WebSocket communication is available.
This function just performs a regular browser check. It CANNOT, however, tell you if the web-server is configured to use web-sockets or if the current page supports them.


```javascript
openWSConnection = function (openCallback, messageCallback, closeCallback, errorCallback)
```
This function establishes a WebSocket connection with the current page.
The `openCallback` argument must be a function that will be called (without arguments) when the connection successfully opens.
The `messageCallback` argument must be a function receiving the data sent to you by the Flask application.
The `closeCallback` argument must be a function that will be called (without arguments) when the connection closes.
The `errorCallback` argument must be a function that receives a string briefly describing an error (if any) - be it a network error or some MOTDPlayer-specific error (page doesn't support WebSocket communication, for example).
Makes no effect if there already exists an active WebSocket connection.


```javascript
closeWSConnection = function ()
```
This function closes current WebSocket connection.
Makes no effect if there's no active WebSocket connection.


```javascript
sendWSData = function (obj)
```
Use this function to send your data to the Flask application.
The `obj` argument is the data you send.
Makes no effect if there's no active WebSocket connection.


```javascript
switchPage = function (newPageId, successCallback, errorCallback)
```
Use this function to request a page switch.
The `newPageId` argument is the ID of the page you want to switch to.
The `successCallback` argument must be a function that will be called (without arguments) if the switch went successfully.
The `errorCallback` argument must be a function that receives a string briefly describing an error (if any) - be it a network error or some MOTDPlayer-specific error (switch wasn't allowed, for example).

