from server import KVServer
from custom_protocol import Message
from custom_protocol import CustomProtocol

kv_server = KVServer(6666, "server_list")

def test_fetch_server():
    test_msg = Message()
    test_msg.Op = Message.INIT
    protocol = CustomProtocol()
    ack = kv_server.processRequest(protocol.encode(test_msg))
    print(protocol.decode(ack).value.split(';'))

if __name__=="__main__":
    test_fetch_server()