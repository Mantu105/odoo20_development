# Odoo 20 Module Migration Notes

Findings from migrating `task_approval` onto this Odoo 20 checkout
(`D:\Mantu\odoo_20\odoo`). These are breaking changes verified directly
against the Odoo 20 source (`odoo/addons/base`, `odoo/orm`), not just this
module's symptoms — keep this around as a checklist for migrating other
custom modules.

## 1. `ir.rule` is gone — merged into `ir.access`

Odoo 20 unifies `ir.model.access` (CRUD permissions) and `ir.rule` (record
rules) into a single model: **`ir.access`**
(`odoo/addons/base/models/ir_access.py`). There is no `ir.rule` model
anymore — any XML record or Python code referencing it fails with
`KeyError: 'ir.rule'` while the registry loads.

### Old shape (pre-20)

Two separate mechanisms:

```csv
# security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_task_approval_employee,task.approval.employee,model_task_approval,group_task_approval_employee,1,1,1,1
```

```xml
<!-- security/xxx_security.xml -->
<record id="rule_task_approval_employee_own" model="ir.rule">
    <field name="name">Task Approval: employee sees own tasks</field>
    <field name="model_id" ref="model_task_approval"/>
    <field name="groups" eval="[(4, ref('group_task_approval_employee'))]"/>
    <field name="domain_force">
        ['|', ('assigned_to_id', '=', user.id), ('create_uid', '=', user.id)]
    </field>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
</record>
```

### New shape (Odoo 20)

One row per group does both jobs, in a CSV file **named `ir.access.csv`**
(the model name is taken from the filename, same convention as before):

```csv
# security/ir.access.csv
id,name,model_id,group_id/id,operation,domain
access_task_approval_employee,Task Approval: employee own tasks,task.approval,group_task_approval_employee,crud,"['|', ('assigned_to_id', '=', user.id), ('create_uid', '=', user.id)]"
access_task_approval_manager,Task Approval: manager all tasks,task.approval,group_task_approval_manager,crud,
```

Column notes:

- **`model_id`** is now the plain technical model name (`task.approval`),
  *not* an `ir.model` external id (`model_task_approval`). This works
  because `ir.model._rec_names_search` includes the `model` field, so
  `load()`'s name-search resolution matches it directly.
- **`group_id/id`** is the standard external-id CSV column, unchanged.
- **`operation`** replaces the four `perm_*` booleans with a single CRUD
  code: `crud`, `r`, `ru`, `cr`, etc. (see `CRUD_SELECTION` in
  `ir_access.py`).
- **`domain`** replaces `domain_force`. Leave it blank for unrestricted
  access (equivalent to the old `[(1,'=',1)]` catch-all rule).

You can also define `ir.access` rows as XML `<record>`s instead of CSV if
you prefer — same fields, `model="ir.access"`.

### Semantics: how permission + domain combine

This is the part that's easy to get wrong when migrating:

- A row **with `group_id` set** is a *permission*. All matching
  permissions for the groups a user belongs to are **OR'ed** together.
- A row **with `group_id` blank** is a *restriction*. All restrictions are
  **AND'ed** onto every user regardless of group (this replaces a
  group-less/global `ir.rule`).
- Final visible-record domain = `OR(permissions) AND AND(restrictions)`
  (see `_access_domain()` in `odoo/orm/models.py`).

Practical effect: don't keep a separate "full access, no domain" row for
a group that also needs a restricted-domain row — the blank-domain row
ORs in `True` and silently cancels the restriction out. Fold the
domain into the *same* row instead (as shown above). This is exactly why
the old module's separate `ir.model.access.csv` (blanket grant) +
`ir.rule` (domain restriction) pair had to be collapsed into one CSV row
per group.

### Checklist when migrating another module

1. Rename `security/ir.model.access.csv` → `security/ir.access.csv`.
2. Add `operation` and `domain` columns; drop the four `perm_*` columns.
3. Change `model_id:id` values from `model_xxx` external ids to the plain
   dotted model name.
4. Delete any `<record model="ir.rule">` blocks; fold their `domain_force`
   into the corresponding group's `ir.access` row's `domain` column.
5. Update `__manifest__.py`'s `data` list to point at the renamed CSV.

## 2. Chatter markup: `div.oe_chatter` → `<chatter/>`

The pre-18 convention of manually listing chatter fields is gone —
verified **zero** occurrences of `oe_chatter` across the entire core
`addons` tree (85 files use the new tag instead).

### Old shape

```xml
<div class="oe_chatter">
    <field name="message_follower_ids"/>
    <field name="activity_ids"/>
    <field name="message_ids"/>
</div>
```

Without special-case handling for this div, Odoo 20 just renders each
field with its default widget — i.e. three raw editable one2many list
grids (`mail.followers`, `mail.activity`, `mail.message` columns) instead
of the chatter UI. No error is raised, so this fails silently as a UI bug
rather than a load-time crash.

### New shape

```xml
<chatter/>
```

Place it as a direct child of `<form>`, immediately after `</sheet>` —
matching every core view (e.g. `sale.order`'s form view).

### Checklist when migrating another module

- Search the module's views for `oe_chatter`.
- Replace the whole `<div class="oe_chatter">...</div>` block with a bare
  `<chatter/>` tag in the same position.

## 3. Not a migration issue, but worth knowing: `res.groups` → category

Already correctly handled in this module, but worth noting for others:
since Odoo 19, `res.groups` no longer links to `ir.module.category`
directly via `category_id`. Groups now go through a
`res.groups.privilege` record, which in turn links to the category:

```xml
<record id="privilege_task_approval" model="res.groups.privilege">
    <field name="name">Task Approval</field>
    <field name="category_id" ref="module_category_task_approval"/>
</record>

<record id="group_task_approval_employee" model="res.groups">
    <field name="name">Employee</field>
    <field name="privilege_id" ref="privilege_task_approval"/>
</record>
```

## 4. Data quirk (not a code change): `ir_module_module.module_type`

Not part of the module's code, but can make a correctly-installed module
invisible in the Apps UI: the Apps page's left-hand filter groups by
`ir_module_module.module_type` (`official` / `industries`, added by
`base_import_module`), defaulting the view to `official`. If a module's
`ir.module.module` row was created before that field existed in the
registry (e.g. a very first bootstrap run with `-i base` only), the
column is left `NULL` and the module silently disappears from the
default Apps view even though `state = 'installed'`.

Fix is a one-off data patch, not a module change:

```sql
UPDATE ir_module_module SET module_type = 'official' WHERE name = '<module>';
```
