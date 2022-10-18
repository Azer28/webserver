import queue
import socket
import select

def start():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8000))
    server_socket.listen(5)

    client_conns = []
    outputs = []
    client_conns.append(server_socket)
    message_queues = {}

    while True:
        # import time
        # time.sleep(360)
        # conn, addr = server_socket.accept()
        # client_conns.append(conn)
        print("calling select")
        read_ready, write_ready, exc_ready = select.select(client_conns, outputs, [])

        print("select is called", read_ready, len(read_ready))
        for x in read_ready:
            if x is server_socket:
                connection, addr = x.accept()
                client_conns.append(connection)
                message_queues[connection] = queue.Queue()
            else:
            # print(x is server_socket)
                data = x.recv(100)
                print(data, len(data))
                if data:
                    message_queues[connection].put(data.decode("utf-8"))
                    if x not in outputs:
                        pass
                        # outputs.append(x)
                else:
                    client_conns.remove(connection)
                    while not message_queues[connection].empty():
                        print(message_queues[connection].get())
                    # print("no data for", x)


if __name__ == "__main__":
    start()

