from odoo import api

def send_task_deadline_extension_email(env, task, task_type='task'):
    """
    Sends email notification to task assignees and the project manager when the task's deadline is modified.
    Args:
        env: Odoo environment
        task: The task record whose deadline was changed
        task_type: String indicating if it's an 'in-progress' or 'canceled' task
    """
    if not task.user_ids and not task.project_id.user_id:
        return

    # Reference the email template
    template = env.ref('custom_project_addon.email_template_task_deadline_extension', raise_if_not_found=True)

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

    # Send the email with context to indicate task type
    template.with_context(task_type=task_type).send_mail(task.id, force_send=True, email_values={
        'recipient_ids': [(6, 0, recipient_partners.ids)],
    })