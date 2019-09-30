from client.client import Client

from multiprocessing import Process
import time
import random
import string

TEST_COUNTER = 50000
num_key = 100

def main(server_list):
    # basic correctness
    test_correct_single(server_list)
    # test_correct_multiple(server_list)
    # test_order_single(server_list)
    # test_order_multiple(server_list)
    # test_throughput(server_list)
    test_dist_throughput(server_list)
    # test_latency(server_list)
    # test_dist_latency(server_list)

def test_correct_single(server_list):
    # basic correctness
    print("Testing basic correctness")
    client = Client(server_list)
    old_val, rtn = client.put("aa", "11")
    if rtn != 0:
        print("Incorrect return value!")
    old_val, rtn = client.put("bb", "22")
    if rtn != 0:
        print("Incorrect return value!")
    old_val, rtn = client.put("cc", "33")
    if rtn != 0:
        print("Incorrect return value!")
    old_val, rtn = client.put("aa", "44")
    if rtn != 0:
        print("Incorrect return value!")
    if old_val != "11":
        print("Inconsistent value, exepected: 11, get: {}".format(old_val))
    old_val, rtn = client.put("bb", "55")
    if rtn != 0:
        print("Incorrect return value!")
    if old_val != "22":
        print("Inconsistent value, exepected: 22, get: {}".format(old_val))
    old_val, rtn = client.put("cc", "66")
    if rtn != 0:
        print("Incorrect return value!")
    if old_val != "33":
        print("Inconsistent value, exepected: 33, get: {}".format(old_val))
    val, rtn = client.get("aa")
    if rtn != 0:
        print("Incorrect return value!")
    if val != "44":
        print("Inconsistent value, exepected: 44, get: {}".format(val))
    val, rtn = client.get("bb")
    if rtn != 0:
        print("Incorrect return value!")
    if val != "55":
        print("Inconsistent value, exepected: 55, get: {}".format(val))
    val, rtn = client.get("cc")
    if rtn != 0:
        print("Incorrect return value!")
    if val != "66":
        print("Inconsistent value, exepected: 66, get: {}".format(val))
    client.shutdown()
    print("Test Succeed!")

def test_correct_multiple(server_list):
    print("Testing consistency over multiple client")
    client_list = []
    for server in server_list:
        client_list.append(Client([server]))
    for i in range(len(client_list)):
        print("putting value for server: {}".format(i))
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
    value = ''.rjust(1024, '0')
    failure = 0
    elapsed_time = 0
    for i in range(10):
        for key in key_list:
            start = time.time()
            old_val, rtn = client.put(key, value)
            if (rtn == -1):
                failure += 1
            elapsed_time += time.time() - start
    
    print(failure)
    rate = (10*num_key*(1024+32)/1024/1024/elapsed_time)
    print("Througput for uniform key: {:.3f} MB/s".format(rate))  

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
    
    rate = (10*num_key*(1024+32)/1024/1024/elapsed_time)
    client.shutdown()
    print(failure)
    print("Througput for single client: {:.3f} MB/s".format(rate))  
    # rate_dict[server_id] = 10*10000*(2048+32)/1024/1024/elapsed_time

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

    rate = (len(server_list)*10*10*num_key*(1024+32)/1024/1024/elapsed_time)
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


def test_latency(server_list):
    # test latency of uniform key for put
    print("Testing latency...")
    client = Client(server_list)
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]) for x in range(num_key)]
    value = ''.rjust(1024, '0')
    failure = 0
    elapsed_time = 0
    for i in range(10):
        for key in key_list:
            start = time.time()
            old_val, rtn = client.put(key, value)
            if (rtn == -1):
                failure += 1
            elapsed_time += time.time() - start
    
    print(failure)
    print(elapsed_time)
    latency = elapsed_time / (10*num_key) * 1e3
    print("Average latency for uniform key: {:.3f} ms".format(latency))  

def _dist_latency(server, key_list, value):
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
    
    rate = (10*num_key*(1024+32)/1024/1024/elapsed_time)
    client.shutdown()
    if failure > 0:
        print(failure)
    latency = elapsed_time / (10*num_key) * 1e3
    print("Average latency for uniform key: {:.3f} ms".format(latency))  

def test_dist_latency(server_list):
    key_list = [''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]) for x in range(num_key)]
    # value = ''.rjust(2048, '0')
    value = '0'
    print("Testing latency from multiple client")
    process_list = []
    start = time.time()
    for server in server_list:
        for i in range(10):
            p = Process(target=_dist_latency, args=(server, key_list, value, ))
            # p = Process(target=test_throughput, args=([server], ))
            p.start()
            process_list.append(p)
    for p in process_list:
        p.join()
    elapsed_time = time.time() - start


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', type=str, nargs='+')
    args = parser.parse_args()
    main(args.servers)
