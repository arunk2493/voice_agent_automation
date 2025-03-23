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
import time

@pytest.mark.parametrize("username, password, expected_result", [
    ("standard_user", "secret_sauce", True),
    ("locked_out_user", "secret_sauce", False),
    ("problem_user", "secret_sauce", True),  # Problem user logs in but might have other issues later
    ("performance_glitch_user", "secret_sauce", True), #Performance glitch user logs in but may encounter performance issues 
    ("", "secret_sauce", False),
    ("standard_user", "", False),
    (" ", " ", False),
    ("standard_user", "wrong_password", False),
    ("invalid_user", "secret_sauce", False), 

])
def test_login(username, password, expected_result):
    driver = webdriver.Chrome()
    driver.get("https://www.saucedemo.com/")
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='username']")))
    username_field.send_keys(username)
    time.sleep(1)


    password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='password']")))
    password_field.send_keys(password)
    time.sleep(1)



    login_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='login-button']")))
    login_button.click()
    time.sleep(1)

    if expected_result:
        assert driver.current_url == "https://www.saucedemo.com/inventory.html" #Successfully login
    else:
        error_message = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='error']")))
        assert error_message.is_displayed() #Displays error message if invalid login


    driver.quit()