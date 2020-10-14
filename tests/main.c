#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--version") == 0) {
        fprintf(stderr, "Version 0.1.1\n");
        return 0;
    }
    if (argc != 2 + 1) return 1;
    printf("%d", atoi(argv[1]) + atoi(argv[2]));
}
