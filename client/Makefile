# CC=gcc
# FLAGS=-I/usr/include/python3.6m -I/usr/include/python3.6m  -Wno-unused-result -Wsign-compare -g -fdebug-prefix-map=/build/python3.6-lEonRF/python3.6-3.6.8=. -specs=/usr/share/dpkg/no-pie-compile.specs -fstack-protector -Wformat -Werror=format-security  -DNDEBUG -g -fwrapv -O3 -Wall -fPIC
# LDFLAGS=-L/usr/lib/python3.6/config-3.6m-x86_64-linux-gnu -L/usr/lib -lpython3.6m -lpthread -ldl  -lutil -lm  -Xlinker -export-dynamic -Wl,-O1 -Wl,-Bsymbolic-functions

# client: client.o
# 	$(CC) client.o  -o client $(LDFLAGS)

# client.o: client.c
# 	$(CC) $(FLAGS) -c client.c

CC=gcc
FLAGS=-fPIC -Wall

all:test lib739kv.so

test:unittest.o client.o
	$(CC) $^ -o $@ 

client.o: client.c
	$(CC) $(FLAGS) -c client.c

lib739kv.so:client.o
	$(CC) -shared $< -o $@

unittest.o:unittest.c
	$(CC) -c $(FLAGS) $< -o $@

clean:
	rm -rf *.o *.so test