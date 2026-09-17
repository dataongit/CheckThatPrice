from bs4 import BeautifulSoup

class JPC:
    name = "JPC"

    def parseData(self, data: str) -> str:
        parseddata = BeautifulSoup(data, "html.parser")
        price = parseddata.find("meta", attrs={"itemprop": "price"})
        return price["content"].strip()