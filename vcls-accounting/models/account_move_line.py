# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class Move(models.Model):
    _inherit = 'account.move'

    period_end = fields.Date()

class AccountAnalyticLine(models.Model):
    _inherit = 'account.move.line'
    
    external_account = fields.Char(
        related = 'partner_id.external_account'
    )

    journal_code = fields.Char(
        related = 'journal_id.code'
    )

    account_code = fields.Char(
        related = 'account_id.code'
    )

    base_currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_base_currency',
        store=True)
    
    period_end = fields.Date(
        related = 'move_id.period_end',
    )

    @api.depends('debit','credit')
    def _compute_base_currency(self):
        for rec in self:
            rec.base_currency_id = self.env.ref('base.EUR')
    
    convertion_rate = fields.Float(
        compute='_compute_base_values',
        store=True)

    debit_base_currency = fields.Monetary(
        default=0.0,
        currency_field='base_currency_id',
        readonly=True)
        
    credit_base_currency = fields.Monetary(
        default=0.0,
        currency_field='base_currency_id',
        readonly=True)

    @api.depends('debit','credit','company_currency_id')
    def _compute_base_values(self):
        for line in self.filtered(lambda l: l.debit>0 and l.company_currency_id):
            debit_conv = line.company_currency_id._convert(
                line.debit,
                self.env.ref('base.EUR'),
                self.env.user.company_id,
                line.date or fields.Datetime.now(),
            )
            line.convertion_rate = line.company_currency_id.rate
            line.debit_base_currency = debit_conv

        for line in self.filtered(lambda l: l.credit>0 and l.company_currency_id): 
            credit_conv = line.company_currency_id._convert(
                line.credit,
                self.env.ref('base.EUR'),
                self.env.user.company_id,
                line.date or fields.Datetime.now(),
            )
            line.convertion_rate = line.company_currency_id.rate
            line.credit_base_currency = credit_conv

class Invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        result = super(Invoice, self).action_invoice_open()
        #we edit the date of the moves with the period end account.move.line account.move
        self.move_id.period_end = self.timesheet_limit_date

        return result