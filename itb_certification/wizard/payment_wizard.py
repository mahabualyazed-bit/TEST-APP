from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class CertificatePaymentWizard(models.TransientModel):
    _name = 'itb.certificate.payment.wizard'
    _description = 'Certificate Payment Wizard'

    certificate_id = fields.Many2one('itb.certificate', readonly=True)
    payment = fields.Selection([
        ('direct_payment', 'Direct Payment'),
        ('payroll', 'Payroll'),
    ], string='Payment', required=True, default='direct_payment')
    payment_type = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ], string='Payment Type')
    certificate_date = fields.Date(string='Certificate Date', default=fields.Date.context_today)
    amount = fields.Float(string='Amount', readonly=True)

    @api.constrains('payment', 'payment_type')
    def _check_payment_type(self):
        for rec in self:
            if rec.payment == 'direct_payment' and not rec.payment_type:
                raise ValidationError('Payment Type is required for Direct Payment.')

    @api.constrains('payment', 'certificate_date')
    def _check_certificate_date(self):
        today = date.today()
        for rec in self:
            if rec.payment == 'payroll':
                if not rec.certificate_date:
                    raise ValidationError('Certificate Date is required for Payroll payment.')
                if (rec.certificate_date.month, rec.certificate_date.year) != (today.month, today.year):
                    raise ValidationError('Certificate Date must be within the current month.')

    def action_create_payment(self):
        cert = self.certificate_id
        if self.payment == 'payroll':
            cert.write({
                'pay_in_payroll': True,
                'payroll_date': self.certificate_date,
                'payment_state': 'in_payment',
            })
            return
        employee = cert.employee_id
        partner = employee.user_id.partner_id
        category = cert.certification_id.certificate_category
        analytic_distribution = {str(category.analytic_account_id.id): 100} if category.analytic_account_id else False
        vals = {
            'type': 'send',
            'partner_id': partner.id if partner else False,
            'ref': employee.name,
            'account_ids': [(0, 0, {
                'label': cert.certification_id.certificate_name,
                'amount': self.amount,
                'account_id': category.expense_account_id.id,
                'analytic_distribution': analytic_distribution,
            })],
        }
        if self.payment_type == 'cash':
            trans = self.env['trans.cash'].create(vals)
            cert.cash_trans_id = trans.id
        else:
            trans = self.env['trans.bank'].create(vals)
            cert.bank_trans_id = trans.id
        cert.payment_state = 'in_payment'