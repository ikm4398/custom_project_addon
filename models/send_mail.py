###models/send_mail.py
from odoo import api

def send_task_state_change_email(env, task):
    """
    Sends email notification to task assignees and the project manager when task state becomes 'In Progress'.
    """
    if not task.user_ids:
        return

    # Reference the email template
    template = env.ref('custom_project_addon.email_template_task_state_change', raise_if_not_found=True)

    # Get the project manager
    project_manager = task.project_id.user_id

    # Combine assignees and project manager
    recipients = task.user_ids
    if project_manager:
        recipients |= project_manager

    # Filter users with valid email addresses
    recipients = recipients.filtered(lambda u: u.email)
    if not recipients:
        return

    # Get the partner_ids of all recipients
    recipient_partners = recipients.mapped('partner_id')

    # Send the email
    template.send_mail(task.id, force_send=True, email_values={
        'recipient_ids': [(6, 0, recipient_partners.ids)],
    })
