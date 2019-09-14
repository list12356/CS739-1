

int kv739_init(char ** server_list);
int kv739_shutdown(void);
int kv739_get(char * key, char * value);
int kv739_put(char * key, char * value, char * old_value);