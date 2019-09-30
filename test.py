from client.client import Client
from server.custom_protocol import CustomProtocol
from server.custom_protocol import Message

from multiprocessing import Process
import time
import random
import string
import socket

TEST_COUNTER = 50000
socket_dict = {}
protocol = CustomProtocol()

def main(server_list):
    test_setup(server_list)
    # basic correctness
    test_correct_single(server_list)
    test_correct_multiple(server_list)
    # test_order_single(server_list)
    # test_order_multiple(server_list)
    # test_throughput(server_list)
    test_dist_throughput(server_list)

def test_setup(server_list):
    for server in server_list:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        import pdb; pdb.set_trace()
        addr, port = server.split(':')
        s.connect(tuple([addr, int(port)]))
        socket_dict[server] = s 
   

def test_correct_single(server_list):
    # basic correctness
    print("Testing basic correctness")
    client = Client(server_list)
    old_val = client.put("aa", "11")
    old_val = client.put("bb", "22")
    old_val = client.put("cc", "33")
    old_val = client.put("aa", "44")
    if old_val != "11":
        print("Inconsistent value, exepected: 11, get: {}".format(old_val))
    old_val = client.put("bb", "55")
    if old_val != "22":
        print("Inconsistent value, exepected: 22, get: {}".format(old_val))
    old_val = client.put("cc", "66")
    if old_val != "33":
        print("Inconsistent value, exepected: 33, get: {}".format(old_val))
    val = client.get("aa")
    if val != "44":
        print("Inconsistent value, exepected: 44, get: {}".format(val))
    val = client.get("bb")
    if val != "55":
        print("Inconsistent value, exepected: 55, get: {}".format(val))
    val = client.get("cc")
    if val != "66":
        print("Inconsistent value, exepected: 66, get: {}".format(val))
    print("Test Succeed!")

def test_correct_multiple(server_list):
    print("Testing consistency over multiple client")
    client_list = []
    for server in server_list:
        client_list.append(Client([server]))
    for i in range(len(client_list)):
        client_list[i].put("test_server_name", server_list[i])
        for j in range(len(client_list)):
            value = client_list[j].get("test_server_name")
            if value != server_list[i]:
                print("Inconsistent value, exepected: {}, get: {}".format(server_list[i], value))
                return -1
    print("Test Succeed!")
    return 0


def test_throughput(server_list):
    # test throughput of uniform key for put
    print("Testing througput...")
    client = Client(server_list)
    num_key = 10000
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)]) for x in range(num_key)]
    value = ''.rjust(2048, '0')
    elapsed_time = 0
    for i in range(10):
        for key in key_list:
            start = time.time()
            client.put(key, value)
            elapsed_time += time.time() - start
    
    rate = (10*10000*(2048+32)/1024/1024/elapsed_time)
    print("Put operation througput for uniform key: {:.3f} MB/s".format(rate))

    random.shuffle(key_list)
    elapsed_get_time = 0
    for i in range(10):
        for key in key_list:
            start = time.time()
            client.get(key)
            elapsed_get_time += time.time() - start
    get_rate = (10*10000*(2048+32)/1024/1024/elapsed_get_time)
    print("Get operation througput for uniform key: {:.3f} MB/s".format(get_rate))

    # Estimate average latency per query
    latency_put = elapsed_time / (10*10000) / 1e3
    latency_get = elapsed_get_time / (10*10000) / 1e3
    print("Put average latency: {:.3f} ms".format(latency_put))
    print("Get average latency: {:.3f} ms".format(latency_get))


def _dist_throughput(server, key_list, value):
    client = Client([server])
    elapsed_time = 0
    random.shuffle(key_list)
    for i in range(10):
        for key in key_list:
            start = time.time()
            client.put(key, value)
            elapsed_time += time.time() - start
    
    rate = (10*10000*(2048+32)/1024/1024/elapsed_time)
    print("Througput for single client: {:.3f} MB/s".format(rate))  
    # rate_dict[server_id] = 10*10000*(2048+32)/1024/1024/elapsed_time

    latency_put = elapsed_time / (10*10000) / 1e3
    print("Put average latency for single client: {:.3f} ms".format(latency_put))

def test_dist_throughput(server_list):
    num_key = 10000
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)]) for x in range(num_key)]
    value = ''.rjust(2048, '0')
    print("Testing throughput from multiple client")
    process_list = []
    start = time.time()
    for server in server_list:
        for i in range(10):
            p = Process(target=_dist_throughput, args=(server, key_list, value, ))
            # p = Process(target=test_throughput, args=([server], ))
            p.start()
            process_list.append(p)
    for p in process_list:
        p.join()
    elapsed_time = time.time() - start

    rate = (len(server_list)*10*10*10000*(2048+32)/1024/1024/elapsed_time)
    print("Througput for uniform key from multiple client: {:.3f} MB/s".format(rate))  

 
def test_order_single(server_list, verbose=True):
    if verbose:
        print("Testing adding counter from single client")
    failure = 0
    client = Client(server_list)
    client.put("counter", "xxx")
    for i in range(1 + TEST_COUNTER):
        old_val = client.put("counter", str(i))
        if old_val == '':
            failure += 1
    print("Total Failuer: {!s}".format(failure))
    if verbose:
        print("Total counter: {}, actual get: {}".format(TEST_COUNTER, client.get("counter")))

def test_order_multiple(server_list):
    # provide each client single server
    print("Testing adding counter from multiple client")
    process_list = []
    for server in server_list:
        for i in range(5):
            p = Process(target=test_order_single, args=([server], False, ))
            p.start()
            process_list.append(p)
    for p in process_list:
        p.join()
    client = Client(server_list)
    print("Expected get counter {}, actual get: {}".format(TEST_COUNTER, client.get("counter")))

def _test_block(server):
    msg = Message()
    msg.Op = Message.BLOCK  
    socket_dict[server].sendall(protocol.encode(msg))
    
def _test_unblock(server):
    msg = Message()
    msg.Op = Message.UNBLOCK
    socket_dict[server].sendall(protocol.encode(msg))

def test_block(server_list):
    client = Client(server_list)
    client.put("block_key", "aaa")
    for server in server_list:
        _test_block(server)
    print(client.get("block_key"))
    for server in server_list:
        _test_unblock(server)
    print(client.get("block_key"))
    
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', type=str, nargs='+')
    args = parser.parse_args()
    main(args.servers)
