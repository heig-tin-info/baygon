CSRCS=$(wildcard *.c)
COBJS=$(patsubst %.c,%.o,$(CSRCS))
EXEC=a.out

CFLAGS=-std=c99 -g -Wall -pedantic

all: $(EXEC)

$(EXEC): $(COBJS)
	$(CC) $^ -o$@ $(LDFLAGS)

clean:
	$(RM) $(EXEC) *.o

.PHONY: test all format build
