from odoo import models, fields, api
from odoo.exceptions import ValidationError
import calendar
from datetime import date

class Certificate(models.Model):
    _name = 'itb.certificate'
    _description = 'Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    create_uid = fields.Many2one('res.users', string='Created By', readonly=True, default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Created On', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    certification_id = fields.Many2one('itb.certification', string='Certificate Name')
    certificate_category = fields.Many2one('itb.certification.category',string='Certificate Category',related='certification_id.certificate_category',readonly=True,store=True)

    deadline_date = fields.Date(string='Deadline Date')
    start_date = fields.Date(string='Start Date')
    cancel_reason = fields.Text(string='Cancel Reason', readonly=True)
    done_date = fields.Datetime(string='Done Date', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('approve', 'Approved'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    certificate_amount = fields.Integer(string='Certificate Amount',related='certification_id.certificate_amount',readonly=True,store=True)
    cash_trans_id = fields.Many2one('trans.cash', copy=False)
    bank_trans_id = fields.Many2one('trans.bank', copy=False)

    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
    ], default='not_paid', copy=False
    )
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account',related='certification_id.certificate_category.analytic_account_id',readonly=True,store=True)
    certificate_attachment = fields.Binary(string='Attachment', attachment=True)
    certificate_attachment_filename = fields.Char(string='Attachment Filename')
    pay_in_payroll = fields.Boolean(default=False, copy=False)
    payroll_date = fields.Date(copy=False)
    payslip_id = fields.Many2one('hr.payslip', readonly=True, copy=False)

    def action_open_payslip(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'res_id': self.payslip_id.id,
        }

    def action_done(self):
        if not self.certificate_attachment:
            raise ValidationError('You must upload the certificate attachment before marking it as Done.')
        today = date.today()
        start_date = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)

        deadline = self.deadline_date
        achieved = deadline and today <= deadline

        self.write({'state': 'done', 'done_date': fields.Datetime.now()})

        policies = self.env['itb.points.policy'].search([
            ('model_name.model', '=', 'itb.certificate')
        ])
        if policies:
            lines = [(0, 0, {
                'name': policy.name,
                'points': policy.points if achieved else 0,
                'policy_id': policy.id,
                'deduction_points': policy.deduction_points if not achieved else 0,
            }) for policy in policies]

            existing_record = self.env['itb.points.record'].search([
                ('employee_id', '=', self.employee_id.id),
                ('start_date', '=', start_date),
                ('end_date', '=', end_date),
            ], limit=1)

            if existing_record:
                existing_record.add_or_update_lines(lines)
            else:
                self.env['itb.points.record'].create({
                    'employee_id': self.employee_id.id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'line_ids': lines,
                })

        template = self.env.ref('itb_certification.mail_template_certificate_done_manager', raise_if_not_found=False)
        if template and self.employee_id.parent_id.work_email:
            template.send_mail(self.id, force_send=True)

    def action_submit(self):
        self.write({'state': 'submitted'})
        template = self.env.ref('itb_certification.mail_template_certificate_submit', raise_if_not_found=False)
        if template and self.employee_id.work_email:
            template.send_mail(self.id, force_send=True)

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Reason',
            'res_model': 'itb.certificate.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_certificate_id': self.id},
        }

    def action_refund(self):
        self.write({'state': 'refunded'})
        template = self.env.ref('itb_certification.mail_template_certificate_refund', raise_if_not_found=False)
        if not template:
            return
        accounting_employees = self.env['hr.employee'].search([('is_accounting', '=', True)])
        for emp in accounting_employees:
            if emp.work_email:
                template.with_context(
                    email_to=emp.work_email,
                    accounting_name=emp.name,
                    record_url=f"/web#id={self.id}&model=itb.certificate&view_type=form",
                ).send_mail(self.id, force_send=True)

    def action_register_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Register Payment',
            'res_model': 'itb.certificate.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_certificate_id': self.id,
                'default_amount': self.certificate_amount,
            },
        }

    def action_open_cash_trans(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'trans.cash',
            'view_mode': 'form',
            'res_id': self.cash_trans_id.id,
        }

    def action_open_bank_trans(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'trans.bank',
            'view_mode': 'form',
            'res_id': self.bank_trans_id.id,
        }