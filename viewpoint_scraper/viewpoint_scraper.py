import logging
import os
import bs4
import requests
import re
import json
from json import JSONDecodeError
from urllib.parse import urlparse
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logging.basicConfig(level=logging.INFO)

BASE_URL = "https://www.viewpoint.ca"

SUBDISTRICTS = {
    "Subdistrict A (Bedford)": 74,
    "Subdistrict F (Bedford)": 73,
    "Subdistrict H (Bedford)": 85,
    "Subdistrict A (Kingswood, Haliburton Hills, Hammonds Plains)": 86,
    "Subdistrict F (Fairmount, Clayton Park, Rockingham)": 23,
}


def get_streets(subdistrict_num: int) -> dict:
    url = BASE_URL + f"/forsale/subdistrict/{subdistrict_num}"
    logging.info(f"{subdistrict_num=}")
    soup = bs4.BeautifulSoup(requests.get(url).content, "html.parser")

    streets_dict = {}
    for street_list in soup.find_all("div", attrs={"id": "subdistrict-list"}):
        for street in street_list.find_all("a"):
            street_name = street.text
            street_url = street.get("href")

            streets_dict[street_name] = street_url

    return streets_dict


def get_properties(street_url) -> dict:
    logging.info(f"{street_url=}")
    soup = bs4.BeautifulSoup(requests.get(street_url).content, "html.parser")

    properties_dict = {}

    for property_item in soup.find("div", attrs={"id": "property-list"}).find_all("a"):
        property_url = property_item.get("href")

        if property_url.startswith("/cutsheet"):
            property_name = property_item.text
            properties_dict[property_name] = property_url

    return properties_dict


def to_snake_case(text: str) -> str:
    # Replace slashes with spaces to preserve both parts (e.g. Bathrooms (F/H))
    text = text.replace("/", " ")
    # Remove parentheses
    text = re.sub(r"[()]+", "", text)
    # Replace non-alphanumeric characters (spaces, commas, dots) with underscores
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    # Convert to lowercase and strip trailing underscores
    return text.strip("_").lower()


def clean_json(json_str) -> str:
    # remove escape characters
    json_str = json_str.replace("\n", "").replace("\t", "")
    # remove trailing commas
    json_str = re.sub(r",(\s*[\]}])", r"\1", json_str)
    # replace empty values like "value": ,
    json_str = re.sub(r'"value":\s*,', '"value": null,', json_str)
    json_str = re.sub(r'"latitude":\s*,', '"latitude": null,', json_str)
    json_str = re.sub(r'"longitude":\s*}', '"longitude": null}', json_str)
    return json_str


def process_json(wait: WebDriverWait) -> dict:
    json_element = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        )
    )
    json_raw = json_element.get_attribute("innerHTML")
    try:
        json_data = json.loads(clean_json(json_raw))
    except JSONDecodeError as e:
        logging.error("Unable to parse JSON: %s", str(e))
        logging.error("Cleaned string: %s", clean_json(json_raw))
        json_data = {}
    
    return json_data

