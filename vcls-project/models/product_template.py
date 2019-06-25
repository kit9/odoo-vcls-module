from odoo import models, fields, tools, api
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    #################
    # CUSTOM FIELDS #
    #################

    grouping_info = fields.Char(
        store = True,
        compute = '_compute_grouping_info',
    )

    ###################
    # COMPUTE METHODS #
    ###################

    @api.depends('deliverable_id','seniority_level_id')
    def _compute_grouping_info(self):
        for prod in self:
            if prod.deliverable_id:
                prod.grouping_info = prod.deliverable_id.name
            elif prod.seniority_level_id:
                prod.grouping_info = prod.seniority_level_id.name
            else:
                prod.grouping_info = False
