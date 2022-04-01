from ftplib import error_reply
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from base64 import b64decode
from twocaptcha import TwoCaptcha
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from os import environ
from time import sleep
import re


TWOCAPTCHA_API_KEY = environ["TWOCAPTCHA_API_KEY"]
SENDGRID_API_KEY = environ["SENDGRID_API_KEY"]
NOTIFICATION_RECIPIENTS = environ["NOTIFICATION_RECIPIENTS"].split(":")


options = webdriver.FirefoxOptions()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)


last_checked_month = None
results = []

for year in range(2022, 2024):
    for month in range(1, 13):

        # load captcha page
        url = f"https://service2.diplo.de/rktermin/extern/appointment_showMonth.do?locationCode=amst&realmId=1113&categoryId=2662&dateStr=01.{str(month).zfill(2)}.{year}"
        driver.get(url)
        sleep(1)

        # check for captcha
        captchas = driver.find_elements(By.CSS_SELECTOR, "captcha div")
        if len(captchas):

            captcha_solved = False
            while captcha_solved == False:
                print("🔃 Solving Captcha... ", end="")

                # save captcha
                captcha = captchas[0]
                captcha_image_data = re.search("url\(\"data:image/jpg;base64,(.*)\"\)", captcha.value_of_css_property("background")).group(1)
                with open("captcha.jpg", "wb") as img:
                    img.write(b64decode(captcha_image_data))

                # solve captcha
                solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
                captcha_solution = solver.normal("captcha.jpg")

                # enter captcha
                field = driver.find_element(By.ID, "appointment_captcha_month_captchaText")
                field.clear()
                field.send_keys(captcha_solution["code"])
                field.send_keys(Keys.RETURN)
                sleep(5)

                # check captcha
                captcha_solved = True
                error_messages = driver.find_elements(By.ID, "message")
                if len(error_messages):
                    if "wrong" in error_messages[0].text:
                        captcha_solved = False

                print("done" if captcha_solved else "failed")

                # report captcha success
                solver.report(captcha_solution["captchaId"], captcha_solved)

        # check for appointments
        headers = driver.find_elements(By.CSS_SELECTOR, "h2")

        # skip if already checked
        current_checked_month = headers[-1].text
        if current_checked_month == last_checked_month:
            continue
        last_checked_month = current_checked_month

        if not any(["Unfortunately, there are no appointments" in h.text for h in headers]):
            print(f"✅ Appointments available in {current_checked_month} - {url}")
            results.append((current_checked_month, url))
        else:
            print(f"❎ No Appointments in {current_checked_month}")

if len(results):
    email = Mail(
        from_email="irrer.polterer@posteo.de",
        to_emails=NOTIFICATION_RECIPIENTS,
        subject="[NOTIFICATION] Konsulat Termine",
        html_content="<br><br>".join([f"<a href='{url}'>Appointments available in {month}</a>" for (month, url) in results])
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(email)

# end
driver.quit()
