# -*- coding: utf-8 -*-
from odoo import fields, models


class TaskRejectWizard(models.TransientModel):
    """Small wizard that forces a manager to justify a rejection."""

    _name = 'task.reject.wizard'
    _description = 'Task Rejection Wizard'

    task_id = fields.Many2one(
        comodel_name='task.approval',
        string='Task',
        required=True,
        ondelete='cascade',
    )
    reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        self.ensure_one()
        self.task_id._reject(self.reason)
        return {'type': 'ir.actions.act_window_close'}
