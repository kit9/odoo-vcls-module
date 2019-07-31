# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api
from odoo.exceptions import UserError, ValidationError, Warning

import logging
_logger = logging.getLogger(__name__)


class ResoucesLeads(models.Model):

    _name = 'crm.resource.lead'
    _description = 'resource for lead'
    
    project_role_id = fields.Many2one(
        'hr.project_role', string='Seniority')
    number = fields.Float('Number')

class Leads(models.Model):

    _inherit = 'crm.lead'

    company_id = fields.Many2one(string = 'Trading Entity', default = lambda self: self.env.ref('vcls-hr.company_VCFR'))

    # KEEP CAMPAIGN_ID -> FIRST CONTACT
    #campaign_ids = fields.Many2many('utm.campaign', string = 'Campaings')

    ###################
    # DEFAULT METHODS #
    ###################

    def _default_am(self):
        return self.guess_am()
    
    ### CUSTOM FIELDS RELATED TO MARKETING PURPOSES ###
    user_id = fields.Many2one(
        'res.users', 
        string='Account Manager', 
        track_visibility='onchange', 
        #default='_default_am',
        )
    
    company_id = fields.Many2one(default = '')

    country_group_id = fields.Many2one(
        'res.country.group',
        string = "Geographic Area",
        compute = '_compute_country_group',
    )

    referent_id = fields.Many2one(
        'res.partner',
        string = 'Referent',
    )

    functional_focus_id = fields.Many2one(
        'partner.functional.focus',
        string = 'Functional  Focus',
    )

    partner_seniority_id = fields.Many2one(
        'partner.seniority',
        string = 'Seniority',
    )

    client_activity_ids = fields.Many2many(
        'client.activity',
        string = 'Client Activity',
    )

    client_product_ids = fields.Many2many(
        'client.product',
        string = 'Client Product',
    )

    industry_id = fields.Many2one(
        'res.partner.industry',
        string = "Industry",
    )

    product_category_id = fields.Many2one(
        'product.category',
        string = 'Business Line',
        domain = "[('is_business_line','=',True)]"
    )

    
    #date fields
    expected_start_date = fields.Date(
        string="Expected Project Start Date",
    )

    won_reason = fields.Many2one(
        'crm.won.reason',
        string='Won Reason',
        index=True,
        track_visibility='onchange'
    )

    internal_ref = fields.Char(
        string="Ref",
        #readonly = True,
        store = True,
        compute = '_compute_internal_ref',
        inverse = '_set_internal_ref',
    )
    
    technical_adv_id = fields.Many2one(
        'hr.employee', 
        string='Main Technical Advisor', 
        track_visibility='onchange', 
        )
    
    support_team = fields.Many2many(
        'hr.employee', 
        string='Other Technical Experts', 
        )
    
    resources_ids = fields.Many2many(
        'crm.resource.lead', 
        string='Resources', 
        )
    
    CDA = fields.Boolean('CDA signed')
    MSA = fields.Boolean('MSA valid')
    
    contract_type = fields.Selection([('saleorder', 'Sale Order'),
                                      ('workorder', 'Work Order'),
                                      ('termandcondition', 'Terms and conditions'),])


    #is_support_user = fields.Boolean(compute='_compute_is_support_user', store=False)

    app_country_group_id = fields.Many2one(
        'res.country.group',
        string = "Application Geographic Area",
    )

    therapeutic_area_ids = fields.Many2many(
        'therapeutic.area',
        string ='Therapeutic Area',
    )
    
    targeted_indication_ids = fields.Many2many(
        'targeted.indication',
        string ='Targeted Indication',
    )
    
    stage_development_id = fields.Many2one(
        'stage.development',
        string ='Stage of Development',
    )

    meet_story = fields.Char(
    )

    initial_vcls_contact = fields.Many2one(
        'res.users', 
        default=lambda self: self.env.user.id,
        string='VCLS Initial Contact'
    )

    #name = fields.Char() We don't compute, it breaks too much usecases

    lead_history = fields.Many2many(comodel_name="crm.lead", relation="crm_lead_rel", column1="crm_lead_id1")

    ### MIDDLE NAME ###

    contact_middlename = fields.Char("Middle name")

    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        lead_partner_data = super(Leads, self)._create_lead_partner_data(
            name,
            is_company,
            parent_id
        )
        if not is_company:
            if self.contact_middlename:
                lead_partner_data.update({
                    "middlename": self.contact_middlename,
                })
                if 'name' in lead_partner_data:
                    del lead_partner_data['name']
        return lead_partner_data


    @api.model
    def create(self, vals):
        ################
        _logger.info("On create : {}".format(vals))
        if vals['contact_name'] and vals['contact_lastname'] and vals['contact_middlename']:
                vals['name'] = vals['contact_name'] + " " + vals['contact_middlename'] + " " + vals['contact_lastname']
        elif vals['contact_name'] and vals['contact_lastname']:
                vals['name'] = vals['contact_name'] + " " + vals['contact_lastname']
        #############
        lead = super(Leads, self).create(vals)
        # VCLS MODS
        if lead.type == 'lead':
            lead.message_ids[0].subtype_id = self.env.ref('vcls-crm.lead_creation')
        # END OF MODS
        return lead

    ###################
    # COMPUTE METHODS #
    ###################

    """ def _compute_is_support_user(self):
        self.is_support_user = self.env.user.has_group('vcls-hr.vcls_group_superuser_lvl1') """


    @api.depends('country_id')
    def _compute_country_group(self):
        for lead in self:
            groups = lead.country_id.country_group_ids
            if groups:
                lead.country_group_id = groups[0]
    
    @api.onchange('name')
    def _onchange_name(self):
        for lead in self:
            if lead.type == 'opportunity' and lead.internal_ref:
                lead.name_to_internal_ref(False)


    
    """@api.onchange('partner_id','country_id')
    def _change_am(self):
        for lead in self:
            lead.user_id = lead.guess_am()"""
    
    @api.depends('partner_id','type')
    def _compute_internal_ref(self):
        for lead in self:
            if lead.partner_id and lead.type=='opportunity': #we compute a ref only for opportunities, not lead
                if not lead.partner_id.altname:
                    _logger.warning("Please document ALTNAME for the client {}".format(lead.partner_id.name))
                else:
                    next_index = lead.partner_id.core_process_index+1 or 1
                    _logger.info("_compute_internal_ref: Core Process increment for {} from {} to {}".format(lead.partner_id.name,lead.partner_id.core_process_index,next_index))
                    #lead.partner_id.write({'core_process_index': next_index})
                    lead.internal_ref = "{}-{:03}".format(lead.partner_id.altname,next_index)
                    lead.name_to_internal_ref(False)
                    
    @api.onchange('internal_ref')
    def _set_internal_ref(self):
        for lead in self:
            #format checking
            try:
                ref_alt = lead.internal_ref[:-4]
                ref_index = int(lead.internal_ref[-3:])
                if ref_alt.upper() != lead.partner_id.altname.upper():
                    _logger.warning("ALTNAME MISMATCH:{} in company and {} in opportunity {}".format(lead.partner_id.altname.upper(),ref_alt.upper(),lead.name))
                    return
                    #lead.internal_ref = False
                
                if ref_index > lead.partner_id.core_process_index:
                    lead.partner_id.write({'core_process_index': ref_index})
                    _logger.info("_set_internal_ref: Core Process update for {} to {}".format(lead.partner_id.name,ref_index))

            except:
                _logger.warning("Bad Lead Reference syntax: {}".format(lead.internal_ref))
                #lead.internal_ref = False


    ################
    # TOOL METHODS #
    ################

    def guess_am(self):
        if self.partner_id.user_id:
            return self.partner_id.user_id
        elif self.country_group_id.default_am:
            return self.country_group_id.default_am
        #elif self.team_id.
        else:
            return False

    def name_to_internal_ref(self,write_ref = False):
        for lead in self:
            if lead.type == 'opportunity':
                #we verify if the format is matching expectations
                try:
                    #if the name already contains the ref
                    offset = lead.name.upper().find(lead.partner_id.altname.upper())
                    if offset != -1:
                        index = int(lead.name[offset+len(lead.partner_id.altname)+1:offset+len(lead.partner_id.altname)+4])
                        lead.name = "{}-{:03}{}".format(lead.partner_id.altname.upper(),index,lead.name[offset+len(lead.partner_id.altname)+4:])
                        if write_ref:
                            lead.internal_ref = "{}-{:03}".format(lead.partner_id.altname.upper(),index)
                            _logger.info("Updated Lead Ref: {}".format(lead.internal_ref))

                    elif lead.internal_ref:
                        lead.name = "{} | {}".format(lead.internal_ref,lead.name)

                except:
                    _logger.info("Unable to extract ref from opp name {}".format(lead.name))


    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        data = super()._create_lead_partner_data(name,is_company,parent_id)
        data['country_group_id'] = self.country_group_id
        data['referent_id'] = self.referent_id
        data['functional_focus_id'] = self.functional_focus_id
        data['partner_seniority_id'] = self.partner_seniority_id
        data['industry_id'] = self.industry_id
        data['client_activity_ids'] = self.client_activity_ids
        data['client_product_ids'] = self.client_product_ids

        return data

    @api.multi
    def _convert_opportunity_data(self, customer, team_id=False):
        """ Extract the data from a lead to create the opportunity
            :param customer : res.partner record
            :param team_id : identifier of the Sales Team to determine the stage
        """
        data = super()._convert_opportunity_data(customer, team_id)
        
        """#program integration
        if customer:
            isFirstOpportunity = True if len(self.env['crm.lead'].search([('partner_id','=',customer.id)])) < 0 else False
            if isFirstOpportunity :
                values = {'name': "Opportunity's program for client : {}".format(customer.altName),'client_id':customer.id}
                if customer.expert_id:
                    values = values.update({'leader_id':customer.expert_id}) 
                elif customer.user_id:
                    values = values.update({'leader_id':customer.user_id})
                    
                new_program = self.env['project.program'].create(values)
                data['program_id'] = new_program.id"""
        
        data['country_group_id'] = self.country_group_id
        data['referent_id'] = self.referent_id
        data['functional_focus_id'] = self.functional_focus_id
        data['partner_seniority_id'] = self.partner_seniority_id
        data['industry_id'] = self.industry_id
        data['client_activity_ids'] = self.client_activity_ids
        data['client_product_ids'] = self.client_product_ids
        data['product_category_id'] = self.product_category_id
        
        return data

    def _onchange_partner_id_values(self, partner_id):
        result = super(Leads, self)._onchange_partner_id_values(partner_id)
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            result.update({
                "industry_id": partner.industry_id,
                "client_activity_ids": partner.client_activity_ids,
                "client_product_ids": partner.client_product_ids
            })
            if not partner.is_company:
                result.update({
                    "contact_middlename": partner.middlename,
                })
        return result
    
    @api.onchange('contact_name','contact_lastname','contact_middlename')
    def _compute_partner_name(self):
        for lead in self:
            if lead.contact_name and lead.contact_lastname and lead.contact_middlename:
                res = lead.contact_name + " " + lead.contact_middlename + " " + lead.contact_lastname
                lead.name = res
            elif lead.contact_name and lead.contact_lastname:
                res = lead.contact_name + " " + lead.contact_lastname
                lead.name = res
    
    def write(self, vals):
        _logger.info("On write : {}".format(vals))
        if vals['contact_name'] and vals['contact_lastname'] and vals['contact_middlename']:
                vals['name'] = vals['contact_name'] + " " + vals['contact_middlename'] + " " + vals['contact_lastname']
        elif vals['contact_name'] and vals['contact_lastname']:
                vals['name'] = vals['contact_name'] + " " + vals['contact_lastname']
        _logger.info("{}".format(vals))
        return super(Leads, self).write(vals)
    
    #def _vals_to_name
    
    def all_campaigns_pop_up(self):
        print('OK')



