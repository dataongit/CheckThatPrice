import os
from parsers.jpc_parser import JPC
from parsers.amazonde_parser import AmazonDE
from parsers.ebayde_parser import EbayDE
import json
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
from babel import numbers
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

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

    def __init__(self, jpcChecker: JPC = None, amazonChecker: AmazonDE = None, ebayChecker : EbayDE = None) -> None:

        self._jpcChecker = jpcChecker or JPC()
        self._amazonChecker = amazonChecker or AmazonDE()
        self._ebayChecker = ebayChecker or EbayDE()
        # Registry of vendor name -> parser. Add a new webpage by writing a
        # parser with a `name` attribute and listing it here - no new
        # branching logic needed in requestProcess.
        self._checkers = {
            checker.name: checker
            for checker in (self._jpcChecker, self._amazonChecker, self._ebayChecker)
        }


    def requestProcess(self, data: dict) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)
        try:
            for product in data["products"]:
                for vendor in product["vendors"]:
                    checker = self._checkers.get(vendor["name"])
                    if checker is None:
                        continue

                    try:
                        driver.get(vendor["url"])
                        price = checker.parseData(driver)
                    except TimeoutException:
                        print(f"Could not find a price: {vendor['url']}")
                        continue

                    if float(vendor["price"]) != float(price):
                        self._sendPriceEmail(
                        checker.name,
                        product["name"],
                        price,
                        vendor["url"],
                        vendor["currency"],
                        )
                        self.update_price(
                        checker.name, product["name"], price
                        )
        finally:
            driver.quit()

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