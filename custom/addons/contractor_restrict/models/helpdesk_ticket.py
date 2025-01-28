from odoo import models, api, exceptions, _



import logging
_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        # Check if the user belongs to the contractor group
        if self.env.user.has_group('contractor_restrict.group_helpdesk_contractor'):
            if 'team_id' in vals:
                # Fetch the 'Operations' team dynamically
                operations_team = self.env['helpdesk.team'].search([('name', '=', 'Operations')], limit=1)

                # Debug logs
                _logger.info(f"Operations Team ID: {operations_team.id if operations_team else 'Not Found'}")
                _logger.info(f"User is trying to set team_id to: {vals['team_id']}")

                # Check if the selected team is NOT 'Operations'
                if not operations_team or vals['team_id'] != operations_team.id:
                    raise exceptions.UserError(
                        _("You are only allowed to assign tickets to the 'Operations' team.")
                    )

        # Allow other updates
        return super(HelpdeskTicket, self).write(vals)
