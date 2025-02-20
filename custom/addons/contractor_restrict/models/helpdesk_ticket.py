import logging
from odoo import models, api, exceptions, _

_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def create(self, vals):
        """ Restrict contractors to create tickets only in 'Operations' or 'Contractors' teams """
        if self.env.user.has_group('contractor_restrict.group_helpdesk_contractor'):
            # Fetch allowed teams dynamically
            allowed_teams = self.env['helpdesk.team'].search([
                ('name', 'in', ['Contractors'])
            ])
            allowed_team_ids = allowed_teams.mapped('id')

            # Check if team_id is specified during creation
            if 'team_id' in vals:
                team_id = vals['team_id'][0] if isinstance(vals['team_id'], (tuple, list)) else vals['team_id']

                # Log for debugging
                _logger.info(f"Allowed Team IDs: {allowed_team_ids}")
                _logger.info(f"User is trying to create a ticket with team_id: {team_id}")

                if team_id not in allowed_team_ids:
                    raise exceptions.UserError(
                        _("You can only create tickets for the 'Operations' or 'Contractors' team.")
                    )
            else:
                # Default to 'Operations' if no team is provided
                operations_team = self.env['helpdesk.team'].search([('name', '=', 'Operations')], limit=1)
                vals['team_id'] = operations_team.id if operations_team else False

        return super(HelpdeskTicket, self).create(vals)

    def write(self, vals):
        """ Restrict contractors from changing the team if the current team is NOT 'Contractors' """
        if self.env.user.has_group('contractor_restrict.group_helpdesk_contractor'):
            if 'team_id' in vals:
                # Get the allowed teams dynamically
                operations_team = self.env['helpdesk.team'].search([('name', '=', 'Operations')], limit=1)
                contractors_team = self.env['helpdesk.team'].search([('name', '=', 'Contractors')], limit=1)
                allowed_team_ids = [team.id for team in [operations_team, contractors_team] if team]

                for ticket in self:
                    # Debug logging
                    _logger.info(f"Current ticket team: {ticket.team_id.name} (ID: {ticket.team_id.id})")
                    _logger.info(f"User is trying to change team_id to: {vals['team_id']}")

                    # Restrict team change if the current team is not 'Contractors'
                    if ticket.team_id.id != contractors_team.id:
                        raise exceptions.UserError(
                            _("You can only change the team if the current team is 'Contractors'.")
                        )

                    # Ensure the new team is either 'Operations' or 'Contractors'
                    new_team_id = vals['team_id'][0] if isinstance(vals['team_id'], (tuple, list)) else vals['team_id']
                    if new_team_id not in allowed_team_ids:
                        raise exceptions.UserError(
                            _("You can only assign tickets to the 'Operations' or 'Contractors' team.")
                        )

        return super(HelpdeskTicket, self).write(vals)
