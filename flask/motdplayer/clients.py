from contextlib import suppress
import json

from ccp.constants import CommunicationMode
from ccp.transmit import CommunicationAccepted, SRCDSClient


class MOTDClient(SRCDSClient):
    def __init__(self, addr, plugin_name):
        super().__init__(addr, plugin_name)

        self.set_mode(CommunicationMode.RAW)

        with suppress(CommunicationAccepted):
            self.receive_data()

    def exchange_json_data(self, **kwargs):
        self.send_data(json.dumps(kwargs).encode('utf-8'))
        return json.loads(self.receive_data().decode('utf-8'))

    def exchange_custom_data(self, data):
        response = self.exchange_json_data(
            action="custom-data", custom_data=data)

        if response['status'] == "OK":
            return response['custom_data']

        return None

    def request_switch(self, new_page_id):
        response = self.exchange_json_data(
            action="switch", new_page_id=new_page_id)

        self.stop()

        return response['status'] == "OK"

    def set_identity(self, steamid, salt, session_id, ws):
        response = self.exchange_json_data(
            action="set-identity", new_salt=salt, steamid=steamid,
            session_id=session_id, ws=ws
        )

        if response['status'] == "OK":
            return None

        self.stop()
        return response['status']
