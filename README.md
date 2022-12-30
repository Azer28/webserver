# Web server

This script allows to run http webserver which processes GET and HEAD http requests. Basically it responses with the requested files in the root directory
--------

### Usage

run the webserver
```bash
python httpd.py -w 4
```
-w N - number of OS processes which handle socket requests
```bash
python httpd.py -w 3 -r custom_directory_path
```
-r Directory_root - directory where to search for the reuqested files. Defaultn value `storage`

### Webserver architecture

Webserver is based on the event-driver architecture. It uses epoll selector and its interface. All sockets are nonblocking

Running webserver was tested using:
- Python 3.8

No additional python package is required
