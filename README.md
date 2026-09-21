# PriceCheckerEmail

A Python app that checks product prices on **a variety of e-commerce sites** using Selenium and emails you when a price changes. Products and their last recorded prices are stored in `list.json`. After sending an alert, the app saves the new price for the next comparison.

Alerts cover both price increases and decreases. Run a check manually or use Docker Compose to check automatically once a day.

## Setup

Run the following commands from the project directory.

For Docker, you need Docker with Compose and Python 3 on the host to manage the watch list. The image includes Python, Chromium, its driver, and Xvfb.

For local execution, you need Python 3.12 or newer, `uv`, and Chrome or Chromium with a compatible driver. A desktop display or Xvfb is required: the app currently starts Chrome in normal GUI mode.

### Configure email

Create a `.env` file in the project directory:

```dotenv
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=your-account@example.com
SMTP_PASSWORD=your-smtp-password
SENDER_EMAIL=your-account@example.com
RECEIVER_EMAIL=recipient@example.com
```

Replace these examples with your provider's settings. The app uses SMTP over SSL (`SMTP_SSL`), typically on port 465; STARTTLS on port 587 is not implemented. Use an app password if your provider requires one.

Both `.env` and `list.json` are excluded from Git.

### Add products

The watch-list editor creates `list.json` automatically if it does not exist. It uses only Python's standard library.

```bash
python3 manageList.py add-product "Product Name"
python3 manageList.py add-vendor "Product Name" "Vendor" "https://www.vendor.com/PRODUCT_ID" --price 169.99 --currency EUR
python3 manageList.py list
```

Replace the example URL with your actual product URL. Use the exact vendor names `Amazon DE`, `Ebay DE`, or `JPC`; unregistered names are skipped during checks.

`--price` is the starting reference price, not a target price. If you omit it, it defaults to `0`, so the first successful check of a nonzero price sends an email and saves that price. `--currency` defaults to `EUR`; it controls the email's currency symbol and does not convert prices.

More watch-list commands:

```bash
# Create a product and its vendor together.
python3 manageList.py add-vendor "Album" "Vendor" "https://www.vendor.com/PRODUCT_PATH" --price 24.99 --create-product

# Repeating add-vendor updates its URL, reference price, and currency.
python3 manageList.py add-vendor "Album" "Vendor" "https://www.vendor.com/PRODUCT_PATH" --price 22.99

python3 manageList.py remove-vendor "Album" "Vendor"
python3 manageList.py remove-product "Album"
python3 manageList.py --help
```

## Run with Docker

Create `.env` and `list.json` before starting the container, then run:

```bash
docker compose up -d --build
docker compose logs -f pricechecker
```

The default schedule is **00:00 in Europe/Berlin**, with no immediate check at startup. Configure these values in `docker-compose.yml`:

```yaml
environment:
  RUN_AT: "00:00"
  TZ: "Europe/Berlin"
  RUN_ON_START: "false"
```

Set `RUN_ON_START` to `"true"` to also check when the container starts. Apply configuration changes with `docker compose up -d`.

To run one check immediately, without starting the scheduler:

```bash
docker compose run --rm pricechecker xvfb-run -a -s "-screen 0 1920x1080x24" python main.py
```

The scheduler already wraps its daily checks in Xvfb. Custom commands bypass the scheduler, so the one-off command includes Xvfb explicitly. This gives Chrome a virtual display without requiring a desktop or monitor on the host.

The container mounts `.env` read-only and updates the host's `list.json`. It runs as UID 1000, which must have permission to write that file.

To change the watch list while using Docker, recreate the container around your edits:

```bash
docker compose down
python3 manageList.py list
# Run your add-product, add-vendor, or removal commands here.
docker compose up -d
```

This avoids concurrent writes and ensures the container mounts the latest file, since the editor saves changes by replacing `list.json`.

## Run locally

Install the Python dependencies:

```bash
uv sync --locked
```

On a desktop, run a single check:

```bash
uv run main.py
```

On a headless distribution, install a browser and matching driver for your OS and CPU architecture, plus Xvfb. On Debian/Ubuntu-based systems, install the virtual-display tools with:

```bash
sudo apt update
sudo apt install xvfb xauth
```

Then run:

```bash
xvfb-run -a -s "-screen 0 1920x1080x24" uv run main.py
```

`main.py` checks the list once and exits. Automatic daily scheduling is provided by the Docker entrypoint.

## Troubleshooting

- **Missing environment variable:** check that `.env` contains all six email settings and that you are running from the project directory.
- **Chrome cannot start:** check the browser/driver installation and run through Xvfb when there is no desktop display.
- **Could not find a price:** the page or price element timed out. The shop may have changed its layout or returned an error or challenge page. That vendor is skipped for the current run.
- **eBay returns HTTP 403:** the server refused the request. This was observed with Chrome's native headless mode; the current setup uses normal Chrome with Xvfb for server execution. A virtual display does not guarantee that a shop will accept automated requests.
- **Email fails:** check the SSL port, credentials, and any app-password requirement. SMTP errors currently stop the run.
- **Docker cannot update prices:** check write permissions on the host's `list.json` for container UID 1000.
