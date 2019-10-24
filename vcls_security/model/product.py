# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        has_access = self.env['ir.model.access']._disable_cwd_access(
            self._name, operation, 'vcls_security.vcls_account_manager', raise_exception)
        if not has_access:
            return has_access
        return super(ProductTemplate, self).check_access_rights(operation, raise_exception)


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        has_access = self.env['ir.model.access']._disable_cwd_access(
            self._name, operation, 'vcls_security.vcls_account_manager', raise_exception)
        if not has_access:
            return has_access
        return super(Product, self).check_access_rights(operation, raise_exception)
