# from odoo import models, fields, api
# from odoo.exceptions import UserError
# from odoo.tools.translate import _
# from .send_mail import send_task_state_change_email

# class ProjectTask(models.Model):
#     _inherit = 'project.task'

#     state = fields.Selection(selection_add=[
#         ('01_in_progress', 'In Progress'),
#         ('02_changes_requested', 'Changes Requested'),
#         ('03_approved', 'Approved'),
#         ('1_canceled', 'Canceled'),
#         ('1_done', 'Done')
#     ], ondelete={
#         '01_in_progress': 'set default',
#         '02_changes_requested': 'set default',
#         '03_approved': 'set default',
#         '1_canceled': 'set default',
#         '1_done': 'set default'
#     })

#     @api.model
#     def create(self, vals_list):
#         """
#         Set the first task in a project to 'In Progress', others to 'Canceled'.
#         Ensure company_id is set, defaulting to the current user's company.
#         """
#         if isinstance(vals_list, dict):
#             vals_list = [vals_list]

#         for vals in vals_list:
#             if not vals.get('company_id'):
#                 project_id = vals.get('project_id')
#                 if project_id:
#                     project = self.env['project.project'].browse(project_id)
#                     vals['company_id'] = project.company_id.id if project.company_id else self.env.company.id
#                 else:
#                     vals['company_id'] = self.env.company.id

#             project_id = vals.get('project_id')
#             if project_id:
#                 existing_tasks_count = self.search_count([
#                     ('project_id', '=', project_id),
#                     ('state', 'not in', ['1_canceled', '1_done', False])
#                 ])
#                 vals['state'] = '01_in_progress' if existing_tasks_count == 0 else '1_canceled'
#         return super().create(vals_list)

#     def write(self, vals):
#         """
#         1. Prevent edits to done/canceled tasks (except system/status fields)
#         2. When marking task as done, activate next canceled task
#         3. Send email on task state change to 'In Progress'
#         """
#         SYSTEM_FIELDS = {
#             'state',
#             'message_ids',
#             'access_token',
#             'write_date',
#             '__last_update',
#             'date_last_stage_update',
#             'write_uid',
#             'activity_ids',
#             'message_follower_ids'
#         }

#         user_fields = set(vals.keys()) - SYSTEM_FIELDS

#         for task in self:
#             if task.state in ['1_done', '1_canceled'] and user_fields:
#                 if task.state == '1_canceled':
#                     raise UserError(_(
#                         "The task '%s' is locked. Please complete the previous task in the project to make changes."
#                     ) % task.name)
#                 else:
#                     raise UserError(_(
#                         "The task '%s' is completed and cannot be modified. You can only change its status."
#                     ) % task.name)

#         # Notify on status change to In Progress
#         if vals.get('state') == '01_in_progress':
#             for task in self.filtered(lambda t: t.state == '1_canceled' and t.user_ids):
#                 send_task_state_change_email(self.env, task)

#         # Transition to done and unlock next canceled task
#         if vals.get('state') == '1_done':
#             for task in self.filtered(lambda t: t.state != '1_done'):
#                 next_task = self.search([
#                     ('project_id', '=', task.project_id.id),
#                     ('state', '=', '1_canceled'),
#                     ('id', '!=', task.id)
#                 ], order='create_date ASC', limit=1)

#                 if next_task:
#                     super(ProjectTask, next_task).write({'state': '01_in_progress'})
#                     send_task_state_change_email(self.env, next_task)

#         return super().write(vals)

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from .send_mail import send_task_state_change_email

class ProjectTask(models.Model):
    _inherit = 'project.task'

    state = fields.Selection(selection_add=[
        ('01_in_progress', 'In Progress'),
        ('02_changes_requested', 'Changes Requested'),
        ('03_approved', 'Approved'),
        ('1_canceled', 'Canceled'),
        ('1_done', 'Done')
    ], ondelete={
        '01_in_progress': 'set default',
        '02_changes_requested': 'set default',
        '03_approved': 'set default',
        '1_canceled': 'set default',
        '1_done': 'set default'
    })

    @api.model
    def create(self, vals_list):
        """
        Set the first task in a project to 'In Progress', others to 'Canceled'.
        Ensure company_id is set, defaulting to the current user's company.
        """
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('company_id'):
                project_id = vals.get('project_id')
                if project_id:
                    project = self.env['project.project'].browse(project_id)
                    vals['company_id'] = project.company_id.id if project.company_id else self.env.company.id
                else:
                    vals['company_id'] = self.env.company.id

            project_id = vals.get('project_id')
            if project_id:
                existing_tasks_count = self.search_count([
                    ('project_id', '=', project_id),
                    ('state', 'not in', ['1_canceled', '1_done', False])
                ])
                vals['state'] = '01_in_progress' if existing_tasks_count == 0 else '1_canceled'
        return super().create(vals_list)

    def write(self, vals):
        """
        1. Prevent edits to done/canceled tasks (except system/status fields or allowed deadline updates)
        2. When marking task as done, activate next canceled task
        3. Send email on task state change to 'In Progress'
        """
        SYSTEM_FIELDS = {
            'state',
            'message_ids',
            'access_token',
            'write_date',
            '__last_update',
            'date_last_stage_update',
            'write_uid',
            'activity_ids',
            'message_follower_ids'
        }

        # Allow date_deadline updates for canceled tasks if triggered by system (e.g., extend_date.py)
        allowed_fields = SYSTEM_FIELDS | {'date_deadline'} if self.env.context.get('allow_deadline_update') else SYSTEM_FIELDS
        user_fields = set(vals.keys()) - allowed_fields

        for task in self:
            if task.state in ['1_done', '1_canceled'] and user_fields:
                if task.state == '1_canceled':
                    raise UserError(_(
                        "The task '%s' is locked. Please complete the previous task in the project to make changes."
                    ) % task.name)
                else:
                    raise UserError(_(
                        "The task '%s' is completed and cannot be modified. You can only change its status."
                    ) % task.name)

        # Notify on status change to In Progress
        if vals.get('state') == '01_in_progress':
            for task in self.filtered(lambda t: t.state == '1_canceled' and t.user_ids):
                send_task_state_change_email(self.env, task)

        # Transition to done and unlock next canceled task
        if vals.get('state') == '1_done':
            for task in self.filtered(lambda t: t.state != '1_done'):
                next_task = self.search([
                    ('project_id', '=', task.project_id.id),
                    ('state', '=', '1_canceled'),
                    ('id', '!=', task.id)
                ], order='create_date ASC', limit=1)

                if next_task:
                    super(ProjectTask, next_task).write({'state': '01_in_progress'})
                    send_task_state_change_email(self.env, next_task)

        return super().write(vals)