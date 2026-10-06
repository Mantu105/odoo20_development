# -*- coding: utf-8 -*-
{
    'name': 'Task Approval',
    'version': '20.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage tasks through a Draft → Submitted → Approved / Rejected '
               'approval workflow with role-based access.',
    'description': """
Task Approval
=============

A custom module that lets employees create tasks and route them through a
lightweight approval workflow:

    Draft  ->  Submitted  ->  Approved
                          \\-> Rejected

Key features
------------
* Custom ``task.approval`` model (Task Name, Description, Assigned To,
  Priority, Status, Due Date) with an auto-generated reference number.
* Full CRUD with Tree / Form / Search views, filters and group-by.
* State machine driven by object buttons with server-side guards.
* Validation of mandatory fields and past due dates.
* Rejection wizard that captures a mandatory reason.
* Chatter (mail.thread) with field tracking for a full audit trail.
* Two security groups (Employee / Manager) enforced through
  access rights + record rules.
""",
    'author': 'Mantu Raj',
    'website': 'https://www.linkedin.com/in/mantu105/',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        # Security must load first: groups are referenced by the access CSV.
        'security/task_approval_security.xml',
        'security/ir.access.csv',
        # Master data.
        'data/task_approval_data.xml',
        # Wizards before the views/actions that may reference them.
        'wizards/task_reject_wizard_views.xml',
        # Views, then menus (menus reference the actions defined in views).
        'views/task_approval_views.xml',
        'views/task_approval_menus.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
