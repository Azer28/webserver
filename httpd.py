import argparse
from multiprocessing import Pool
import socket
import select
import os

from request_handler import HTTPResponse, parse_request


DIRECTORY_ROOT = "storage"
HTTP_REQUEST_ENDER = b"\r\n\r\n"
SERVER_HOST = "localhost"
SERVER_PORT = 8000


def start_epoll(root_dir):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(0)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    
    epoll = select.epoll()
    epoll.register(server_socket.fileno(), select.EPOLLIN)
    # print("server_socket.fileno()", server_socket.fileno(), select.EPOLLIN, select.EPOLLOUT)
    connections = {}
    request_data = {}
    responses = {}

    while True:
        events = epoll.poll(1)
        # print(pid, events)
        for fileno, event in events:
            if fileno == server_socket.fileno():
                # print(pid, "server socket fileno", fileno, event)
                client_socket, address = server_socket.accept()
                client_socket.setblocking(0)
                epoll.register(client_socket, select.EPOLLIN)
                connections[client_socket.fileno()] = client_socket
                request_data[client_socket.fileno()] = bytearray()
            
            elif event & select.EPOLLIN:
                data = connections[fileno].recv(1024)
                request_data[fileno].extend(data)
                # print(pid, "data", fileno, data)
                if HTTP_REQUEST_ENDER in data:
                    # print("the end of the request. Stop reading")
                    http_request = parse_request(request_data[fileno])
                    resp = HTTPResponse(http_request).build_response(root_dir)
                    responses[fileno] = resp
                    epoll.modify(fileno, select.EPOLLOUT)
                    del request_data[fileno]

            elif event & select.EPOLLOUT:
                resp_data = responses.get(fileno)

                if resp_data:
                    sent = connections[fileno].send(resp_data)
                    responses[fileno] = resp_data[sent:]
                
                else:
                    epoll.unregister(fileno)
                    connections[fileno].close()
                    del connections[fileno]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-w", type=int)
    parser.add_argument("-r", type=str, default=DIRECTORY_ROOT)
    args = parser.parse_args()

    wrk_num = args.w
    dir_root = args.r  

    with Pool(processes=wrk_num) as pool:
        task_args = [dir_root] * wrk_num
        pool.map(start_epoll, task_args)
