import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

DASHBOARD_URL = "https://adamasknowledgecity.ac.in/student/dashboard"

REG_NO = "your registration number"     # your registration number
PASSWORD = "your password"     # your password

DRY_RUN = False         
RADIO_CHOICE = 0       
SLIDER_VALUE = "max"  
COMMENT_TEXT = ""        
PAUSE = 1.5           
MAX_FORMS = 500         
MAX_FAILS_PER_SUBJECT = 2 

SUBJECT_ROW = "text=/^\\s*completed\\s*$/i"
GIVE_FEEDBACK = "button:has-text('Give Feedback'), a:has-text('Give Feedback')"
SUBMIT_BTN = "button:has-text('Submit Feedback'), input[value*='Submit Feedback']"
PERIOD_TABS = "a:has-text('Period'), button:has-text('Period')"
CONFIRM_BTN = ".swal2-confirm, button:has-text('OK'), button:has-text('Yes'), button:has-text('Confirm')"

shot_no = 0


def shot(page, label):
    global shot_no
    shot_no += 1
    name = f"debug_{shot_no}_{label}.png"
    try:
        page.screenshot(path=name, full_page=True)
        print(f"  saved screenshot {name} | url: {page.url}")
    except Exception as e:
        print(f"  could not save screenshot: {e}")


def fill_form(page):
    names = page.eval_on_selector_all(
        "input[type=radio]",
        "els => [...new Set(els.map(e => e.name).filter(Boolean))]",
    )
    for name in names:
        group = page.locator(f"input[type=radio][name='{name}']")
        if group.count() > RADIO_CHOICE:
            group.nth(RADIO_CHOICE).check(force=True)

    for s in page.locator("input[type=range]").all():
        s.evaluate(
            """(el, v) => {
                const val = v === 'max' ? el.max : v === 'min' ? el.min : v;
                el.value = val;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }""",
            SLIDER_VALUE,
        )

    if COMMENT_TEXT:
        for ta in page.locator("textarea").all():
            if ta.is_visible():
                ta.fill(COMMENT_TEXT)


def submit(page):
    btn = page.locator(SUBMIT_BTN).first
    btn.wait_for(state="visible", timeout=15000)
    btn.scroll_into_view_if_needed()
    btn.click()
    time.sleep(PAUSE)
    try:  # success / confirm popup, if any
        page.locator(CONFIRM_BTN).first.click(timeout=3000)
    except PWTimeout:
        pass
    time.sleep(PAUSE)


def open_subject(page, index):
    page.goto(DASHBOARD_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(PAUSE)
    rows = page.locator(SUBJECT_ROW)
    if index >= rows.count():
        return False
    rows.nth(index).click()
    time.sleep(PAUSE)
    return True


def main():
    done = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context().new_page()
        page.on("dialog", lambda d: d.accept())
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")

        # Auto-login if the login page is showing
        reg_box = page.get_by_placeholder("Registration No.")
        if reg_box.count() > 0 and reg_box.first.is_visible():
            reg_box.first.fill(REG_NO)
            page.get_by_placeholder("Password").first.fill(PASSWORD)
            page.get_by_role("button", name="Login").first.click()
            try:
                page.wait_for_url("**/student/dashboard**", timeout=20000)
            except PWTimeout:
                pass
            page.wait_for_load_state("networkidle")

        if "dashboard" not in page.url:
            input("Auto-login did not reach the dashboard. Log in manually, "
                  "open the dashboard, then press Enter here... ")
            page.goto(DASHBOARD_URL)
            page.wait_for_load_state("networkidle")
        time.sleep(PAUSE)
        total_subjects = page.locator(SUBJECT_ROW).count()
        print(f"Found {total_subjects} subjects.")

        for i in range(total_subjects):
            fails = 0
            while done < MAX_FORMS and fails < MAX_FAILS_PER_SUBJECT:
                try:
                    if not open_subject(page, i):
                        break

                    btns = page.locator(GIVE_FEEDBACK)
                    try:
                        btns.first.wait_for(state="visible", timeout=5000)
                    except PWTimeout:
                        print(f"Subject {i + 1}: nothing pending.")
                        break

                    btns.first.click()
                    # wait until the form is actually on screen
                    page.wait_for_selector(SUBMIT_BTN, state="visible", timeout=15000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(PAUSE)

                    tabs = page.locator(PERIOD_TABS)
                    n_tabs = max(tabs.count(), 1)
                    for t in range(n_tabs):
                        if tabs.count() > 1:
                            tabs.nth(t).click()
                            time.sleep(0.7)
                        fill_form(page)
                        if DRY_RUN:
                            print("DRY_RUN: form filled, not submitted.")
                            input("Press Enter to close... ")
                            browser.close()
                            return
                        submit(page)
                        done += 1
                        print(f"Submitted #{done} (subject {i + 1}, tab {t + 1})")
                    fails = 0

                except Exception as e:
                    fails += 1
                    print(f"Subject {i + 1}: problem ({type(e).__name__}) "
                          f"- attempt {fails}/{MAX_FAILS_PER_SUBJECT}")
                    shot(page, f"subj{i + 1}")

        browser.close()
    print(f"Done. Submitted {done} forms.")


if __name__ == "__main__":
    main()