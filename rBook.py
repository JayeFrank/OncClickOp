import json
import logging
import time
import pathlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VIDEO_PATH = r"F:\deskkkk\2222.MP4"
COOKIE_FILE = r"D:\myCook.txt"
EDGE_DRIVER_PATH = r"D:\wDriver\msedgedriver.exe"
PUBLISH_URL    = "https://creator.xiaohongshu.com/publish/publish"
TITLE_TEXT     = "测试测试测试标题"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

service = Service(EDGE_DRIVER_PATH)
options = Options()
logging.info("Starting Edge WebDriver")
driver = webdriver.Edge(service=service, options=options)
logging.info("Edge WebDriver started successfully")

driver.set_window_size(1400,900)

driver.get("https://creator.xiaohongshu.com")
# 读取本地的Cookies文件，加载到driver
with open(COOKIE_FILE, encoding="utf8") as f:
    cookies = json.loads(f.read())
    for cookie in cookies:
        driver.add_cookie(cookie)
    logger.info(f"Loaded {len(cookies)} cookies")
# 进入创作者页面，并上传视频
driver.get(PUBLISH_URL)

wait = WebDriverWait(driver, 12)
file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
file_input.send_keys(str(VIDEO_PATH))
logger.info("Video selected for upload")

try:
    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, '//*[contains(text(),"上传成功")]'), "上传成功"
    ))
    logger.info("上传成功")
except Exception:
    logger.error("视频还在上传中···")
    driver.quit()
    raise
# 填写标题  d-text
# 输入标题
title_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@class,"d-text")]')))
title_input.send_keys(TITLE_TEXT)
logger.info("标题已输入")
time.sleep(2)
# 点击发布
publish_btn = wait.until(EC.presence_of_element_located((
    By.CSS_SELECTOR,
    "button.publishBtn"
    )))
wait.until(lambda drv: publish_btn.is_enabled())
publish_btn.click()
logger.info("点击发布")

wait.until(EC.url_contains("/publish/success"))
success_url = driver.current_url
logger.info(f"成功发布, landed on: {success_url}")
time.sleep(5)
driver.quit()