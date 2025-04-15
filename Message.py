import json
import uuid
import time


class Message:
    def __init__(self, msgType, command, sender, recipient,state, body=""):
        self.header = {
            "type": msgType,
            "command": command,
            "senderID": sender,
            "recipientID": recipient,
            "state": state,
            "messageID": str(uuid.uuid4()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "length": len(body.encode()) if body else 0
        }
        self.body = body

    def toJson(self):
        return json.dumps({"header": self.header, "body": self.body})

    def encode(self):
        return self.toJson().encode()

    @staticmethod
    def fromJson(jsonStr):
        msgDict = json.loads(jsonStr)

        msg = Message(
            msgDict["header"]["type"],
            msgDict["header"]["command"],
            msgDict["header"]["senderID"],
            msgDict["header"]["recipientID"],
            msgDict["header"]["state"],
            msgDict["body"]
        )
        # Copy over the messageID and timestamp instead of generating new ones
        msg.header["messageID"] = msgDict["header"]["messageID"]
        msg.header["timestamp"] = msgDict["header"]["timestamp"]
        return msg

    @staticmethod
    def decode(data):
        return Message.fromJson(data.decode())

    class MessageTypes:
        COMMAND = "COMMAND"
        DATA = "DATA"
        CONTROL = "CONTROL"

    class States:
        AVAILABLE = "AVAILABLE" 
        CONNECTED = "CONNECTED"
        AWAY = "AWAY"

    class Commands:
        INIT = "INIT"
        TERM = "TERM"
        DATA = "DATA"
        ACK = "ACK"
        RESEND = "RESEND"
        SEEDER = "SEEDER"
        LEECHER = "LEECHER"
        FILE_LIST = "FILE_LIST"
        FILE_REQUEST = "FILE_REQUEST"
        CHUNK_LIST = "CHUNK_LIST"
        CHUNK_ASSIGNMENT = "CHUNK_ASSIGNMENT"
        PORT_INFO="PORT_INFO"