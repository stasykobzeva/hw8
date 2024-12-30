from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from requests import get, put
import os
import urllib.parse
import json

token = input("Введите oAuth-токен: ")

def run(handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8010)
    httpd = HTTPServer(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def get_uploaded_files(self):
        resp = get(
            "https://cloud-api.yandex.net/v1/disk/resources?path=Uploads",
            headers={"Authorization": f"OAuth {token}"}
        )
        if resp.status_code == 200:
            data = json.loads(resp.text)
            embedded = data.get('_embedded')
            items = embedded.get('items', []) if embedded else []
            return {urllib.parse.unquote(item['name']) for item in items}
        return set()

    def do_GET(self):
        uploaded_files = self.get_uploaded_files()

        def fname2html(fname):
            color = "rgba(0, 200, 0, 0.25)" if fname in uploaded_files else "white"
            return f"""
                <li style="background-color: {color};"
                onclick="fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})">
                    {fname}
                </li>
            """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
            <html>
                <head>
                </head>
                <body>
                    <ul>
                {files} 
                    </ul>
                </body>
            </html>
        """.format(files="\n".join(map(fname2html, os.listdir("pdfs")))).encode())

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        fname = self.rfile.read(content_len).decode("utf-8")
        local_path = f"pdfs/{fname}"
        ya_path = f"Uploads/{urllib.parse.quote(fname)}"
        resp = get(f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={ya_path}",
                headers={"Authorization": f"OAuth {token}"})
        print(resp.text)
        upload_url = json.loads(resp.text)["href"]
        print(upload_url)
        resp = put(upload_url, files={'file': (fname, open(local_path, 'rb'))})
        print(resp.status_code)
        self.send_response(200)
        self.end_headers()


run(handler_class=HttpGetHandler)