# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

MANAGER_GROUP = 'task_approval.group_task_approval_manager'


class TaskApproval(models.Model):
    """A task that flows through a Draft -> Submitted -> Approved/Rejected
    approval workflow.

    Employees create and submit their own tasks; managers approve or reject
    submitted tasks. Visibility and CRUD are enforced through record rules and
    access rights (see ``security/``), while the state transitions are guarded
    server-side in this model so the workflow cannot be bypassed via the ORM.
    """

    _name = 'task.approval'
    _description = 'Task Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, due_date asc, id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------
    name = fields.Char(
        string='Task Name',
        required=True,
        tracking=True,
        index=True,
        help="Short, descriptive title of the task.",
    )
    reference = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        help="Unique, auto-generated task reference.",
    )
    description = fields.Html(
        string='Description',
        help="Full description of what needs to be done.",
    )
    assigned_to_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        required=True,
        tracking=True,
        default=lambda self: self.env.user,
        domain="[('share', '=', False)]",
        help="Internal user responsible for completing the task.",
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='1',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
        help="Draft: editable by the owner.\n"
             "Submitted: awaiting a manager decision.\n"
             "Approved / Rejected: final states.",
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True,
        help="Date by which the task must be completed. Cannot be in the past.",
    )

    # --- Audit / decision fields (filled automatically) ---------------
    approver_id = fields.Many2one(
        comodel_name='res.users',
        string='Decided By',
        readonly=True,
        copy=False,
        help="Manager who approved or rejected the task.",
    )
    decision_date = fields.Datetime(
        string='Decision Date',
        readonly=True,
        copy=False,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True,
        copy=False,
    )
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # CRUD overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sequence-based reference on creation."""
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'task.approval') or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        """Duplicated tasks start fresh in draft with a new reference."""
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('name', _("%s (copy)", self.name))
        return super().copy(default)

    # ------------------------------------------------------------------
    # Constraints / validation
    # ------------------------------------------------------------------
    @api.constrains('due_date')
    def _check_due_date_not_in_past(self):
        """A due date may never be set in the past."""
        today = fields.Date.context_today(self)
        for task in self:
            if task.due_date and task.due_date < today:
                raise ValidationError(_(
                    "The due date of task '%(task)s' (%(date)s) cannot be in "
                    "the past.",
                    task=task.name or _('New'),
                    date=fields.Date.to_string(task.due_date),
                ))

    # ------------------------------------------------------------------
    # Workflow actions (object buttons)
    # ------------------------------------------------------------------
    def action_submit(self):
        """Draft -> Submitted (owner action)."""
        for task in self:
            task._ensure_state('draft', _("Only draft tasks can be submitted."))
            task.write({'state': 'submitted'})
            task.message_post(body=_("Task submitted for approval."))
        return True

    def action_approve(self):
        """Submitted -> Approved (manager only)."""
        self._ensure_manager()
        for task in self:
            task._ensure_state(
                'submitted', _("Only submitted tasks can be approved."))
            task.write({
                'state': 'approved',
                'approver_id': self.env.user.id,
                'decision_date': fields.Datetime.now(),
                'rejection_reason': False,
            })
            task.message_post(body=_("Task approved."))
        return True

    def action_reject(self):
        """Open the rejection wizard so a reason can be captured (manager only)."""
        self.ensure_one()
        self._ensure_manager()
        self._ensure_state('submitted', _("Only submitted tasks can be rejected."))
        return {
            'name': _("Reject Task"),
            'type': 'ir.actions.act_window',
            'res_model': 'task.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_id': self.id},
        }

    def action_reset_to_draft(self):
        """Submitted / Rejected -> Draft, clearing the previous decision."""
        for task in self:
            if task.state not in ('submitted', 'rejected'):
                raise UserError(_(
                    "Only submitted or rejected tasks can be reset to draft."))
            task.write({
                'state': 'draft',
                'approver_id': False,
                'decision_date': False,
                'rejection_reason': False,
            })
            task.message_post(body=_("Task reset to draft."))
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _reject(self, reason):
        """Perform the actual rejection. Called from the wizard."""
        self.ensure_one()
        self._ensure_manager()
        self._ensure_state('submitted', _("Only submitted tasks can be rejected."))
        self.write({
            'state': 'rejected',
            'approver_id': self.env.user.id,
            'decision_date': fields.Datetime.now(),
            'rejection_reason': reason,
        })
        self.message_post(body=_("Task rejected. Reason: %s", reason))
        return True

    def _ensure_state(self, expected_state, error_message):
        """Guard a transition so it only runs from the expected source state."""
        self.ensure_one()
        if self.state != expected_state:
            raise UserError(error_message)

    def _ensure_manager(self):
        """Raise unless the current user is a Task Approval Manager."""
        if not self.env.user.has_group(MANAGER_GROUP):
            raise UserError(_(
                "Only a Task Approval Manager can approve or reject tasks."))
