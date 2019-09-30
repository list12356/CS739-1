from client.client import Client
from server.custom_protocol import CustomProtocol
from server.custom_protocol import Message

from multiprocessing import Process
from multiprocessing import Manager
import time
import random
import string
import socket

TEST_COUNTER = 50000
socket_dict = {}
protocol = CustomProtocol()
num_key = 100

def main(server_list):
    test_setup(server_list)
    # basic correctness
    test_correct_single(server_list)
    test_correct_multiple(server_list)
    # test_order_single(server_list)
    # test_order_multiple(server_list)
    # test_throughput(server_list)
    # test_dist_throughput(server_list)
    test_block(server_list)

def test_setup(server_list):
    for server in server_list:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr, port = server.split(':')
        s.connect(tuple([addr, int(port)]))
        socket_dict[server] = s 
   

def test_correct_single(server_list):
    # basic correctness
    print("Testing basic correctness")
    client = Client(server_list)
    old_val, rtn = client.put("aa", "11")
    if rtn != 1:
        print("Incorrect return value!")
    old_val, rtn = client.put("bb", "22")
    if rtn != 1:
        print("Incorrect return value!")
    old_val, rtn = client.put("cc", "33")
    if rtn != 1:
        print("Incorrect return value!")
    old_val, rtn = client.put("cc", "44")
    if rtn != 0:
        print("Incorrect return value!")
    if old_val != "11":
        print("Inconsistent value, exepected: 11, get: {}".format(old_val))
    old_val, rtn = client.put("aa", "55")
    if rtn != 0:
        print("Incorrect return value!")
    if old_val != "22":
        print("Inconsistent value, exepected: 22, get: {}".format(old_val))
    old_val, rtn = client.put("bb", "66")
    if rtn != 0:
        print("Incorrect return value!")
    if old_val != "33":
        print("Inconsistent value, exepected: 33, get: {}".format(old_val))
    val, rtn = client.get("aa")
    if rtn != 0:
        print("Incorrect return value!")
    if val != "55":
        print("Inconsistent value, exepected: 44, get: {}".format(val))
    val, rtn = client.get("bb")
    if rtn != 0:
        print("Incorrect return value!")
    if val != "66":
        print("Inconsistent value, exepected: 55, get: {}".format(val))
    val, rtn = client.get("cc")
    if rtn != 0:
        print("Incorrect return value!")
    if val != "43":
        print("Inconsistent value, exepected: 66, get: {}".format(val))
    client.shutdown()
    print("Test Succeed!")

def test_correct_multiple(server_list):
    print("Testing consistency over multiple client")
    client_list = []
    for server in server_list:
        client_list.append(Client([server]))
    for i in range(len(client_list)):
        client_list[i].put("test_server_name", server_list[i])
        for j in range(len(client_list)):
            value, rtn = client_list[j].get("test_server_name")
            if value != server_list[i]:
                print("Inconsistent value, exepected: {}, get: {}".format(server_list[i], value))
            if rtn != 0:
                print("Incorrect rtn from client: {}".format(j))
    for client in client_list:
        client.shutdown()
    print("Test Succeed!")
    return 0


def test_throughput(server_list):
    # test throughput of uniform key for put
    print("Testing througput...")
    client = Client(server_list)
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]) for x in range(num_key)]
    value = ''.rjust(2048, '0')
    failure = 0
    elapsed_time = 0
    for i in range(10):
        for key in key_list:
            start = time.time()
            old_val, rtn = client.put(key, value)
            if (rtn == -1):
                failure += 1
            elapsed_time += time.time() - start
    
    rate = (10*num_key*(2048+32)/1024/1024/elapsed_time)
    print("Througput for uniform key: {:.3f} MB/s".format(rate))  

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
    latency_put = elapsed_time / (10*num_key) / 1e3
    latency_get = elapsed_get_time / (10*num_key) / 1e3
    print("Put average latency: {:.3f} ms".format(latency_put))
    print("Get average latency: {:.3f} ms".format(latency_get))


