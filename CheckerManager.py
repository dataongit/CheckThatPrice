import os
import requests
import random
from parsers.jpc_parser import JPC
from parsers.amazonde_parser import AmazonDE
import json
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
from babel import numbers
import simple_useragent as sua

load_dotenv()

SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_USERNAME = os.environ["SMTP_USERNAME"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

def send(msg, sender_email, debug=False):
    if debug:
        with smtplib.SMTP("localhost", 8025) as server:
            server.send_message(msg)

    else:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            SMTP_SERVER, SMTP_PORT, context=context
        ) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)


class Manager:

    sender_email = os.environ["SENDER_EMAIL"]
    receiver_email = os.environ["RECEIVER_EMAIL"]

    def __init__(self, jpcChecker: JPC = None, amazonChecker: AmazonDE = None) -> None:

        self._jpcChecker = jpcChecker or JPC()
        self._amazonChecker = amazonChecker or AmazonDE()

        # Registry of vendor name -> parser. Add a new webpage by writing a
        # parser with a `name` attribute and listing it here - no new
        # branching logic needed in requestProcess.
        self._checkers = {
            checker.name: checker
            for checker in (self._jpcChecker, self._amazonChecker)
        }


    def requestProcess(self, data: dict) -> None:
        for product in data["products"]:
            for vendor in product["vendors"]:
                checker = self._checkers.get(vendor["name"])
                if checker is None:
                    continue

                randomAgent = sua.get_list(shuffle=True, force_cached=True)
                headers = {'User-Agent': self.user_agents[randomAgent]}
                request = requests.get(vendor["url"], headers=headers)
                price = checker.parseData(request.text)
                print(price)
                if vendor["price"] > float(price):
                    self._sendPriceEmail(checker.name, product["name"], price, vendor["url"], vendor["currency"])
                    self.update_price(checker.name, product["name"], price)
                elif vendor["price"] < float(price):
                    self._sendPriceEmail(checker.name, product["name"], price, vendor["url"], vendor["currency"])
                    self.update_price(checker.name, product["name"], price)
                elif price == "":
                    pass

    def _sendPriceEmail(self, vendor_name: str, product_name: str, price: str, url: str, currency: str) -> None:
        msg = EmailMessage()
        msg["to"] = self.receiver_email
        msg["from"] = self.sender_email
        msg["subject"] = f"{vendor_name} Price Change"
        msg.set_content(f"""For the product {product_name} the price is now: {numbers.get_currency_symbol(currency=currency)} {price} \r\n 
        Link: {url}""")
        send(msg, self.sender_email)

    def update_price(self, vendor_name: str, product_name: str, price: str):
        with open("list.json", mode="r+") as f:
            data = json.load(f)
            for product in data["products"]:
                if product["name"] == product_name:
                    for vendor in product["vendors"]:
                        if vendor["name"] == vendor_name:
                            vendor["price"] = float(price)
            f.seek(0)
            f.truncate(0)
            json.dump(data, fp=f)