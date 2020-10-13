#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc != 2 + 1) return 1;
    if (strcmp(argv[1], "--version") == 0) {
        printf("Version 0.1.1\n");
        return 0;
    }
    printf("%d", atoi(argv[1]) + atoi(argv[2]));
}
