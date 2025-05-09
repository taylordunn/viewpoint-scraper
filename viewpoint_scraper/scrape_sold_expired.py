from datetime import datetime
import logging
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from viewpoint_scraper import login_to_viewpoint, get_property_info

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    property_urls = [
        "/cutsheet/202422079/1/50-Glissade-Court-Bedford",
        "/cutsheet/202402498/1/50-Glissade-Court-Bedford",
        "/cutsheet/202421623/1/72-Element-Court-Bedford",
        "/cutsheet/202409631/1/21-Element-Court-Bedford",
        "/cutsheet/202500602/1/166-Talus-Avenue-Bedford",
        "/cutsheet/202417878/1/176-Talus-Avenue-Bedford",
        "/cutsheet/202426479/1/187-Talus-Avenue-Bedford",
        "/cutsheet/202426162/1/74-Samaa-Court-Bedford"
        "/cutsheet/202404909/1/105-Samaa-Court-Bedford",
        "/cutsheet/202505125/1/119-Samaa-Court-Bedford",
        "/cutsheet/202408295/1/10-Weybridge-Lane-Bedford",
        "/cutsheet/202425045/1/34-Weybridge-Lane-Bedford",
        "/cutsheet/202417337/1/41-Weybridge-Lane-Bedford",
        "/cutsheet/202503654/1/33-Cairnstone-Lane-Bedford",
        "/cutsheet/202425319/1/66-Amesbury-Gate-Bedford",
        "/cutsheet/202501029/1/186-Amesbury-Gate-Bedford",
        "/cutsheet/202417594/1/92-Bristolton-Avenue-Bedford",
        "/cutsheet/202413895/1/25-Puncheon-Way-Bedford",
        "/cutsheet/202424020/1/32-Crownridge-Drive-Bedford",
        "/cutsheet/202405377/1/76-William-Borrett-Terrace-Bedford",
        "/cutsheet/202405436/1/205-Amesbury-Gate-Bedford",
        "/cutsheet/202415568/1/244-Transom-Drive-Halifax",
        "/cutsheet/202406582/1/315-Transom-Drive-Halifax",
        "/cutsheet/202405919/1/116-Innsbrook-Way-Bedford",
        "/cutsheet/202416652/1/404-Starboard-Drive-Halifax",
    ]    

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    login_to_viewpoint(driver)
    time.sleep(5)

    properties_list = []
    for property_url in property_urls:
        # for each property, get its details
        property_info = get_property_info(property_url, driver)
        # only save single family homes
        if property_info["type"] == "Single Family":
            properties_list.append(property_info)

    # write data to CSV (one row per property)
    if len(properties_list) > 0:
        out_file = f"data/sold_expired/properties_{datetime.now().strftime("%Y-%m-%d")}.csv"
        with open(out_file, mode="w", newline="") as file:
            logging.info(f"Writing data to file: {out_file}")
            fieldnames = list(dict.fromkeys(field for p in properties_list for field in p))
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(properties_list)
