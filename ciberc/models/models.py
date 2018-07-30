# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
import logging

_logger = logging.getLogger(__name__)

class BveView(models.Model):
    _inherit = 'bve.view'

    @api.multi
    def _create_bve_view(self):
        self.ensure_one()

        # create views
        View = self.env['ir.ui.view']
        old_views = View.sudo().search([('model', '=', self.model_name)])
        old_views.sudo().unlink()

        view_vals = [{
            'name': 'Pivot Analysis',
            'type': 'pivot',
            'model': self.model_name,
            'priority': 16,
            'arch': """<?xml version="1.0"?>
                           <pivot string="Pivot Analysis">
                           {}
                           </pivot>
                        """.format("".join(self._create_view_arch()))
        }, {
            'name': 'Graph Analysis',
            'type': 'graph',
            'model': self.model_name,
            'priority': 16,
            'arch': """<?xml version="1.0"?>
                           <graph string="Graph Analysis"
                            type="bar" stacked="True">
                            {}
                           </graph>
                        """.format("".join(self._create_view_arch()))
        }, {
            'name': 'Search BI View',
            'type': 'search',
            'model': self.model_name,
            'priority': 16,
            'arch': """<?xml version="1.0"?>
                           <search string="Search BI View">
                           {}
                           </search>
                        """.format("".join(self._create_view_arch()))
        }]

        for vals in view_vals:
            View.sudo().create(vals)

        # create Tree view
        tree_view = View.sudo().create(
            {'name': 'Tree Analysis',
             'type': 'tree',
             'model': self.model_name,
             'priority': 16,
             'arch': """<?xml version="1.0"?>
                            <tree string="List Analysis" create="false">
                            {}
                            </tree>
                         """.format("".join(self._create_tree_view_arch()))
             })

        # set the Tree view as the default one
        action_vals = {
            'name': self.name,
            'res_model': self.model_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,graph,pivot',
            'view_id': tree_view.id,
            'limit' : 1000, # ONLY THIS LINE IS NEW
            'context': "{'service_name': '%s'}" % self.name,
        }

        ActWindow = self.env['ir.actions.act_window']
        action_id = ActWindow.sudo().create(action_vals)
        self.write({
            'action_id': action_id.id,
            'view_id': tree_view.id,
            'state': 'created'
        })