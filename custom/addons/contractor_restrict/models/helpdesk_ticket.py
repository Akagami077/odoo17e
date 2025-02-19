import logging
from odoo import models, api, exceptions, _

_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def create(self, vals):
        # Check if the user belongs to the contractor group
        if self.env.user.has_group('contractor_restrict.group_helpdesk_contractor'):
            # Fetch the 'Operations' and 'Contractors' teams dynamically
            allowed_teams = self.env['helpdesk.team'].search([
                ('name', 'in', ['Operations', 'Contractors'])
            ])
            allowed_team_ids = allowed_teams.mapped('id')

            # Check if team_id is specified during creation
            if 'team_id' in vals:
                # Extract the ID correctly
                team_id = vals['team_id'][0] if isinstance(vals['team_id'], (tuple, list)) else vals['team_id']

                # Debug logs
                _logger.info(f"Allowed Team IDs: {allowed_team_ids}")
                _logger.info(f"User is trying to create a ticket with team_id: {team_id}")

                # Check if the selected team is NOT in allowed teams
                if team_id not in allowed_team_ids:
                    raise exceptions.UserError(
                        _("You are only allowed to create tickets for the 'Operations' or 'Contractors' team.")
                    )
            else:
                # If no team is specified, default to 'Operations'
                operations_team = self.env['helpdesk.team'].search([('name', '=', 'Operations')], limit=1)
                vals['team_id'] = operations_team.id if operations_team else False

        # Allow other creations
        return super(HelpdeskTicket, self).create(vals)

    def write(self, vals):
        # Check if the user belongs to the contractor group
        if self.env.user.has_group('contractor_restrict.group_helpdesk_contractor'):
            # Restrict editing the description field
            if 'description' in vals:
                raise exceptions.UserError(_("You are not allowed to edit the description of the ticket."))

            # Restrict contractors to assign tickets only to 'Operations' or 'Contractors' team
            if 'team_id' in vals:
                # Fetch the 'Operations' and 'Contractors' teams dynamically
                allowed_teams = self.env['helpdesk.team'].search([
                    ('name', 'in', ['Operations', 'Contractors'])
                ])
                allowed_team_ids = allowed_teams.mapped('id')

                # Extract the ID correctly
                team_id = vals['team_id'][0] if isinstance(vals['team_id'], (tuple, list)) else vals['team_id']

                # Debug logs
                _logger.info(f"Allowed Team IDs: {allowed_team_ids}")
                _logger.info(f"User is trying to set team_id to: {team_id}")

                # Check if the selected team is NOT in allowed teams
                if team_id not in allowed_team_ids:
                    raise exceptions.UserError(
                        _("You are only allowed to assign tickets to the 'Operations' or 'Contractors' team.")
                    )

        # Allow other updates
        return super(HelpdeskTicket, self).write(vals)
