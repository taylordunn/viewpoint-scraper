import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from viewpoint_scraper import login_to_viewpoint, get_property_photos

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    property_urls = [
        "/cutsheet/202422079/1/50-Glissade-Court-Bedford",
        "/cutsheet/202421623/1/72-Element-Court-Bedford",
        "/cutsheet/202409631/1/21-Element-Court-Bedford",
        "/cutsheet/202417878/1/176-Talus-Avenue-Bedford",
        "/cutsheet/202426479/1/187-Talus-Avenue-Bedford",
        "/cutsheet/202424020/1/32-Crownridge-Drive-Bedford",
        "/cutsheet/202503015/1/70-Crownridge-Drive-Bedford"
        "/cutsheet/202503654/1/33-Cairnstone-Lane-Bedford",
        "/cutsheet/202408295/1/10-Weybridge-Lane-Bedford",
        "/cutsheet/202425045/1/34-Weybridge-Lane-Bedford",
        "/cutsheet/202505125/1/119-Samaa-Court-Bedford",
        "/cutsheet/202425319/1/66-Amesbury-Gate-Bedford",
        "/cutsheet/202508352/1/90-Crownridge-Drive-Bedford"
        "/cutsheet/202415477/1/161-Terradore-Lane-Bedford",
        "/cutsheet/202510435/1/87-Innsbrook-Way-Bedford",
        "/cutsheet/202512042/1/1169-Fleetwood-Drive-Fall-River",
        "/cutsheet/202512069/1/196-Fleetview-Drive-Halifax",
        "/cutsheet/202512242/1/262-Heddas-Way-Fall-River",
        "/cutsheet/202512228/1/82-Shirley-Elliott-Court-Bedford",
        "/cutsheet/202513284/1/49-Crownridge-Drive-Bedford",
        "/cutsheet/202514528/1/43-Crownridge-Drive-Bedford",
        "/cutsheet/202503675/1/1006-Mccabe-Lake-Drive-Middle-Sackville",
        "/cutsheet/202517777/1/68-Element-Court-Bedford"
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
        get_property_photos(property_url, driver)


