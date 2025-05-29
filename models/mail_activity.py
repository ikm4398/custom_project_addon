from odoo import models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.constrains('res_model', 'res_id')
    def _check_task_kanban_state(self):
        """
        Prevent scheduling activities on project tasks in 'done' or 'canceled' states.
        """
        for activity in self.filtered(lambda a: a.res_model == 'project.task'):
            task = self.env['project.task'].browse(activity.res_id)
            if task and task.state in ['1_done', '1_canceled']:
                if task.state == '1_canceled':
                    raise UserError(_(
                        "This task (%s) is locked. Please complete the previous task in the project to proceed."
                    ) % task.name)
                else:  # 1_done
                    raise UserError(_(
                        "Cannot schedule activities on task '%s' because it is already completed."
                    ) % task.name)