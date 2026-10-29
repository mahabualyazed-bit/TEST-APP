from odoo import models, fields

class HrPayslipCertificate(models.Model):
    _inherit = 'hr.payslip'

    certificate_amount = fields.Float('Certificate Amount')

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') in ('done', 'paid'):
            certs = self.env['itb.certificate'].search([
                ('payslip_id', 'in', self.ids),
                ('pay_in_payroll', '=', True),
                ('payment_state', '=', 'in_payment'),
            ])
            if certs:
                certs.write({'payment_state': 'paid'})
        return res

    def compute_sheet(self):
        self.check_emp_certificate()
        return super().compute_sheet()

    def check_emp_certificate(self):
        employee_ids = self.mapped('employee_id').ids
        all_certs = self.env['itb.certificate'].search([
            ('pay_in_payroll', '=', True),
            ('employee_id', 'in', employee_ids),
        ])
        for rec in self:
            certs = all_certs.filtered(
                lambda c: c.employee_id.id == rec.employee_id.id
                          and rec.date_from <= c.payroll_date <= rec.date_to
            )
            if certs:
                rec.certificate_amount = sum(certs.mapped('certificate_amount'))
                certs.write({'payslip_id': rec.id})

    def _compute_certificate_count(self):
        for rec in self:
            rec.certificate_count = self.env['itb.certificate'].search_count([('payslip_id', '=', rec.id)])

    certificate_count = fields.Integer(compute='_compute_certificate_count')

    def action_open_certificates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Certificates',
            'res_model': 'itb.certificate',
            'view_mode': 'list,form',
            'domain': [('payslip_id', '=', self.id)],
        }