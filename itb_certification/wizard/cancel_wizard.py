from odoo import models, fields

class CertificateCancelWizard(models.TransientModel):
    _name = 'itb.certificate.cancel.wizard'
    _description = 'Certificate Cancel Wizard'

    certificate_id = fields.Many2one('itb.certificate')
    cancel_reason = fields.Text(string='Cancel Reason', required=True)

    def action_save(self):
        self.certificate_id.write({
            'state': 'cancelled',
            'cancel_reason': self.cancel_reason,
        })