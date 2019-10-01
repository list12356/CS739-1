# CS739-1
* Compile client libraray.
```bash
cd ./client/
make
```
* Move the compiled .so library to repo's root directory
```bash
cd TO_ROOT_OF_THIS_REPO
cp ./client/lib739kv.so .
```
* Excute the two bash scripts to run server and client programs

## Usage of Server
To run single server, run
```bash
python3 server/server.py PORT_NUMBER
```
where `PORT_NUMBER` is the port the server listen to.
To run batch of server, run the 
```bash
bash run_server.sh
```
where you need to specify the all the different ports the server listens in the bash file.
Also, you need to specify **all the complete address:ports** in `server_list` file. 
For example, you run 2 server listening to localhost:6666 localhost:7777, then your `run_server.sh` will be
```bash
python3 server/server.py 6666 &
python3 server/server.py 7777
```
and your `server_list will be
```
127.0.0.1:6666
127.0.0.1:7777
```

## Usage of test client
To test client performance, run `bash run_client.sh`. You also need to specify all the address and ports of the server available as all or a subset of these addresses will be passed to client's init method.
