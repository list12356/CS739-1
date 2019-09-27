from client.client import Client
import time


def main(server_list):
    # basic correctness
    # test_correct(server_list)
    test_order(server_list)

def test_correct(server_list):
    # basic correctness
    client = Client(server_list)
    old_val = client.put("aa", "11")
    old_val = client.put("bb", "22")
    old_val = client.put("cc", "33")
    time.sleep(1)
    old_val = client.put("aa", "44")
    old_val = client.put("bb", "55")
    old_val = client.put("cc", "66")
    print(client.get("aa"))
    print(client.get("bb"))
    print(client.get("cc"))
    import pdb; pdb.set_trace()
    # assert client.get("aa") == "44"
    # assert client.get("bb") == "55"
    # assert client.get(

def test_order(server_list):
    client = Client(server_list)
    failure = 0
    client.put("aa", "xxx")
    # import pdb; pdb.set_trace()
    time.sleep(1)
    for i in range(1000):
        old_val = client.put("aa", str(i))
        if old_val == '':
            # import pdb; pdb.set_trace()
            failure += 1
    print(client.get("aa"))
    print("Total Failuer: {!s}".format(failure))

def test_throughput(server_list):
    client = Client(server_list)



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', type=str, nargs='+')
    args = parser.parse_args()
    main(args.servers)
