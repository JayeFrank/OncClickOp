from selenium.common import TimeoutException
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
import time
import json
logging.basicConfig(level=logging.DEBUG)
service = Service(r"D:\wDriver\msedgedriver.exe")
options = Options()
logging.debug("Starting Edge WebDriver")
driver = webdriver.Edge(service=service, options=options)
logging.debug("Edge WebDriver started successfully")
driver.get('https://creator.xiaohongshu.com/login')
logging.debug("Page opened successfully")
print(driver.title)
driver.set_window_size(1400,900)
wait_flag = 1

while(wait_flag):
    try:
        if WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.XPATH, "//div[@class='personal']"))):
        # 3. 将登录后的cookies保存到本地文件
            with open("D:/myCook.txt", "w", encoding="utf8") as f:
                f.write(json.dumps(driver.get_cookies(), indent=4, ensure_ascii=False))
            wait_flag = 0
            time.sleep(5)
            break   
    except TimeoutException:
        print("登录超时，请检查网络或手动登录后重试。")
        driver.quit()
        exit()