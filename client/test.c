#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "client.h"

int main(int argc, char* argv[])
{
    //test_split
    if (argc < 2)
    {
        fprintf(stderr, "error usage\n");
    }
    char **server_list = malloc((argc + 1)*sizeof(char*));
    for(int i = 0; i < argc - 1; i++)
    {
        server_list[i] = malloc(128);
        strcpy(server_list[i], argv[i + 1]);
    }
    server_list[argc] = NULL;
    char value[2048];
    kv739_init(server_list);
    kv739_put("aa", "11", value);
    kv739_put("bb", "22", value);
    kv739_put("cc", "33", value);
    kv739_get("aa", value);
    printf("%s\n", value);
    kv739_get("bb", value);
    printf("%s\n", value);
    kv739_get("cc", value);
    printf("%s\n", value);
    return 0;
}