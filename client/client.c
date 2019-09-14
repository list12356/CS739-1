
#include <sys/types.h>          /* See NOTES */
#include <sys/socket.h>
#include <stdlib.h>
#include <arpa/inet.h> 
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include "client.h"

/*
0-3 optype
4-7 time
8-11 return value
12 has old_value 
13 has_value 
128-255 key
256-2303 value
2304-4352 old value
*/

int num_server;
int* socket_list;

struct packet
{
    int optype;
    int time;
    int return_value;
    char has_old_val;
    char has_val;
    char key[128];
    char value[2048];
    char old_value[2048];
};

// use little endian to encode integer
int encode_int(char* bytes, int n)
{
    bytes[3] = (n >> 24) & 0xFF;
    bytes[2] = (n >> 16) & 0xFF;
    bytes[1] = (n >> 8) & 0xFF;
    bytes[0] = n & 0xFF;
}

int decode_int(char* bytes, int* n)
{
    *n = 0;
    *n |= bytes[3] << 24;
    *n |= bytes[2] << 16;
    *n |= bytes[1] << 8;
    *n |= bytes[0];
}

int encode(struct packet* pkt, char* str)
{
    encode_int(str, pkt -> optype);
    encode_int(str+4, pkt -> time);
    encode_int(str+8, pkt -> return_value);
    str[12] = pkt -> has_old_val;
    str[13] = pkt -> has_val;
    strcpy(str + 128, pkt -> key);
    strcpy(str + 256, pkt -> value);
    strcpy(str + 2304, pkt -> old_value);
}

int decode(struct packet* pkt, char* str)
{
    decode_int(str, &pkt -> optype);
    decode_int(str+4, &pkt -> time);
    decode_int(str+8, &pkt -> return_value);
    str[12] = pkt -> has_old_val;
    str[13] = pkt -> has_val;
    strcpy(pkt -> key, str + 128);
    strcpy(pkt -> value, str + 256);
    strcpy(pkt -> old_value, str + 2304);
}

int split(char* server, char** address, int* port)
{
    int n = strlen(server);
    int addr_len = 0;
    for(int i = 0; i < n; i++)
    {
        if(server[i] == ':')
        {
            addr_len = i;
            break;
        }
    }
    *address = malloc(addr_len + 1);
    strncpy(*address, server, addr_len);
    (*address)[addr_len] = '\0';
    *port = atoi(server + addr_len + 1);
    return 0;
}

int kv739_init(char **server_list)
{
    num_server = 0;
    int max_server = 128;
    socket_list = malloc(max_server*sizeof(int));
    while(*server_list != NULL)
    {
        printf(*server_list);
        struct sockaddr_in serv_addr;
        char* server = *server_list;
        int tcp_socket = socket(AF_INET, SOCK_STREAM, 0);

        char *address;
        int port;
        split(server, &address, &port);
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port); 
        
        // Convert IPv4 and IPv6 addresses from text to binary form 
        if(inet_pton(AF_INET, address, &serv_addr.sin_addr)<=0)  
        { 
            printf("\nInvalid address/ Address not supported \n"); 
            return -1; 
        } 

        if(tcp_socket < 0)
        {
            printf("\n Socket creation error \n");
            server_list = server_list + 1;
            continue;
        }
        if (connect(tcp_socket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
        { 
            printf("\nConnection Failed \n"); 
            server_list = server_list + 1;
            continue; 
        } 
        socket_list[num_server++] = tcp_socket;
        if(num_server >= max_server)
        {
            max_server *= 2;
            server_list = realloc(server_list, max_server*sizeof(int));
        }
        server_list = server_list + 1;
    }
}

int kv739_get(char * key, char * value)
{
    int latest = 0;
    int rtn = 0;
    char *buf = malloc(8192);
    for(int i = 0; i < num_server; i++)
    {
        memset(buf, 0, 8192);
        struct packet pkt;
        pkt.optype = 0;
        strcpy(pkt.key, key);
        encode(&pkt, buf);
        send(socket_list[i] , buf , 8192 , 0); 
        int rtn = read(socket_list[i] , buf, 8192);
        decode(&pkt, buf);
        if (pkt.time > latest)
        {
            strcpy(value, pkt.value);
            rtn = 1 - pkt.has_val;
        }
    }
    free(buf);
    return rtn;
}
int kv739_put(char * key, char * value, char * old_value)
{
    int latest = 0;
    int rtn = 0;
    char *buf = malloc(8192);
    for(int i = 0; i < num_server; i++)
    {
        memset(buf, 0, 8192);
        struct packet pkt;
        pkt.optype = 1;
        pkt.time = time(NULL);
        strcpy(pkt.key, key);
        strcpy(pkt.value, value);
        encode(&pkt, buf);
        send(socket_list[i] , buf , 8192 , 0); 
        int rtn = read(socket_list[i] , buf, 8192);
        decode(&pkt, buf);
        if (pkt.time > latest)
        {
            strcpy(old_value, pkt.old_value);
            rtn = 1 - pkt.has_old_val;
        }
    }
    free(buf);
    return rtn;
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