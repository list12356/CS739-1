
#include <sys/types.h>          /* See NOTES */
#include <sys/socket.h>
#include <stdlib.h>
#include <arpa/inet.h> 
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <sys/time.h>
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
struct timeval tv;

//TODO: use enum to represent optype

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
    printf("%d, %d, %d, %d, %d, ",
        pkt->optype, pkt->time, pkt->return_value, pkt->has_old_val, pkt->has_val);
        if (pkt->key)
            printf("%s, ", pkt->key);
        if (pkt->value)
            printf("%s, ", pkt->value);
        if (pkt->old_value)
            printf("%s\n", pkt->old_value);
}

int init_packet(struct packet* pkt)
{
    pkt->optype = 0;
    pkt->time = 0;
    pkt->return_value = 0;
    pkt->has_old_val = 0;
    pkt->has_val = 0;
    // pkt->key = malloc(128);
    memset(pkt->key, 0, 128);
    // pkt->value = malloc(2048);
    memset(pkt->value, 0, 2048);
    // pkt->old_value = malloc(2048);
    memset(pkt->old_value, 0, 2048);
}

int release_packet(struct packet* pkt)
{
    free(pkt->key);
    free(pkt->value);
    free(pkt->old_value);
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

/*
TODO: this function does not tolerate any error in the message.
*/
int decode(struct packet* pkt, char* str)
{
    decode_int(str, &pkt -> optype);
    decode_int(str+4, &pkt -> time);
    decode_int(str+8, &pkt -> return_value);
    pkt -> has_old_val = str[12]; 
    pkt -> has_val = str[13];
    strcpy(pkt -> key, str + 128);
    strcpy(pkt -> value, str + 256);
    strcpy(pkt -> old_value, str + 2304);
}

int split_port(char* server, char** address, int* port)
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

char** fetch_server(char** init_list)
{
    char *buf = malloc(8192);
    int sent = 0;
    int num_read = 0;
    char **server_list = NULL;
    struct packet pkt;
    init_packet(&pkt);

    for(;*init_list != NULL; init_list++)
    {
        struct sockaddr_in serv_addr;
        char* init_server = *init_list;
        int tcp_socket = socket(AF_INET, SOCK_STREAM, 0);

        char *address;
        int port;
        split_port(init_server, &address, &port);
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port); 
        
        if (setsockopt (tcp_socket, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout,
                    sizeof(timeout)) < 0)
        {
            printf("setsockopt failed\n");
            close(tcp_socket);
            continue;
        }

        if (setsockopt (tcp_socket, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout,
                    sizeof(timeout)) < 0)
        {
            printf("setsockopt failed\n");
            close(tcp_socket);
            continue;
        }

        // Convert IPv4 and IPv6 addresses from text to binary form 
        if(inet_pton(AF_INET, address, &serv_addr.sin_addr)<=0)  
        { 
            printf("\nInvalid address/ Address not supported \n");
            close(tcp_socket);
            continue;
        } 

        if(tcp_socket < 0)
        {
            printf("\n Socket creation error \n");
            close(tcp_socket);
            continue;
        }
        if (connect(tcp_socket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
        { 
            printf("\nConnection Failed \n"); 
            close(tcp_socket);
            continue; 
        }
        memset(buf, 0, 8192);
        pkt.optype = 2;
        encode(&pkt, buf);
        sent = send(tcp_socket , buf , 8192 , 0);
        if (sent != 8192)
        {
            printf("Sent not complete, skip.\n");
            close(tcp_socket);
            continue;
        }
        num_read = read(tcp_socket , buf, 8192);
        if (num_read < 0)
        {
            close(tcp_socket);
        }
        decode(&pkt, buf);
        
        num_server = pkt.return_value;
        if (num_server == 0)
        {
            close(tcp_socket);
            continue;
        }
        // start delemilite the serverlist
        server_list = malloc((num_server + 1)*sizeof(char*));
        int n = strlen(pkt.value);
        int offset = 0;
        int m = 0;
        for(int i = 0; i < n; i++)
        {
            if (pkt.value[i] == ';')
            {
                server_list[m] = malloc(64);
                strncpy(server_list[m], pkt.value + offset, i - offset);
                offset = i + 1;
                m++;
            }
        }
        if (offset < n)
        {
            server_list[m] = malloc(64);
            strncpy(server_list[m++], pkt.value + offset, n - offset);
        }
        server_list[num_server] = NULL;
        // server number does not match the delimilited 
        if (num_server != m)
        {
            fprintf(stderr, "Error: Received number of server does not match");
        }
        //release_packet(&pkt);
        close(tcp_socket);
        break;
    }
    return server_list;
}

int kv739_init(char **init_list)
{
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    char** server_list = fetch_server(init_list);
    if (server_list == NULL || num_server == 0)
        return -1;
    socket_list = malloc(num_server*sizeof(int));



    for(int i = 0; i < num_server; i++)
    {
        struct sockaddr_in serv_addr;
        char* server = server_list[i];
        int tcp_socket = socket(AF_INET, SOCK_STREAM, 0);

        char *address;
        int port;
        split_port(server, &address, &port);
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
            continue; 
        } 

        if(tcp_socket < 0)
        {
            printf("\n Socket creation error \n");
            continue;
        }
        if (connect(tcp_socket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
        { 
            printf("\nConnection Failed on %s\n", server); 
            continue; 
        } 
        socket_list[i] = tcp_socket;
    }
}

int kv739_shutdown(void)
{
    for(int i = 0; i < num_server; i++)
    {
        close(socket_list[i]);
    }
    if (socket_list != NULL)
    {
        free(socket_list);
    }
    socket_list = NULL;
    num_server = 0;
}

int kv739_get(char * key, char * value)
{
    int latest = -2147483648;
    int rtn = 0;
    int num_read = 0;
    char *buf = malloc(8192);
    struct packet pkt;
    init_packet(&pkt);
    for(int i = 0; i < num_server; i++)
    {
        int retry = 0;
        int sent = 0;
        memset(buf, 0, 8192);
        pkt.optype = 0;
        strcpy(pkt.key, key);
        encode(&pkt, buf);
        while((sent = send(socket_list[i] , buf , 8192 , 0)) != 8192)
        {
            printf("Sent not complete, retry: %d\n", retry + 1);
            if (retry++ >= 2 || sent < 0)
                break;
        }
        if (sent != 8192)
            continue;
        num_read = read(socket_list[i] , buf, 8192);
        if (num_read < 0)
            continue;
        decode(&pkt, buf);
        // print_packet(&pkt);
        if (pkt.time > latest)
        {
            strcpy(value, pkt.value);
            latest = pkt.time;
            rtn = 1 - pkt.has_val;
        }
    }
    free(buf);
    // release_packet(&pkt);
    return rtn;
}
int kv739_put(char * key, char * value, char * old_value)
{
    int latest = -2147483648;
    int rtn = 0, num_read = 0;
    char *buf = malloc(8192);
    struct packet pkt;
    init_packet(&pkt);
    for(int i = 0; i < num_server; i++)
    {
        int retry = 0;
        int sent = 0;
        memset(buf, 0, 8192);
        pkt.optype = 1;
        gettimeofday(&tv, NULL);
        pkt.time = time(NULL) % 10000000 *100 +  (int)(tv.tv_usec) / 10000 % 100;
        strcpy(pkt.key, key);
        strcpy(pkt.value, value);
        encode(&pkt, buf);
        
        while((sent = send(socket_list[i] , buf , 8192 , 0)) != 8192)
        {
            printf("Sent not complete, retry: %d\n", retry + 1);
            if (retry++ >= 2 || sent < 0)
                break;
        }
        if (sent != 8192)
            continue;
        num_read = read(socket_list[i] , buf, 8192);
        if (num_read < 0)
            continue;
        decode(&pkt, buf);
        //print_packet(&pkt);
        if (pkt.time > latest)
        {
            strcpy(old_value, pkt.old_value);
            rtn = 1 - pkt.has_old_val;
        }
    }
    // release_packet(&pkt);
    free(buf);
    return rtn;
}

