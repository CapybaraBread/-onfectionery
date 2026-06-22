import json
import os
import re
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from jinja2 import Environment, FileSystemLoader
from openpyxl import load_workbook


EMAIL = "denis05102012@gmail.com"
excel = load_workbook("site_data.xlsx", data_only=True)


def read_sheet(name):
    rows = list(excel[name].values)
    return [dict(zip(rows[0], row)) for row in rows[1:]]


settings = {row["key"]: row["value"] for row in read_sheet("settings")}
template = Environment(loader=FileSystemLoader("templates")).get_template("index.html")
html = template.render(
    settings=settings,
    products=read_sheet("products"),
    reviews=read_sheet("reviews"),
    gallery=read_sheet("gallery"),
    footer_links=read_sheet("footer_links"),
)

with open("index.html", "w", encoding="utf-8") as file:
    file.write(html)


class SiteHandler(SimpleHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/send-phone":
            self.send_json(404, {"ok": False, "message": "Страница не найдена"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            self.send_json(400, {"ok": False, "message": "Некорректные данные формы"})
            return

        phone = str(data.get("phone", "")).strip()
        consent = data.get("consent") is True
        product = str(data.get("product", "")).strip() or "Не выбран"

        if not consent:
            self.send_json(400, {"ok": False, "message": "Необходимо согласие на обработку данных"})
            return
        if not re.fullmatch(r"[+0-9 ()-]{7,25}", phone):
            self.send_json(400, {"ok": False, "message": "Введите корректный номер телефона"})
            return

        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            self.send_json(503, {"ok": False, "message": "На сервере не настроена отправка почты"})
            return

        email_data = json.dumps(
            {
                "from": "Сладкий сундук <onboarding@resend.dev>",
                "to": [EMAIL],
                "subject": "Новая заявка с сайта Сладкий сундук",
                "text": "Номер телефона: {}\nТовар: {}\nДата: {}".format(
                    phone,
                    product,
                    datetime.now().strftime("%d.%m.%Y %H:%M"),
                ),
            }
        ).encode("utf-8")
        request = Request(
            "https://api.resend.com/emails",
            data=email_data,
            headers={
                "Authorization": "Bearer {}".format(api_key),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=15) as response:
                response.read()
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            print("Ошибка Resend API {}: {}".format(error.code, details), flush=True)
            self.send_json(502, {"ok": False, "message": "Не удалось отправить письмо. Попробуйте позже"})
            return
        except (OSError, URLError) as error:
            print("Ошибка подключения к Resend: {}".format(error), flush=True)
            self.send_json(502, {"ok": False, "message": "Не удалось отправить письмо. Попробуйте позже"})
            return

        self.send_json(200, {"ok": True, "message": "Спасибо! Мы скоро вам перезвоним"})


print("index.html создан")
try:
    server = HTTPServer(("0.0.0.0", 8000), SiteHandler)
    print("Сайт запущен: http://127.0.0.1:8000")
    server.serve_forever()
except OSError:
    print("Порт 8000 уже занят. Остановите старый сервер командой Ctrl+C")
except KeyboardInterrupt:
    print("\nСервер остановлен")
