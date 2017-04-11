from base64 import b64encode
import json
from json.decoder import JSONDecodeError
import sys
from traceback import format_exc

from flask import jsonify, render_template, request

try:
    import uwsgi
except ImportError:
    uwsgi = None

from ccp.transmit import CommunicationEnded
from ccp.sock_client import ConnectionAbort

from . import AuthMethod, config, servers, sockets, User, wrps
from .clients import MOTDClient


TEMPLATE_CSGO_REDIRECT_PATH = "motdplayer/csgo_redirect.html"
TEMPLATE_ERROR_PATH = "motdplayer/error.html"
EXCEPTION_HEADER = ("{breaker}\nMOTDPlayer has caught "
                    "an exception!\n{breaker}\n".format(breaker="=" * 79))


def print_exc():
    print(EXCEPTION_HEADER, file=sys.stderr, end='')
    print(format_exc(), file=sys.stderr)


def build_error(error_id, ws):
    if ws:
        return {
            'status': "ERROR_VIEW",
            'error_id': error_id,
        }

    if request.is_json:
        return jsonify({
            'status': "ERROR_VIEW",
            'error_id': error_id,
        })

    return render_template(TEMPLATE_ERROR_PATH, error=error_id)


def create_client(client_class, db, server_id, plugin_id, page_id, steamid,
                  auth_method, auth_token, session_id, ws):
    """
    :return: server, wrp, user, client, error
    """
    # Check if server/plugin/page combo exists
    try:
        server = servers[server_id]
    except KeyError:
        return None, None, None, None, build_error("Unknown Server.", ws)

    try:
        plugin_wrps = wrps[plugin_id]
    except KeyError:
        return server, None, None, None, build_error("Unknown Plugin.", ws)

    try:
        wrp = plugin_wrps[page_id]
    except KeyError:
        return server, None, None, None, build_error("Unknown Page.", ws)

    # Auth
    steamid = str(steamid)
    user = User.query.filter(
        User.steamid == steamid, User.server_id == server_id).first()

    if user is None:
        user = User(server_id, steamid)
        db.session.add(user)

    if not user.authenticate(
            auth_method, plugin_id, page_id, auth_token, session_id):

        db.session.rollback()
        return server, wrp, None, None, build_error("Invalid Auth.", ws)

    # Connection to SRCDS
    try:
        client = client_class((server['host'], server['port']), 'motdplayer')
    except ConnectionAbort:
        
        # May happen if our IP address is not in receiver's CCP whitelist
        return server, wrp, user, None, build_error("IP Not Whitelisted.", ws)

    if auth_method == AuthMethod.SRCDS:
        new_salt = user.get_new_salt()

        if not client.set_identity(steamid, new_salt, session_id, ws):
            return (
                server, wrp, user, client, build_error(
                    "Identity Rejected.", ws))

        user.salt = new_salt

    elif auth_method == AuthMethod.WEB:
        if not client.set_identity(steamid, None, session_id, ws):
            return (
                server, wrp, user, client, build_error(
                    "Identity Rejected.", ws))

        web_salt = user.get_new_salt()
        user.web_salt = web_salt

    else:
        client.stop()
        return server, wrp, user, client, build_error(
            "Unknown Auth Method.", ws)

    db.session.commit()

    return server, wrp, user, client, None


