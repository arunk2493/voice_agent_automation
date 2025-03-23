from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

TEST_URL = "https://www.saucedemo.com/"

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

@pytest.mark.parametrize("username, password, expected_result", [
    ("standard_user", "secret_sauce", "products"),
    ("locked_out_user", "secret_sauce", "error"),
    ("problem_user", "secret_sauce", "products"), # Though products page loads, images are broken - considered a pass for login
    ("performance_glitch_user", "secret_sauce", "products"),  # Slow login, but eventually succeeds
    ("", "secret_sauce", "error"),
    ("standard_user", "", "error"),
    (" ", " ", "error"),
    ("invalid_user", "invalid_password", "error"),
    ("standard_user", "wrong_password", "error")
])
def test_login_scenarios(username, password, expected_result):
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get("https://www.saucedemo.com/")

    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test='username']")))
    password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test='password']")))
    login_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test='login-button']")))


    username_field.send_keys(username)
    time.sleep(1)
    password_field.send_keys(password)
    time.sleep(1)
    login_button.click()
    time.sleep(1)



    if expected_result == "products":
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "title"))) # Check for products page title
        except:
            pytest.fail("Login successful, but products page not loaded")

    elif expected_result == "error":
        try:
           error_message = wait.until(EC.presence_of_element_located((By.XPATH, "//h3[@data-test='error']")))
           assert error_message.is_displayed()
        except:
            pytest.fail("Error message not displayed on invalid login")
    driver.quit()