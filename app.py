from selenium import webdriver
from selenium.webdriver.common.by import By
from base64 import b64decode
import re


driver = webdriver.Firefox()

### Captcha Page

driver.get("https://service2.diplo.de/rktermin/extern/appointment_showMonth.do?locationCode=amst&realmId=1113&categoryId=2662")

# save captcha
captcha = driver.find_element(By.CSS_SELECTOR, "captcha div")
captcha_image_data = re.search("url\(\"data:image/jpg;base64,(.*)\"\)", captcha.value_of_css_property("background")).group(1)
with open("captcha.jpg", "wb") as img:
    img.write(b64decode(captcha_image_data))



# end
driver.quit()
