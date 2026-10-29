from odoo import models, fields

class TransBank(models.Model):
    _inherit = 'trans.bank'

    bank_certificate_id = fields.Many2one('itb.certificate', compute='_compute_certificate', store=False)

    def _compute_certificate(self):
        certs = self.env['itb.certificate'].search(
            [('bank_trans_id', 'in', self.ids)])
        cert_map = {c.bank_trans_id.id: c for c in certs}
        for rec in self:
            rec.bank_certificate_id = cert_map.get(rec.id, False)

    def action_open_certificate(self):
        record = self.env['itb.certificate'].search(
            [('bank_trans_id', '=', self.id)], limit=1)
        if record:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'itb.certificate',
                'view_mode': 'form',
                'res_id': record.id,
            }

    def write(self, vals):
        result = super().write(vals)
        if vals.get('state') == 'done':
            certs = self.env['itb.certificate'].search(
                [('bank_trans_id', 'in', self.ids)])
            if certs:
                certs.write({'payment_state': 'paid'})
        return result