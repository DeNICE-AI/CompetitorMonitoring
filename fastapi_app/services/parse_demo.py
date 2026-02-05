from typing import Tuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from fastapi_app.core import config


def _create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,720")

    if config.CHROME_DRIVER_PATH:
        service = Service(config.CHROME_DRIVER_PATH)
        return webdriver.Chrome(service=service, options=options)
    return webdriver.Chrome(options=options)


def fetch_page_text(url: str) -> Tuple[str, str]:
    driver = None
    try:
        driver = _create_driver()
        driver.get(url)
        html = driver.page_source
    except WebDriverException as exc:
        raise RuntimeError("Failed to fetch page with Selenium") from exc
    finally:
        if driver:
            driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"
    return title, text[:4000]
