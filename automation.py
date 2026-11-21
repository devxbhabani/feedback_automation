import re
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

DASHBOARD_URL = "https://adamasknowledgecity.ac.in/student/dashboard"

REG_NO = "AU/2025/0003051"     # your registration number
PASSWORD = "Bhabani@2006"     # your password

DRY_RUN = False           
RADIO_CHOICE = 0        
SLIDER_VALUE = "max"     
COMMENT_TEXT = ""         
PAUSE = 1.5         
MAX_FORMS = 500         
MAX_FAILS_PER_SUBJECT = 3 
MAX_SAME_FORM = 4        

SUBJECT_ROW = "text=/^\\s*completed\\s*$/i"
GIVE_FEEDBACK = "button:has-text('Give Feedback'), a:has-text('Give Feedback')"
SUBMIT_BTN = "button:has-text('Submit Feedback'), input[value*='Submit Feedback']"
PERIOD_TABS = "a:has-text('Period'), button:has-text('Period')"
CONFIRM_BTN = ".swal2-confirm, button:has-text('OK'), button:has-text('Confirm')"

shot_no = 0


def short(e):
    return str(e).strip().splitlines()[0][:200] if str(e).strip() else type(e).__name__


def shot(page, label):
    global shot_no
    shot_no += 1
    name = f"debug_{shot_no}_{label}.png"
    try:
        page.screenshot(path=name, full_page=True)
        print(f"  saved screenshot {name} | url: {page.url}")
    except Exception as e:
        print(f"  could not save screenshot: {short(e)}")

FILL_JS = """
([radioChoice, sliderValue, comment]) => {
    const vis = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    // radios: group visible ones by name, pick one per group
    const groups = {};
    document.querySelectorAll('input[type=radio]').forEach(r => {
        if (!vis(r)) return;
        (groups[r.name || ('_' + Math.random())] ||= []).push(r);
    });
    Object.values(groups).forEach(list => {
        const r = list[Math.min(radioChoice, list.length - 1)];
        r.checked = true;
        r.dispatchEvent(new Event('input', {bubbles: true}));
        r.dispatchEvent(new Event('change', {bubbles: true}));
        r.click();
    });
    // sliders
    document.querySelectorAll('input[type=range]').forEach(s => {
        if (!vis(s)) return;
        s.value = sliderValue === 'max' ? s.max : sliderValue === 'min' ? s.min : sliderValue;
        s.dispatchEvent(new Event('input', {bubbles: true}));
        s.dispatchEvent(new Event('change', {bubbles: true}));
    });
    // optional comment
    if (comment) {
        document.querySelectorAll('textarea').forEach(t => {
            if (!vis(t)) return;
            t.value = comment;
            t.dispatchEvent(new Event('input', {bubbles: true}));
            t.dispatchEvent(new Event('change', {bubbles: true}));
        });
    }
    return Object.keys(groups).length;
}
"""


def fill_visible(page):
    return page.evaluate(FILL_JS, [RADIO_CHOICE, SLIDER_VALUE, COMMENT_TEXT])


def get_tabs(page):
    return page.locator(PERIOD_TABS).filter(has_text=re.compile(r"\d{1,2}:\d{2}"))


def fill_all_tabs(page):
    tabs = get_tabs(page)
    n = tabs.count()
    if n > 1:
        for t in range(n):
            tabs.nth(t).click()
            time.sleep(0.7)
            fill_visible(page)
        tabs.nth(0).click()         
        time.sleep(0.7)
    else:
        fill_visible(page)
    return max(n, 1)


def click_submit(page):
    btn = page.locator(SUBMIT_BTN).filter(visible=True).first
    btn.wait_for(state="visible", timeout=15000)
    try:
        btn.scroll_into_view_if_needed(timeout=5000)
        btn.click(timeout=8000)
    except Exception as e:
        print(f"  normal click failed ({short(e)}), using JS click")
        page.evaluate(
            """() => {
                const vis = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                const b = [...document.querySelectorAll("button, input[type=submit]")]
                    .find(x => vis(x) && /submit feedback/i.test(x.innerText || x.value || ''));
                if (!b) throw new Error('submit button not found');
                b.click();
            }"""
        )
    time.sleep(PAUSE)
    try: 
        page.locator(CONFIRM_BTN).first.click(timeout=3000)
    except Exception:
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


def pending_in_modal(page):
    """Returns the 'N pending' number shown in the modal, or None if not found."""
    try:
        text = page.inner_text("body", timeout=3000)
    except Exception:
        return None
    m = re.search(r"(\d+)\s*pending", text, re.I)
    return int(m.group(1)) if m else None


def login_if_needed(page):
    page.goto(DASHBOARD_URL)
    page.wait_for_load_state("networkidle")
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


def main():
    done = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context().new_page()
        page.on("dialog", lambda d: d.accept())

        login_if_needed(page)
        total_subjects = page.locator(SUBJECT_ROW).count()
        print(f"Found {total_subjects} subjects.")

        for i in range(total_subjects):
            fails = 0
            last_url, same = None, 0
            while done < MAX_FORMS and fails < MAX_FAILS_PER_SUBJECT:
                try:
                    if not open_subject(page, i):
                        break

                    btns = page.locator(GIVE_FEEDBACK).filter(visible=True)
                    try:
                        btns.first.wait_for(state="visible", timeout=8000)
                    except PWTimeout:
                        n = pending_in_modal(page)
                        if n:
                            raise RuntimeError(f"modal says {n} pending but no Give Feedback button found")
                        print(f"Subject {i + 1}: nothing pending.")
                        break

                    btns.first.click()
                    page.wait_for_selector(SUBMIT_BTN, state="visible", timeout=15000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(PAUSE)

                    if page.url == last_url:
                        same += 1
                    else:
                        last_url, same = page.url, 1
                    if same >= MAX_SAME_FORM:
                        raise RuntimeError("same form keeps coming back - submit is not registering")

                    n_tabs = fill_all_tabs(page)
                    if DRY_RUN:
                        print(f"DRY_RUN: filled {n_tabs} tab(s), not submitted.")
                        input("Press Enter to close... ")
                        browser.close()
                        return

                    click_submit(page)
                    done += 1
                    print(f"Submitted #{done} (subject {i + 1}, {n_tabs} tab(s))")
                    fails = 0

                except Exception as e:
                    fails += 1
                    print(f"Subject {i + 1}: problem - {short(e)} "
                          f"(attempt {fails}/{MAX_FAILS_PER_SUBJECT})")
                    shot(page, f"subj{i + 1}")

        browser.close()
    print(f"Done. Submitted {done} forms.")


if __name__ == "__main__":
    main()