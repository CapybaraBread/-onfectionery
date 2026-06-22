import json
import os
import re
import smtplib
from datetime import datetime
from email.message import EmailMessage
from http.server import HTTPServer, SimpleHTTPRequestHandler

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

        password = os.environ.get("GMAIL_APP_PASSWORD")
        if not password:
            self.send_json(503, {"ok": False, "message": "На сервере не настроена отправка почты"})
            return

        message = EmailMessage()
        message["Subject"] = "Новая заявка с сайта Сладкий сундук"
        message["From"] = EMAIL
        message["To"] = EMAIL
        message.set_content(
            "Номер телефона: {}\nТовар: {}\nДата: {}".format(
                phone,
                product,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
            )
        )

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
                smtp.login(EMAIL, password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            print(
                "Ошибка Gmail SMTP: {}: {}".format(type(error).__name__, error),
                flush=True,
            )
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
