
#include <sys/types.h>          /* See NOTES */
#include <sys/socket.h>
#include <stdlib.h>
#include <arpa/inet.h> 
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <stdio.h>
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
int num_partition;
int num_replica;
int* socket_list;
struct timeval timeout;


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

int print_packet(struct packet* pkt)
{
    printf("%d, %d, %d, %c, %c, %s, %s, %s\n",
        pkt->optype, pkt->time, pkt->return_value, pkt->has_old_val, pkt->has_val, pkt->key, pkt->value, pkt->old_value
    );
}

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
    *n = bytes[0] + (bytes[1] << 8) + (bytes[2] << 16) + (bytes[3] << 24);
}

int encode(struct packet* pkt, char* str)
{
    encode_int(str, pkt -> optype);
    encode_int(str+4, pkt -> time);
    encode_int(str+8, 0);
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
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;

    while(*server_list != NULL)
    {
        struct sockaddr_in serv_addr;
        char* server = *server_list;
        int tcp_socket = socket(AF_INET, SOCK_STREAM, 0);

        char *address;
        int port;
        split(server, &address, &port);
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port); 
        
        if (setsockopt (tcp_socket, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout,
                    sizeof(timeout)) < 0)
            printf("setsockopt failed\n");

        if (setsockopt (tcp_socket, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout,
                    sizeof(timeout)) < 0)
            printf("setsockopt failed\n");

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
    int latest = -2147483648;
    int rtn = 0;
    char *buf = malloc(8192);
    for(int i = 0; i < num_server; i++)
    {
        int retry = 0;
        int sent = 0;
        memset(buf, 0, 8192);
        struct packet pkt;
        pkt.optype = 0;
        strcpy(pkt.key, key);
        memset(pkt.value, 0, 2048);
        memset(pkt.old_value, 0, 2048);
        encode(&pkt, buf);
        while((sent = send(socket_list[i] , buf , 8192 , 0)) != 8192)
        {
            printf("Sent not complete, retry: %d\n", retry + 1);
            if (retry++ >= 2 || sent < 0)
                break;
        }
        if (sent != 8192)
            continue;
        int rtn = read(socket_list[i] , buf, 8192);
        decode(&pkt, buf);
        // print_packet(&pkt);
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
    int latest = -2147483648;
    int rtn = 0;
    char *buf = malloc(8192);
    for(int i = 0; i < num_server; i++)
    {
        int retry = 0;
        int sent = 0;
        memset(buf, 0, 8192);
        struct packet pkt;
        pkt.optype = 1;
        pkt.time = time(NULL);
        strcpy(pkt.key, key);
        strcpy(pkt.value, value);
        memset(pkt.old_value, 0, 2048);
        encode(&pkt, buf);
        
        while((sent = send(socket_list[i] , buf , 8192 , 0)) != 8192)
        {
            printf("Sent not complete, retry: %d\n", retry + 1);
            if (retry++ >= 2 || sent < 0)
                break;
        }
        if (sent != 8192)
            continue;
        int rtn = read(socket_list[i] , buf, 8192);
        decode(&pkt, buf);
        // print_packet(&pkt);
        if (pkt.time > latest)
        {
            strcpy(old_value, pkt.old_value);
            rtn = 1 - pkt.has_old_val;
        }
    }
    free(buf);
    return rtn;
}