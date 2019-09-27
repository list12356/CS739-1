import socket
import sys
import datetime
import time
# import message_pb2
import pickle
import custom_protocol
from custom_protocol import CustomProtocol
from threading import Thread
import socket
import threading
import socketserver
import os


class KVServer:
    def __init__(self, port, server_list):
        self.key2val = {}
        self.key2time = {}
        self.lastSaveTime = self.getTime()
        self.recoverFromDisk()
        self.protocol = CustomProtocol()
        self.port = port
        self.host = "localhost"
        self.server_list = server_list
    
    def saveDictIfTimeOut(self):
        if self.getTime() - self.lastSaveTime > 5:
            self.saveToDisk()
            self.lastSaveTime = self.getTime()
            

    def saveToDisk(self):
        try:
            with open(str(self.host) + '_' + str(self.port) + '_key2val.pkl', 'wb') as f:
                pickle.dump(self.key2val, f, pickle.HIGHEST_PROTOCOL)
            with open(str(self.host) + '_' + str(self.port) + '_key2time.pkl', 'wb') as f:
                pickle.dump(self.key2time, f, pickle.HIGHEST_PROTOCOL)
            #print("saving dict to disk")
        except:
            print("saving dict failed")

    def recoverFromDisk(self):
        try:
            #print("Loading dict from disk")
            with open(str(self.host) + '_' + str(self.port) + '_key2val.pkl', 'rb') as f:
                self.key2val = pickle.load(f)
            with open(str(self.host) + '_' + str(self.port) + '_key2time.pkl', 'rb') as f:
                self.key2time = pickle.load(f)
        except:
            print("No existing dict found")

    def getTime(self):
        now = datetime.datetime.utcnow()
        return int(now.strftime("%s"))

    def initSocket(self):
        # initiate socket at the given port
        # https://pymotw.com/2/socket/tcp.html
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Bind socket to local host and port
        try:
            self.socket.bind((self.host, self.port))
        except socket.error as msg:
            print('Bind failed. ' + str(msg))
            sys.exit()

    def processRequest(self, request):
        # request is a string
        # message = custom_protocol.Message()
        # message.ParseFromString(request)
        try:
            message = self.protocol.decode(request)
        except:
            # print("failed decode packet")
            return

        # message.print()
        ACK = custom_protocol.Message()
        if message.Op == custom_protocol.Message.PUT:
            returnVal, oldValue = self.put(message.key, message.value, message.time)
            # print(returnVal, oldValue)
            ACK.returnValue = returnVal
            if oldValue:
                ACK.oldValue = oldValue
                ACK.hasOldValue = 1
            else:
                ACK.hasOldValue = 0
            return self.protocol.encode(ACK)
        elif message.Op == custom_protocol.Message.GET:
            #print("Get operation")
            returnVal, value, time = self.get(message.key)
            ACK.returnValue = returnVal
            if value:
                ACK.hasValue = 1
                ACK.value = value
                ACK.time = time
            else:
                ACK.hasValue = 0
            return self.protocol.encode(ACK)
        
        elif message.Op == custom_protocol.Message.INIT:
            if not os.path.exists(self.server_list):
                print("No server list found!")
                return self.protocol.encode(ACK)
            try:
                with open(self.server_list) as server_file:
                    tmp_list = [x.rstrip() for x in server_file.readlines()]
                    ACK.returnValue = len(tmp_list)
                    ACK.value = ';'.join(tmp_list)
            except:
                pass
            
            return self.protocol.encode(ACK)

    def get(self, key):
        # get the value and timestamp for the given key
        # return returnValue, value, timestamp
        if(key not in self.key2val):
            return 1, None, None
        else:
            return 0, self.key2val[key], self.key2time[key]

    
    def put(self, key, value, time):
        # put operation
        # return returnValue, oldValue
        if key not in self.key2val:
            oldValue = None 
            self.key2val[key] = value 
            self.key2time[key] = time 
            return 1, oldValue
        else:
            oldValue = self.key2val[key]
            if oldValue == value:
                return 0, oldValue
            oldTime = self.key2time[key]
            if time < oldTime:
                # local store already have a newer version
                # no update is done
                # What should we return in this case???
                return 0, oldValue 
            else:
                self.key2val[key] = value 
                self.key2time[key] = time 
                return 0, oldValue

kv_server = None
server_list = None

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        cur_thread = threading.current_thread()
        # print('Handling request thread: {!s}'.format(cur_thread.name))
        while True:
            data = self.request.recv(16384)
            if not data:
                break
            response = kv_server.processRequest(data)
            if response:
                self.request.sendall(response)
        # print('Connection closed by client in thread: {!s}'.format(cur_thread.name))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class PersistThread(threading.Thread):

    def run(self):
        while(True):
            time.sleep(1)
            kv_server.saveDictIfTimeOut()



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_list', type=str, default="server_list")
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    HOST = 'localhost'
    PORT = args.port

    kv_server = KVServer(PORT, args.server_list)
    kv_daemon = PersistThread()
    kv_daemon.daemon = True
    kv_daemon.start()
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)
        server_thread.join()
        # server.shutdown()
