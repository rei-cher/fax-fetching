import time, random, os
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# USERNAME="agent-14@dkdermgroup.com"
# PASSWORD="Weave2024"
# URL="https://app.getweave.com"

# ======= laod env variable ==========
load_dotenv()

# ======= setting up driver ==========
options = uc.ChromeOptions()
# user agent and additional arguents to bypass bot detection
options.add_argument("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = uc.Chrome(options=options)


# ======= open login page and login =======
driver.get(os.getenv("URL"))
# driver.get(URL)
time.sleep(5)
# ======= fill username and password fields ========
driver.find_element(By.NAME, "username").send_keys(os.getenv("USERNAME_ENV"))
driver.find_element(By.NAME, "password").send_keys(os.getenv("PASSWORD_ENV"))

# ======= login =======
driver.execute_script("arguments[0].click()" ,driver.find_element(By.XPATH, "//button[@type='submit']"))

# ====== select faxes ========
time.sleep(10)
try:
    driver.execute_script("arguments[0].click()" ,driver.find_element(By.XPATH, "//button[span[text()='Fax']]"))
except Exception as e:
    print(f"Error clicking or locating the fax: {e}")


# ======= iterating over the faxes =======
try:
    faxes = driver.find_elements(By.XPATH, "//div[@class='frontend-i3urgv']")
    print(len(faxes))
    # for fax in faxes[:2]:
    #     print(fax.get_attribute("outerHTML"))
except Exception as e:
    print(f"Error clicking or locating the fax: {e}")

while True:
    time.sleep(1)