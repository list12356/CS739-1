import ctypes

_client = ctypes.cdll.LoadLibrary("./lib739kv.so")
# _client.kv739_get.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
# _client.kv739_put.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]


class Client:
    
    def __init__(self, server_list):
        num_server = len(server_list)
        argv = (ctypes.c_char_p * (num_server + 1))()
        for i in range(num_server):
            argv[i] = ctypes.c_char_p(server_list[i].encode('ascii'))
        _client.kv739_init(argv)

    def put(self, key, value):
        old_value = ctypes.create_string_buffer(2048)
        # import pdb; pdb.set_trace()
        rtn = _client.kv739_put(key.encode("ascii").ljust(128, b'\0'),\
            value.encode("ascii").ljust(2048, b'\0'), old_value)
        return old_value.value.decode("utf-8"), rtn
    
    def get(self, key):
        val = ctypes.create_string_buffer(2048)
        rtn = _client.kv739_get(key.encode("ascii").ljust(128, b'\0'), val)
        return val.value.decode("utf-8"), rtn
    
    def shutdown(self):
        _client.kv739_shutdown()

    # def __del__(self):
    #     self.shutdown()
