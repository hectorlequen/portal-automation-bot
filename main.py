from pathlib import Path

from playwright.sync_api import TimeoutError, sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(Path("test_page.html").resolve().as_uri())
    page.fill("#mon-champ", "Bonjour depuis Playwright")
    page.click("#mon-bouton")
    try:
        page.click("#bouton-qui-n-existe-pas", timeout=3000)
    except TimeoutError:
        print("Élément introuvable : #bouton-qui-n-existe-pas")
    resultat = page.text_content("#resultat")
    print(resultat)
    page.wait_for_timeout(5000)
    browser.close()