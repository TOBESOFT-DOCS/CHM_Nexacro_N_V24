import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# 환경 변수 또는 설정 파일을 통해 민감한 정보 관리
load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL")
USERNAME = os.getenv("MANUAL_USERNAME")
PASSWORD = os.getenv("PASSWORD")
BOOK_ID = os.getenv("BOOK_ID")
API_URL_BASE = os.getenv("API_URL_BASE")
API_URL = f"{API_URL_BASE}{BOOK_ID}"
EDIT_URL_BASE=os.getenv("EDIT_URL_BASE")
UUID_URL_BASE=os.getenv("UUID_URL_BASE")
EXTERNAL_URL_BASE=os.getenv("EXTERNAL_URL_BASE")
EXTERNAL_SYSTEM_ID=os.getenv("EXTERNAL_SYSTEM_ID")
EXTERNAL_REFRESH_URL_BASE=os.getenv("EXTERNAL_REFRESH_URL_BASE")

ADDED_FILE_PATH = "added_files.txt"
CHANGED_FILE_PATH = "changed_files.txt"

def service_login(driver):
    """로그인 기능"""
    print("Navigating to login page...")
    print(f"LOGIN_URL: {LOGIN_URL}")
    print(f"LOGIN_URL: {USERNAME}")
    print(f"LOGIN_URL: {PASSWORD}")
    driver.get(LOGIN_URL)
    try:
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Username"]'))
        )
        username_input.send_keys(USERNAME)

        password_input = driver.find_element(By.XPATH, '//input[@placeholder="Password"]')
        password_input.send_keys(PASSWORD)

        stay_logged_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Stay logged in"]'))
        )
        stay_logged_in_button.click()
        print("Login successful.")
    except Exception as e:
        print(f"Error during login: {e}")
        raise

def read_file_to_list(file_path):
    """파일을 읽어 리스트로 변환"""
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

def fetch_json_from_api(url):
    """API 요청 및 JSON 데이터 반환"""
    print(f"Fetching data from API: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching API data: {e}")
        return None

def find_target_id(json_data, alias):
    """JSON 데이터에서 특정 alias의 target_id 찾기"""
    if not json_data:
        return None
    for item in json_data.get("userDefinedIds", []):
        if item.get("alias") == alias:
            return item.get("targetId")
    return None

def content_update(driver, target_id, item):
    if not target_id:
        print("Invalid target ID. Cannot proceed with content update.")
        return

    target_url = f"{EDIT_URL_BASE}{target_id}"
    print(f"Navigating to content editing page: {target_url}")
    driver.get(target_url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )

    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
    actions.send_keys(Keys.DELETE).perform()

    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print("Confirm alert detected. Accepting...")
        alert.accept()
    except TimeoutException:
        print("No Confirm alert detected. Continuing...")

    cookies = driver.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    uuid_url = f"{UUID_URL_BASE}"
    response = session.get(uuid_url)
    if response.status_code == 200:
        uuid = response.text.strip()
        print(f"UUID retrieved: {uuid}")

        second_url = f"{EXTERNAL_URL_BASE}{target_id}/{uuid}"
        params = {"system_id": EXTERNAL_SYSTEM_ID, "item": item}

        while True:
            second_response = session.get(second_url, params=params)
            if second_response.status_code == 200:
                print("Second request successful.")
                break
            else:
                print(f"Retrying... (Status: {second_response.status_code})")
                time.sleep(5)

        refresh_url = f"{EXTERNAL_REFRESH_URL_BASE}{target_id}"
        refresh_response = session.get(refresh_url)
        if refresh_response.status_code == 200:
            print("Refresh request successful.")
        else:
            print(f"Failed to refresh: {refresh_response.status_code}")
    else:
        print(f"Failed to get UUID: {response.status_code}")

def process_file_items(file_items, json_response, driver):
    """파일에서 읽은 항목을 처리"""
    for item in file_items:
        target_id = find_target_id(json_response, item)
        print(f"Processing alias '{item}', target_id: {target_id}")
        content_update(driver, target_id, item)

if __name__ == "__main__":
    driver = webdriver.Chrome()
    added_files = read_file_to_list(ADDED_FILE_PATH)
    changed_files = read_file_to_list(CHANGED_FILE_PATH)

    try:
        service_login(driver)
        json_response = fetch_json_from_api(API_URL)
        if json_response:
            print("Processing added files...")
            process_file_items(added_files, json_response, driver)
            print("Processing changed files...")
            process_file_items(changed_files, json_response, driver)
        else:
            print("Failed to fetch JSON data.")
    finally:
        driver.quit()
