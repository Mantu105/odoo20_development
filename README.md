# Odoo 20 — Local Development Setup

This repo runs Odoo 20 locally on Windows with a custom addon (`task_approval`).

```
odoo_20/
├── env/                     # Python virtualenv (not committed)
├── odoo/                    # Odoo 20 core source (odoo-bin, requirements.txt, addons/)
├── custom_addons/
│   └── task_approval/       # custom module — task approval workflow
└── odoo.conf                # local instance config
```

## Requirements

* **Python 3.12** (hard requirement — `odoo/release.py` sets `MIN_PY_VERSION = (3, 12)`; Odoo refuses to start on older versions)
* PostgreSQL running locally, with a role/database matching `odoo.conf`
* Windows: `pywin32` (not listed in `requirements.txt`, which targets Linux primarily)

## First-time setup

1. **Clone Odoo 20 core** into `odoo/` (not committed to this repo):

   ```powershell
   git clone -b 20.0 --depth 1 https://github.com/odoo/odoo.git odoo
   ```

   Then **install Python 3.12** if not already present:

   ```powershell
   winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
   ```

2. **Create the virtualenv against 3.12 specifically:**

   ```powershell
   py -3.12 -m venv env
   env\Scripts\Activate.ps1
   ```

3. **Install dependencies:**

   ```powershell
   python -m pip install --upgrade pip
   pip install -r odoo\requirements.txt --timeout 120 --retries 10
   pip install pywin32
   ```

   > Note: `requirements.txt` was patched to pin `libsass==0.22.0` (a version with a prebuilt Windows wheel) — the originally pinned `0.20.1` fails to build on modern setuptools.

4. **Create the PostgreSQL role/database** matching `odoo.conf` (`db_user=odoo`, `db_password=odoo`, `db_name=odoo20_db` by default).

5. **Initialize the database** (first run only):

   ```powershell
   python odoo\odoo-bin -c odoo.conf -d odoo20_db -i base
   ```

## Running

```powershell
env\Scripts\Activate.ps1
python odoo\odoo-bin -c odoo.conf
```

Then open **http://localhost:9006/**.

## Configuration

See `odoo.conf`:

* `addons_path` — includes both `odoo\odoo\addons` and `custom_addons`
* `db_name` — `odoo20_db`
* `http_port` — `9006`

## Custom addons

* [`custom_addons/task_approval`](custom_addons/task_approval/README.md) — Draft → Submitted → Approved/Rejected task workflow with Employee/Manager roles. See its own README for module-specific install/usage details.

To install or upgrade a custom module:

```powershell
python odoo\odoo-bin -c odoo.conf -d odoo20_db -i task_approval   # install
python odoo\odoo-bin -c odoo.conf -d odoo20_db -u task_approval   # upgrade
```
