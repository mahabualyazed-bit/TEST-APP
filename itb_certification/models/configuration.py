from odoo import models, fields

class Certification(models.Model):
    _name = 'itb.certification'
    _description = 'Certification'
    _rec_name = 'certificate_name'

    certificate_name = fields.Char(string='Certificate Name')
    certificate_category = fields.Many2one('itb.certification.category',string='Certificate Category')
    certificate_amount = fields.Integer(string='Certificate Amount')
    department_id = fields.Many2many('hr.department', string='Department')