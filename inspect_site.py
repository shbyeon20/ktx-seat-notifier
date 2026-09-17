"""사이트 구조 확인용 1회성 스크립트. 출발역 클릭 시 뜨는 모달 구조를 확인한다."""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

options = Options()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://www.korail.com/ticket/search/general#")
time.sleep(10)

date_btn = driver.find_element(By.CSS_SELECTOR, "a.btn_d-day")
date_btn.click()
time.sleep(2)

# 18일(내일, 같은 달) 클릭
day_link = driver.find_element(By.XPATH, "//a[normalize-space(.)='18']")
day_link.click()
time.sleep(1)
driver.save_screenshot("screenshot_after_day.png")
with open("page_source_after_day.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

time_next_btns = driver.find_elements(By.XPATH, "//button[contains(@class,'slick-next')]")
print("slick-next buttons:", len(time_next_btns))
time_next = time_next_btns[-1]  # 시간선택 캐러셀의 next 버튼 (달력 next는 index 0)

for _ in range(5):
    hour_links = driver.find_elements(By.XPATH, "//a[contains(text(),'시') and @aria-disabled='false']")
    texts = [h.text.strip() for h in hour_links]
    print("selectable hours now:", texts)
    match = [h for h in hour_links if h.text.strip() == "09시"]
    if match:
        driver.execute_script("arguments[0].click();", match[0])
        break
    driver.execute_script("arguments[0].click();", time_next)
    time.sleep(1)

time.sleep(1)
header = driver.find_element(By.CSS_SELECTOR, "div.con_Wrap a")
print("header after hour select:", header.text)

apply_btn = driver.find_element(By.XPATH, "//button[contains(@class,'btn_bn-blue') and text()='적용']")
apply_btn.click()
time.sleep(2)

date_field = driver.find_element(By.ID, "startDate")
print("startDate field value after apply:", date_field.get_attribute("value"))

lookup_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_lookup")
lookup_btn.click()
time.sleep(5)

with open("page_source_result.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

total_height = driver.execute_script("return document.body.scrollHeight")
print("scrollHeight:", total_height)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
time.sleep(1)
driver.save_screenshot("screenshot_result_mid.png")
driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
time.sleep(1)
driver.save_screenshot("screenshot_result.png")

print("searched, saved result state. current url:", driver.current_url)
time.sleep(2)
driver.quit()
