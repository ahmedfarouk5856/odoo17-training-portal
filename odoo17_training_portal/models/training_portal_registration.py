# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class TrainingPortalRegistration(models.Model):
    """
    Stores student training registrations submitted via the public portal.
    Each record links to an existing op.student, a training program
    (registrar.partner.training.table), and a specific training week
    (training.weekly.schedule).
    """
    _name        = 'training.portal.registration'
    _description = 'Student Training Registration'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _rec_name    = 'student_name'
    _order       = 'create_date desc'

    # ── Student Information ───────────────────────────────────────────────────

    student_name = fields.Char(
        string='Full Name',
        required=True,
        tracking=True,
    )
    university_name = fields.Selection(
        selection=[('university_1', 'University 1')],
        string='University',
        required=True,
        tracking=True,
    )
    university_id = fields.Char(
        string='University ID',
        required=True,
        tracking=True,
    )
    university_group = fields.Many2one(
        comodel_name='level.year',
        string='Year Level',
        required=True,
        tracking=True,
    )
    national_id = fields.Char(
        string='National ID',
        required=True,
        tracking=True,
    )
    phone_whatsapp = fields.Char(
        string='Phone / WhatsApp',
        required=True,
        tracking=True,
    )

    # ── Training Selection (Many2one — fully dynamic) ─────────────────────────

    training_company_id = fields.Many2one(
        comodel_name='masrtech.register.partner',
        string='Training Company',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    training_program_id = fields.Many2one(
        comodel_name='registrar.partner.training.table',
        string='Training Program',
        required=True,
        tracking=True,
        ondelete='restrict',
        domain="[('relation_id', '=', training_company_id)]",
    )
    training_week_id = fields.Many2one(
        comodel_name='training.weekly.schedule',
        string='Training Week',
        required=True,
        tracking=True,
        ondelete='restrict',
        domain="[('training_id', '=', training_program_id)]",
    )

    # ── Convenience related fields ────────────────────────────────────────────

    week_start_date = fields.Date(
        related='training_week_id.week_start_date',
        store=True,
        readonly=True,
    )
    week_end_date = fields.Date(
        related='training_week_id.week_end_date',
        store=True,
        readonly=True,
    )

    # ── Status ────────────────────────────────────────────────────────────────

    state = fields.Selection(
        selection=[
            ('draft',     'Submitted'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        readonly=True,
    )

    # ── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('national_id')
    def _check_national_id(self):
        for rec in self:
            if rec.national_id and not re.match(r'^\d{14}$', rec.national_id):
                raise ValidationError(_('National ID must be exactly 14 digits.'))

    @api.constrains('training_week_id')
    def _check_week_capacity(self):
        """Prevent registration beyond the week's configured max capacity."""
        for rec in self:
            if not rec.training_week_id:
                continue
            week = rec.training_week_id
            if week.is_full:
                raise ValidationError(_(
                    'Week %s (%s – %s) is fully booked. Please choose another week.'
                ) % (week.week_number, week.week_start_date, week.week_end_date))

    # ── State actions ─────────────────────────────────────────────────────────

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'draft'})
