from bs4 import BeautifulSoup

class AmazonDE:
    name = "Amazon DE"

    def parseData(self, data: str) -> str:
        parseddata = BeautifulSoup(data, "html.parser")
        price = parseddata.select_one(".a-price-whole")
        decimal = parseddata.select_one(".a-price-fraction")
        print(price)
        print(decimal)
        return price.get_text(strip=True).replace(".", "") + "." + decimal.get_text(strip=True)