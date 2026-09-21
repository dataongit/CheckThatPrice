from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AmazonDE:
    name = "Amazon DE"

    def parseData(self, driver: WebDriver) -> str:
        price = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".a-price")
            )
        )

        # Read both parts from the same price container.
        wait = WebDriverWait(price, 15)
        whole = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".a-price-whole")
            )
        ).text
        fraction = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".a-price-fraction")
            )
        ).text

        whole = "".join(char for char in whole if char.isdigit())
        return f"{whole}.{fraction.strip()}"