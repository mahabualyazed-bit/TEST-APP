from odoo import models, fields

class CertificationCategory(models.Model):
    _name = 'itb.certification.category'
    _description = 'Certification Category'
    _rec_name = 'name'

    name = fields.Char(string='Category Name', required=True)
    expense_account_id = fields.Many2one('account.account', string='Expense Account', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')