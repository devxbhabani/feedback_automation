# Adamas Portal Feedback Automation

An automated script using [Playwright](https://playwright.dev/python/) to automatically submit pending class and period feedback forms on the Adamas University Student Knowledge City Portal.

---

## Features

- **Automated Login**: Enters student credentials automatically, with a seamless fallback to manual login if MFA, captcha, or portal changes occur.
- **Batch Processing**: Iterates through all subjects listed on the student dashboard.
- **Period Tab Handling**: Automatically traverses multiple period tabs (if present) for each subject.
- **Form Auto-Filling**:
   - Automatically selects radio button ratings.
   - Dynamically sets slider values (`max`, `min`, or custom rating numbers).
   - Optionally enters custom comments in feedback textareas.
- **Dry-Run Mode**: Test and inspect form-filling behavior on a single form without submitting anything.
- **Error Recovery & Diagnostics**: Captures full-page screenshots (`debug_<n>_<label>.png`) when an element interaction times out or encounters errors.

---

## Prerequisites

- **Python 3.8+** installed on your system.
- Chromium browser binaries (installed via Playwright).

---

## Installation & Setup

1. **Clone or navigate to the project directory:**

   ```powershell
   cd d:\automation
   ```

2. **Install Playwright and dependencies:**
   ```powershell
   pip install playwright
   playwright install chromium
   ```

---

## Configuration

Open `automation.py` and adjust the configuration parameters near the top of the file:

```python
# ---------------- CONFIG ----------------
DASHBOARD_URL = "https://adamasknowledgecity.ac.in/student/dashboard"

# Credentials
REG_NO = "YOUR_REGISTRATION_NO"
PASSWORD = "YOUR_PASSWORD"

# Operation Mode
DRY_RUN = False            # Set to True to preview form filling without submitting
RADIO_CHOICE = 0           # 0 = First option (e.g., Strongly Agree / Yes), 1 = Second option
SLIDER_VALUE = "max"       # "max", "min", or an integer string like "4"
COMMENT_TEXT = ""          # Optional comment string for textareas (leave "" to skip)

# Execution Tuning
PAUSE = 1.5                # Delay (in seconds) between navigation/form actions
MAX_FORMS = 500            # Safety cutoff limit
MAX_FAILS_PER_SUBJECT = 2  # Skip to the next subject after N consecutive failures
```

> [!CAUTION]
> **Credential Security**: Never commit or share your `automation.py` file with live credentials. It is recommended to add `.gitignore` or use environment variables to protect your account.

---

## Usage

1. **Verify with Dry Run (Recommended First Step):**
   In `automation.py`, set:

   ```python
   DRY_RUN = True
   ```

   Run the script:

   ```powershell
   python automation.py
   ```

   A Chromium browser window will open, log in, navigate to the first pending form, and fill in the values without clicking **Submit**. Check that the answers match your expectations, then press <kbd>Enter</kbd> in your terminal to finish.

2. **Full Automated Execution:**
   Set `DRY_RUN = False` in `automation.py` and execute:
   ```powershell
   python automation.py
   ```
   The script will:
   - Authenticate to the portal.
   - Loop through all completed subjects on your dashboard.
   - Open feedback forms for each subject and period tab.
   - Fill and submit the ratings.
   - Display real-time progress in the console (e.g. `Submitted #5 (subject 2, tab 1)`).

---

## Troubleshooting & Debugging

- **Manual Login Prompt:** If the script encounters an authentication issue or a captcha, the terminal will prompt:
   ```text
   Auto-login did not reach the dashboard. Log in manually, open the dashboard, then press Enter here...
   ```
   Simply complete login in the opened browser window, navigate to the dashboard, and press <kbd>Enter</kbd> in the console to let automation resume.
- **Debug Screenshots:** Whenever a subject interaction fails, the script automatically captures full-page snapshots named `debug_<n>_subj<id>.png` in the project directory for inspection.
- **Adjusting Timing:** If your internet connection or portal response is slow, increase `PAUSE` to `2.0` or `2.5`.

---

Disclaimer

This automation script is intended for personal productivity and educational purposes on your own student portal account. Ensure your use complies with Adamas University's student IT and portal policies.
