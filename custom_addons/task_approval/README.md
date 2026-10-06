# Task Approval

A custom Odoo module that lets employees create tasks and route them through a
lightweight approval workflow, with role-based access for **Employee** and
**Manager**.

```
Draft ──▶ Submitted ──▶ Approved
                    └─▶ Rejected  (with a mandatory reason)
```

* **Odoo version:** 17.0 Community Edition
* **License:** LGPL-3
* **Technical name:** `task_approval`

---

## Features

| Requirement | Implementation |
|---|---|
| Custom model | `task.approval` — Task Name, Description, Assigned To, Priority, Status, Due Date (+ auto reference & audit fields) |
| CRUD | Full create/read/update/delete via Tree, Form and Search views |
| Workflow | `Draft → Submitted → Approved / Rejected` state machine with server-side guards |
| Validation | Mandatory fields (`required`) + `@api.constrains` blocking past due dates; rejection requires a reason |
| Views | Tree (status badges), Form (statusbar + chatter), Search (filters & group-by) |
| Security | Two groups (Employee / Manager) enforced through **access rights** *and* **record rules** |
| Extras | Sequenced reference (`TASK/2026/0001`), mail chatter with field tracking, rejection wizard, app icon |

---

## Requirements

* Odoo **17.0** Community Edition
* Python 3.10+
* Depends on Odoo core modules only: `base`, `mail`

No external Python libraries are required.

---

## Installation

1. **Copy the module** into your Odoo addons path:

   ```bash
   cp -r task_approval /path/to/odoo/custom_addons/
   ```

   Make sure the folder is included in `addons_path` in your `odoo.conf`:

   ```ini
   [options]
   addons_path = /path/to/odoo/addons,/path/to/odoo/custom_addons
   ```

2. **Restart the Odoo service** and update the apps list:

   ```bash
   ./odoo-bin -c odoo.conf -u task_approval -d <your_database>
   ```

   Or, from the UI: enable **Developer Mode** → *Apps* → *Update Apps List*.

3. **Install** — search for **“Task Approval”** in *Apps* and click **Install**
   (developer mode must be on to see custom apps).

---

## Configuration — assigning roles

The module ships with two roles under
*Settings → Users & Companies → Users → (a user) → Task Approval*:

* **Employee** — create, edit and submit their **own** tasks. Employees can
  only see tasks they created or that are assigned to them.
* **Manager** — see **all** tasks and **Approve** / **Reject** submitted ones.
  Manager automatically inherits every Employee permission.

Assign at least one Manager so submitted tasks can be actioned.

---

## Usage

1. Open the **Task Approval** app → **Tasks** → **New**.
2. Fill in Task Name, Assigned To, Priority and a Due Date (not in the past),
   then **Submit**.
3. A **Manager** opens the submitted task and clicks **Approve**, or **Reject**
   (which opens a wizard asking for a reason).
4. The decision, decider and timestamp are recorded, and every change is logged
   in the chatter.

---

## Design notes

* **Odoo 17 syntax** — views use the modern inline `invisible` / `readonly`
  expressions (e.g. `invisible="state != 'draft'"`). The legacy `attrs` and
  `states` attributes were removed in Odoo 17 and are intentionally not used.
* **Defense in depth** — the Approve/Reject buttons are hidden from
  non-managers via `groups=`, *and* the transitions re-check the manager group
  server-side (`_ensure_manager`) so the workflow cannot be bypassed through
  the ORM or XML-RPC.
* **Security model** — access rights grant the base CRUD capability per group,
  while record rules scope *which* records each group can touch. Employees are
  limited to their own tasks; managers see everything.
* **Auditability** — `mail.thread` tracking on key fields plus explicit
  `message_post` calls give a complete history of each task.

---

## Module structure

```
task_approval/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── task_approval_data.xml          # reference sequence
├── models/
│   ├── __init__.py
│   └── task_approval.py                # model, workflow, validation
├── security/
│   ├── ir.model.access.csv             # access rights
│   └── task_approval_security.xml      # groups + record rules
├── static/
│   └── description/
│       └── icon.png
├── views/
│   ├── task_approval_menus.xml
│   └── task_approval_views.xml         # tree / form / search / action
└── wizards/
    ├── __init__.py
    ├── task_reject_wizard.py           # rejection reason wizard
    └── task_reject_wizard_views.xml
```
