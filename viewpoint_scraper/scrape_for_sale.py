from datetime import datetime
import logging
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from viewpoint_scraper import login_to_viewpoint, get_streets, get_properties, get_property_info

SUBDISTRICTS = {
    "Subdistrict A (Bedford)": 74,
    "Subdistrict F (Bedford)": 73,
    "Subdistrict H (Bedford)": 85,
    "Subdistrict A (Kingswood, Haliburton Hills, Hammonds Plains)": 86,
    "Subdistrict F (Fairmount, Clayton Park, Rockingham)": 23,
}

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    login_to_viewpoint(driver)
    time.sleep(5)

    properties_list = []
    for subdistrict_name, subdistrict_num in SUBDISTRICTS.items():
        logging.info(f"{subdistrict_name=}")

        # for each subdistrict, get the name and URL for each street
        subdistrict_streets = get_streets(subdistrict_num)

        for street_name, street_url in subdistrict_streets.items():
            # for each street, get property listings
            street_properties = get_properties(street_url)

            for property_name, property_url in street_properties.items():
                # for each property, get its details
                property_info = get_property_info(property_url, driver)
                # only save single family homes
                if property_info["type"] == "Single Family":
                    properties_list.append(
                        {"subdistrict_name": subdistrict_name, "street_name": street_name,
                        "property_name": property_name, **property_info}
                    )
    
    # write data to CSV (one row per property)
    if len(properties_list) > 0:
        out_file = f"data/for_sale/properties_{datetime.now().strftime("%Y-%m-%d")}.csv"
        with open(out_file, mode="w", newline="") as file:
            logging.info(f"Writing data to file: {out_file}")
            fieldnames = list(dict.fromkeys(field for p in properties_list for field in p))
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(properties_list)
