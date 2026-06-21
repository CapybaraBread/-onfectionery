from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader
from openpyxl import load_workbook


excel = load_workbook("site_data.xlsx", data_only=True)


def read_sheet(name):
    rows = list(excel[name].values)
    return [dict(zip(rows[0], row)) for row in rows[1:]]


settings = {row["key"]: row["value"] for row in read_sheet("settings")}

template = Environment(loader=FileSystemLoader("templates")).get_template("index.html.j2")
html = template.render(
    settings=settings,
    products=read_sheet("products"),
    reviews=read_sheet("reviews"),
    gallery=read_sheet("gallery"),
    footer_links=read_sheet("footer_links"),
)

with open("index.html", "w", encoding="utf-8") as file:
    file.write(html)

print("index.html создан")

try:
    server = HTTPServer(("0.0.0.0", 8000), SimpleHTTPRequestHandler)
    print("Сайт запущен: http://127.0.0.1:8000")
    server.serve_forever()
except OSError:
    print("Порт 8000 уже занят. Сайт уже запущен: http://127.0.0.1:8000")
except KeyboardInterrupt:
    print("\nСервер остановлен")
