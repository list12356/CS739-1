from client.client import Client

def main(server_list):
    # basic correctness
    client = Client(server_list)
    old_val = client.put("aa", "11")
    old_val = client.put("bb", "22")
    old_val = client.put("cc", "33")
    print(client.get("aa"))
    print(client.get("bb"))
    print(client.get("cc"))
    old_val = client.put("aa", "44")
    old_val = client.put("bb", "55")
    old_val = client.put("cc", "66")
    print(client.get("aa"))
    print(client.get("bb"))
    print(client.get("cc"))



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', type=str, nargs='+')
    args = parser.parse_args()
    main(args.servers)
