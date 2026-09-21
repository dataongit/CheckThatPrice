from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class EbayDE:
    name = "Ebay DE"

    def parseData(self, driver: WebDriver) -> str:
        price = WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".x-price-primary__price .ux-textspans")
            )
        ).text

        return price.replace(",",".").replace("EUR", "")