def init(app, db):
    @app.route(config.get('application', 'csgo_redirect_from'))
    def route_csgo_redirect(server_id, plugin_id, page_id, steamid,
                            auth_method, auth_token, session_id):

        redirect_to = config.get('application', 'csgo_redirect_to').format(
            server_id=server_id,
            plugin_id=plugin_id,
            page_id=page_id,
            steamid=steamid,
            auth_method=auth_method,
            auth_token=auth_token,
            session_id=session_id,
        )

        return render_template(
            TEMPLATE_CSGO_REDIRECT_PATH, redirect_to=redirect_to)

    @app.route(config.get('application', 'switch_url'), methods=['POST', ])
    def route_ajax_switch(server_id, plugin_id, new_page_id, page_id, steamid,
                          auth_method, auth_token, session_id):

        # Action check
        if request.json['action'] != "switch":
            return build_error("Bad Request.", ws=False)

        server, wrp, user, client, error = create_client(
            MOTDClient, db, server_id, plugin_id, page_id, steamid,
            auth_method, auth_token, session_id, ws=False)

        if error is not None:
            return error

        # Switch
        if not client.request_switch(new_page_id):
            return build_error("Switch Rejected.", ws=False)

        return jsonify({
            'status': "OK",
            'web_auth_token': user.get_web_auth_token(
                plugin_id, new_page_id, session_id),
        })

    @app.route(
        config.get('application', 'base_route'), methods=['GET', 'POST'])
    def route_base_route(server_id, plugin_id, page_id, steamid, auth_method,
                         auth_token, session_id):

        server, wrp, user, client, error = create_client(
            MOTDClient, db, server_id, plugin_id, page_id, steamid,
            auth_method, auth_token, session_id, ws=False)

        if error is not None:
            return error

        # We should probably change it in CCP so that exchange_custom_data
        # accepts a dictionary, not **kwargs
        def ex_data_func(data):
            return client.exchange_custom_data(**data)

        if request.is_json:
            try:
                action = request.json['action']
                data = request.json['custom_data']
            except KeyError:
                return build_error("Bad Request.", ws=False)

            if action != "custom_data":
                return build_error("Invalid Action.", ws=False)

            try:
                data = wrp.ajax_callback(ex_data_func, data)
            except Exception:
                print_exc()
                return build_error("WRP AJAX Callback Raised.", ws=False)
            finally:
                client.stop()

            web_auth_token = user.get_web_auth_token(
                plugin_id, page_id, session_id)

            return jsonify({
                'status': "OK",
                'web_auth_token': web_auth_token,
                'custom_data': data
            })

        else:
            try:
                template_name, context = wrp.regular_callback(ex_data_func)

            except Exception:
                print_exc()
                return build_error("WRP Callback Raised.", ws=False)
            finally:
                client.stop()

            web_auth_token = user.get_web_auth_token(
                plugin_id, page_id, session_id)

            auth_data = {
                'serverId': server_id,
                'pluginId': plugin_id,
                'pageId': page_id,
                'steamid': str(steamid),  # JS cannot into big numbers
                'authMethod': AuthMethod.SRCDS,
                'authToken': auth_token,
                'sessionId': session_id,
            }
            next_auth_data = {
                'serverId': server_id,
                'pluginId': plugin_id,
                'pageId': page_id,
                'steamid': str(steamid),  # JS cannot into big numbers
                'authMethod': AuthMethod.WEB,
                'authToken': web_auth_token,
                'sessionId': session_id,
            }

            return render_template(
                template_name,
                context=context,
                auth_data=auth_data,
                next_auth_data=next_auth_data,
                base64_init_string=b64encode(
                    json.dumps(next_auth_data).encode('utf-8')
                ).decode('utf-8'),
            )

    # WebSocket
    if uwsgi is None:
        @app.route(config.get('application', 'base_route_ws'))
        def route_base_route_ws(server_id, plugin_id, page_id, steamid,
                                auth_method, auth_token, session_id):

            return build_error("WebSocket Not Supported", ws=False)

    else:
        @sockets.route(config.get('application', 'base_route_ws'))
        def route_base_route_ws(server_id, plugin_id, page_id, steamid,
                                auth_method, auth_token, session_id):

            def ws_send(**kwargs):
                uwsgi.websocket_send(json.dumps(kwargs).encode('utf-8'))

            server, wrp, user, client, error = create_client(
                MOTDClient, db, server_id, plugin_id, page_id, steamid,
                auth_method, auth_token, session_id, ws=True)

            if error is not None:
                ws_send(**error)
                return

            web_auth_token = user.get_web_auth_token(
                plugin_id, page_id, session_id)

            ws_send(status="OK", web_auth_token=web_auth_token)

            fd_ws = uwsgi.connection_fd()
            fd_client = client.sock.fileno()

            def read_from_ws():
                try:
                    data_encoded = uwsgi.websocket_recv_nb()
                except OSError:
                    client.stop()
                    return

                if not data_encoded:
                    return

                try:
                    data = json.loads(data_encoded.decode('utf-8'))
                except (JSONDecodeError, UnicodeDecodeError):
                    print_exc()
                    client.stop()
                    return
                except OSError:
                    print_exc()
                    client.stop()
                    return

                # WebSocket -> SRCDS: data goes through wrp callback
                try:
                    filtered_data = wrp.ws_callback(data)
                except Exception:
                    print_exc()
                    client.stop()
                    ws_send(**build_error(
                        "WRP WS Callback Raised.", ws=True))
                    return

                try:
                    data_encoded = json.dumps(
                        filtered_data).encode('utf-8')
                except (TypeError, UnicodeEncodeError):
                    print_exc()
                    client.stop()
                    ws_send(**build_error(
                        "WRP WS Callback Invalid Answer.", ws=True))
                    return

                client.send_data(data_encoded)

            while True:
                uwsgi.wait_fd_read(fd_ws, 3)
                uwsgi.wait_fd_read(fd_client)
                uwsgi.suspend()

                fd = uwsgi.ready_fd()

                if fd > -1:
                    if fd == fd_ws:
                        read_from_ws()

                    elif fd == fd_client:
                        # SRCDS -> WebSocket: send directly without interfering
                        try:
                            data_encoded = client.receive_data()
                        except CommunicationEnded:
                            return

                        try:
                            data = json.loads(data_encoded.decode('utf-8'))
                        except (JSONDecodeError, UnicodeDecodeError):
                            print_exc()
                            # TODO: client.stop?
                            ws_send(**build_error(
                                "SRCDS Sends Invalid Data", ws=True))

                            return

                        ws_send(status="CUSTOM_DATA",
                                custom_data=data['custom_data'])

                else:

                    # Manage ping/pong
                    read_from_ws()