def get_property_info(property_url: str, driver: webdriver.Chrome) -> dict:
    logging.info(f"{property_url=}")
    driver.get(BASE_URL + property_url)

    wait = WebDriverWait(driver, 5)

    # JSON data
    json_data = process_json(wait)
        
    # get listing history
    listing_section = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-section-id="6"]'))
    )
    listing_section.click()
    listing_history = []
    try:
        target = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".table-history-item"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", target)
        listing_items = listing_section.find_elements(
            By.CSS_SELECTOR, ".table-history-item"
        )
        for i, listing_item in enumerate(listing_items):
            listing_header = listing_item.find_element(
                By.CLASS_NAME, "table-history-item-header"
            )
            if i == 0:
                header_labels = [
                    to_snake_case(item.text)
                    for item in listing_header.find_elements(By.TAG_NAME, "span")
                ]

                assert header_labels == [
                    "status",
                    "start_date",
                    "end_date",
                    "list_price",
                    "sold_price",
                    "duration",
                ]
            else:
                header_values = [
                    item.text
                    for item in listing_header.find_elements(By.TAG_NAME, "span")
                ]
                listing_dict = dict(zip(header_labels, header_values))
                listing_dict["changes"] = [
                    l.text
                    for l in listing_item.find_elements(
                        By.CLASS_NAME, "history-item-change"
                    )
                ]

                listing_history.append(listing_dict)
    except TimeoutException as e:
        logging.error("Timeout: failed to recover listing history. %s", str(e))
        driver.save_screenshot("screenshot.png")

    # get details
    details_section = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-section-id="4"]'))
    )
    details_section.click()

    detail_items = details_section.find_elements(By.CLASS_NAME, "cutsheet-detail-item")
    property_details = {}
    for detail in detail_items:
        text = detail.text
        if ":" in text:
            key, value = text.split(":", 1)
            property_details[to_snake_case(key.strip())] = value.strip()

    return {
        "name": json_data.get("name", None),
        "url": json_data.get("url", None),
        "listing_id": re.search(r"/cutsheet/(\d+)/", property_url).group(1),
        "description": json_data.get("description", None),
        "date_posted": json_data.get("datePosted", None),
        "price": json_data.get("priceSpecification", {}).get("price", None),
        "street_address": json_data.get("address", {}).get("streetAddress"),
        "adress_locality": json_data.get("address", {}).get("addressLocality"),
        "postal_code": json_data.get("address", {}).get("postalCode"),
        "rooms": json_data.get("numberOfRooms", None),
        "bathrooms": json_data.get("numberOfBathroomsTotal", None),
        "listing_history": listing_history,
        **property_details,
    }


def login_to_viewpoint(driver: webdriver.Chrome) -> None:
    load_dotenv()
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 5)
    login_button = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'a.nav-item.show-item[href="/user/login"]')
        )
    )

    login_button.click()
    login_div = driver.find_element(By.CLASS_NAME, "vp-dialog")

    if login_div:
        logging.info("Attempting to log in")

        email_input = login_div.find_element(By.CSS_SELECTOR, 'input[type="email"]')
        email_input.send_keys(os.getenv("VIEWPOINT_EMAIL"))
        password_input = login_div.find_element(
            By.CSS_SELECTOR, 'input[type="password"]'
        )
        password_input.send_keys(os.getenv("VIEWPOINT_PASSWORD"))

        login_button = login_div.find_element(By.CLASS_NAME, "btn-positive")
        login_button.click()


def get_property_photos(property_url: str, driver: webdriver.Chrome) -> dict:
    logging.info(f"{property_url=}")
    driver.get(BASE_URL + property_url)

    wait = WebDriverWait(driver, 30)

    # JSON data
    json_data = process_json(wait)

    property_dir = os.path.join("photos", json_data["name"])
    os.makedirs(property_dir, exist_ok=True)

    photos_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".cutsheet-photo-main"))
    )
    photos_button.click()

    img_index = 0

    while True:
        try:
            img = wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        f'img.lg-object.lg-image[data-index="{img_index}"]',
                    )
                )
            )
        except TimeoutException:
            logging.info(f"No image found for index {img_index}. Ending loop.")
            break

        src = img.get_attribute("src")
        logging.info(f"{src=}")
        file_name = os.path.basename(urlparse(src).path)
        file_path = os.path.join(property_dir, file_name)

        if os.path.exists(file_path):
            logging.info(f"File already exists at {file_path}. Skipping.")
        else:
            img_url = src + "?&sd=summary"
            response = requests.get(img_url, stream=True)
            logging.info(f"Downloading photo: {img_url}")
            if response.status_code == 200:
                with open(os.path.join(property_dir, file_name), "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "lg-next-1"))
        )
        next_button.click()

        img_index += 1