def _dist_throughput(server, key_list, value):
    client = Client([server])
    elapsed_time = 0
    failure = 0
    random.shuffle(key_list)
    for i in range(10):
        for key in key_list:
            start = time.time()
            old_val, rtn = client.put(key, value)
            if (rtn == -1):
                failure += 1
            elapsed_time += time.time() - start
    
    rate = ((10*num_key - failure)*(2048+32)/1024/1024/elapsed_time)
    client.shutdown()
    print("Througput for single client: {:.3f} MB/s".format(rate))  
    # rate_dict[server_id] = 10*10000*(2048+32)/1024/1024/elapsed_time

    latency_put = elapsed_time / (10*10000) / 1e3
    print("Put average latency for single client: {:.3f} ms".format(latency_put))

def test_dist_throughput(server_list):
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]) for x in range(num_key)]
    # value = ''.rjust(2048, '0')
    value = '0'
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

    rate = (len(server_list)*10*10*num_key*(2048+32)/1024/1024/elapsed_time)
    print("Througput for uniform key from multiple client: {:.3f} MB/s".format(rate))  

 
def test_order_single(server_list, verbose=True):
    if verbose:
        print("Testing adding counter from single client")
    failure = 0
    client = Client(server_list)
    client.put("counter", "xxx")
    for i in range(1 + TEST_COUNTER):
        old_val, rtn = client.put("counter", str(i))
        if rtn == -1:
            failure += 1
    print("Total Failuer: {!s}".format(failure))
    if verbose:
        val, _ = client.get("counter")
        print("Total counter: {}, actual get: {}".format(TEST_COUNTER, val))

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
    val, _ = client.get("counter")
    print("Expected get counter {}, actual get: {}".format(TEST_COUNTER, val))

def _test_block(server):
    msg = Message()
    msg.Op = Message.BLOCK  
    socket_dict[server].sendall(protocol.encode(msg))
    
def _test_unblock(server):
    msg = Message()
    msg.Op = Message.UNBLOCK
    socket_dict[server].sendall(protocol.encode(msg))

def test_block(server_list):
    for k in range(len(server_list)):
        test_block_K(server_list, k)

def _test_block_put(server_list, ind, trail, key_list, success_dict):
    client = Client(server_list)
    success = 0
    for i in range(trail):
        val, rtn = client.put(key_list[i + ind*trail], str(i + ind*trail))
        if rtn >= 0:
            success += 1
    success_dict[ind] = success
    # print("Client id: {}, success put: {}".format(ind, success))

def _test_block_get(server_list, ind, trail, key_list, success_dict):
    client = Client(server_list)
    success = 0
    for i in range(trail):
        val, rtn = client.get(key_list[i + ind*trail])
        if rtn == 0 and val == str(i + ind*trail):
            success += 1
        else:
            print("client: {}, return: {}, expected value: {}, get: {}".format(ind, rtn, i + ind*trail, val))
    success_dict[ind] = success
    # print("Client id: {}, success get: {}".format(ind, success))

def test_block_K(server_list, k, trail=100):
    print("Testing put/get random key with {} random server fail.".format(k))
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]) for x in range(trail)]

    block_list = random.sample(server_list, k)
    for server in block_list:
        _test_block(server)
    time.sleep(0.1) # give server time to block port
    success = 0
    manager = Manager()
    success_dict = manager.dict()
    process_list = []
    for i in range(trail//5):
        p = Process(target=_test_block_put, args=(server_list, i, 5, key_list, success_dict ))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()
   
    for i in range(trail//5):
        success += success_dict[i]

    print("Client put success rate is {:.3f}".format(success/trail)) 
    
    for server in block_list:
        _test_unblock(server)
    time.sleep(0.1) # give server time to unblock port
    block_list = random.sample(server_list, k)
    for server in block_list:
        _test_block(server)
    time.sleep(0.1) # give server time to block port
    
    success_dict = manager.dict()
    process_list = []
    success = 0
    for i in range(trail//5):
        p = Process(target=_test_block_get, args=(server_list, i, 5, key_list, success_dict ))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()
    
    for i in range(trail//5):
        success += success_dict[i]
    
    for server in block_list:
        _test_unblock(server)
    print("Client get success rate is {:.3f}".format(success/trail)) 
     
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', type=str, nargs='+')
    args = parser.parse_args()
    main(args.servers)
