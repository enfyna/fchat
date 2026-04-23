from playwright.sync_api import sync_playwright


def bing_images_browser(query, max_results=12, headless_mode=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_mode)
        page = browser.new_page()
        page.goto(f"https://www.bing.com/images/search?q={query}")

        page.wait_for_selector("img.mimg")
        imgs = page.query_selector_all("img.mimg")

        urls = []
        for img in imgs:
            src = img.get_attribute("src") or img.get_attribute("data-src")
            if src and src.startswith("http"):
                urls.append(src)
            if len(urls) >= max_results:
                break

        browser.close()
    return urls
