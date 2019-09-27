#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "client.h"

extern int num_server;
extern char** fetch_server(char** init_list);
extern struct timeval timeout;

int test_fetch(char** init_list)
{
    // Should use mock test, but
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    char** server_list = fetch_server(init_list);
    printf("%d\n", num_server);
    for(int i = 0; i < num_server; i++)
        printf("%s\n", server_list[i]);
    
    return 0;
}

int test_init(char** server_list)
{
    return kv739_init(server_list);
}

int test_split()
{
    return 0;
}

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
    test_fetch(server_list);
    test_init(server_list);
    return 0;
}