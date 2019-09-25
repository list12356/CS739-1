from client.client import Client

def main(server_list):
    client = Client(server_list)
    old_val = client.put("aa", "11")
    old_val = client.put("cc", "22")
    old_val = client.put("bb", "33")
    print(client.get("aa"))
    print(client.get("bb"))
    print(client.get("cc"))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', type=str, nargs='+')
    args = parser.parse_args()
    main(args.servers)
