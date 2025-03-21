import time, random, os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def extract_token(username: str, password: str, url: str):

    # ======= setting up driver ==========
    options = uc.ChromeOptions()
    # user agent and additional arguents to bypass bot detection
    options.add_argument("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_experimental_option("detach", True)

    driver = uc.Chrome(use_subprocess=True, options=options)


    # ======= open login page and login =======
    driver.get(url)
    # driver.get(URL)
    time.sleep(5)
    # ======= fill username and password fields ========
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)

    # ======= login =======
    driver.execute_script("arguments[0].click()" ,driver.find_element(By.XPATH, "//button[@type='submit']"))

    time.sleep(10)
    localStorage = driver.execute_script(
        """
            var items = {};
            for (var i = 0; i < localStorage.length; i++) {
                items[localStorage.key(i)] = localStorage.getItem(localStorage.key(i));
            }
            return items;
        """
    )

    token = localStorage["token"]
    if token:
        return token