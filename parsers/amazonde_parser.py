from bs4 import BeautifulSoup

class AmazonDE:
    name = "Amazon DE"

    def parseData(self, data: str) -> str:
        parseddata = BeautifulSoup(data, "html.parser")
        price = parseddata.find("span", attrs={"id": "apex-pricetopay-accessibility-label"})
        return price.get_text(strip=True).replace("€", "")