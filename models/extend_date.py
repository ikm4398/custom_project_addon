from odoo import models, fields
from datetime import timedelta
from .sendmail_dateextend import send_task_deadline_extension_email

class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        """
        Extend deadlines of all canceled tasks in the same project by the same number of days
        when the deadline of an in-progress task is adjusted, and send email notifications for both.
        """
        # Store original deadlines for comparison
        old_deadlines = {task.id: task.date_deadline for task in self if task.state == '01_in_progress'}

        # Call the parent write method to update the task(s)
        result = super().write(vals)

        # Check if date_deadline is being updated
        if 'date_deadline' in vals:
            for task in self.filtered(lambda t: t.state == '01_in_progress'):
                if task.date_deadline and old_deadlines.get(task.id):
                    # Calculate the difference in days between old and new deadline
                    delta_days = (task.date_deadline - old_deadlines[task.id]).days

                    # Send notification for the in-progress task
                    if delta_days != 0:
                        send_task_deadline_extension_email(self.env, task, task_type='in-progress task')

                        # Find all canceled tasks in the same project
                        canceled_tasks = self.search([
                            ('project_id', '=', task.project_id.id),
                            ('state', '=', '1_canceled'),
                            ('id', '!=', task.id)
                        ])

                        # Extend deadlines of canceled tasks and send emails
                        for canceled_task in canceled_tasks:
                            if canceled_task.date_deadline:
                                new_deadline = canceled_task.date_deadline + timedelta(days=delta_days)
                                canceled_task.with_context(allow_deadline_update=True).write({'date_deadline': new_deadline})
                                send_task_deadline_extension_email(self.env, canceled_task, task_type='canceled task')

        return result