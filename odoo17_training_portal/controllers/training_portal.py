# -*- coding: utf-8 -*-
import json
import re

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError


class TrainingPortalController(http.Controller):
    """
    Handles all routes for the public-facing student training registration portal.

    Routes:
        GET  /training/register          — Render the registration form
        GET  /training/ajax/student      — Look up student by university ID
        GET  /training/ajax/programs     — Return training programs for a company + level
        GET  /training/ajax/weeks        — Return weekly schedule with live capacity
        POST /training/register/submit   — Process and save the registration
    """

    # ── Main form ─────────────────────────────────────────────────────────────

    @http.route('/training/register', type='http', auth='public', website=True, csrf=False)
    def training_form(self, **kw):
        companies = request.env['masrtech.register.partner'].sudo().search([
            ('is_training', '=', True)
        ])
        levels = request.env['level.year'].sudo().search([])
        return request.render('training_portal.training_portal_registration_form', {
            'error':         {},
            'error_message': [],
            'form_data':     {},
            'companies':     companies,
            'levels':        levels,
        })

    # ── AJAX: student lookup by university ID ─────────────────────────────────

    @http.route('/training/ajax/student', type='http', auth='public', website=True, csrf=False)
    def ajax_get_student(self, university_id=None, **kw):
        result = {}
        if university_id:
            student = request.env['op.student'].sudo().search([
                ('faculty_id', '=', university_id.strip()),
            ], limit=1)
            if student:
                level_map = {
                    'one':   '1st',
                    'two':   '2nd',
                    'three': '3rd',
                    'four':  '4th',
                }
                level_name = level_map.get(student.level or '', '')
                level_rec = request.env['level.year'].sudo().search([
                    ('name', '=', level_name)
                ], limit=1)
                result = {
                    'found':          True,
                    'name':           student.name or '',
                    'national_id':    student.vat or '',
                    'phone':          student.mobile or '',
                    'level_id':       str(level_rec.id) if level_rec else '',
                }
            else:
                result = {'found': False}
        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')],
        )

    # ── AJAX: training programs filtered by company + year level ─────────────

    @http.route('/training/ajax/programs', type='http', auth='public', website=True, csrf=False)
    def ajax_get_programs(self, company_id=None, level_id=None, **kw):
        result = []
        try:
            cid = int(company_id) if company_id else 0
            lid = int(level_id)   if level_id   else 0
        except (ValueError, TypeError):
            cid = lid = 0

        if cid:
            programs = request.env['registrar.partner.training.table'].sudo().search([
                ('relation_id', '=', cid),
            ])
            # Filter by year level in Python (avoids Many2many domain issues)
            if lid:
                programs = programs.filtered(lambda p: lid in p.level_ids.ids)

            for p in programs:
                display = p.training_title or (p.training.training_name if p.training else '') or p.code or str(p.id)
                result.append({
                    'id':        p.id,
                    'name':      display,
                    'code':      p.code or '',
                    'level_ids': [{'id': l.id, 'name': l.name} for l in p.level_ids],
                })
        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')],
        )

    # ── AJAX: weekly schedule with live seat availability ─────────────────────

    @http.route('/training/ajax/weeks', type='http', auth='public', website=True, csrf=False)
    def ajax_get_weeks(self, program_id=None, **kw):
        result = []
        if program_id:
            try:
                pid = int(program_id)
            except (ValueError, TypeError):
                pid = 0
            if pid:
                weeks = request.env['training.weekly.schedule'].sudo().search([
                    ('training_id', '=', pid),
                ], order='week_number asc')
                for w in weeks:
                    result.append({
                        'id':     w.id,
                        'number': w.week_number,
                        'start':  str(w.week_start_date) if w.week_start_date else '',
                        'end':    str(w.week_end_date)   if w.week_end_date   else '',
                        'max':    w.max_students,
                        'taken':  w.registered_count,
                        'left':   w.remaining_spots,
                        'full':   w.is_full,
                        'pct':    int((w.registered_count / w.max_students) * 100) if w.max_students else 0,
                    })
        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')],
        )

    # ── Form submission ───────────────────────────────────────────────────────

    @http.route('/training/register/submit', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def training_submit(self, **post):
        error         = {}
        error_message = []

        # Required field validation
        required_fields = [
            'student_name', 'university_name', 'university_id',
            'university_group', 'national_id', 'phone_whatsapp',
            'training_company_id', 'training_program_id', 'training_week_id',
        ]
        for field in required_fields:
            if not post.get(field, '').strip():
                error[field] = 'missing'

        # Student must exist in the system
        if not error:
            uid_check = post.get('university_id', '').strip()
            student_check = request.env['op.student'].sudo().search([
                ('faculty_id', '=', uid_check)
            ], limit=1)
            if not student_check:
                error['university_id'] = 'not_found'
                error_message.append(_('This University ID is not registered. Registration is not allowed.'))

        # National ID format validation
        if not error:
            if not re.match(r'^\d{14}$', post.get('national_id', '')):
                error['national_id'] = 'invalid'
                error_message.append(_('National ID must be exactly 14 digits.'))

        # Live capacity check
        if not error:
            week_id = post.get('training_week_id', '')
            if week_id:
                try:
                    wid  = int(week_id)
                    week = request.env['training.weekly.schedule'].sudo().browse(wid)
                    if week.exists() and week.is_full:
                        error['training_week_id'] = 'full'
                        error_message.append(_(
                            'The selected training week is fully booked (%d/%d seats). '
                            'Please choose a different week.'
                        ) % (week.max_students, week.max_students))
                except (ValueError, TypeError):
                    pass

        if error and not error_message:
            error_message.append(_('Please fill in all required fields.'))

        if error:
            companies = request.env['masrtech.register.partner'].sudo().search([
                ('is_training', '=', True)
            ])
            levels = request.env['level.year'].sudo().search([])
            return request.render('training_portal.training_portal_registration_form', {
                'error':         error,
                'error_message': error_message,
                'form_data':     post,
                'companies':     companies,
                'levels':        levels,
            })

        try:
            student_name  = post['student_name'].strip()
            national_id   = post['national_id'].strip()
            phone         = post.get('phone_whatsapp', '').strip()
            university_id = post['university_id'].strip()
            level_id_raw  = post.get('university_group', '')
            level_id      = int(level_id_raw) if level_id_raw else 0
            univ_name_key = post.get('university_name', '')
            company_id    = int(post['training_company_id'])
            program_id    = int(post['training_program_id'])
            week_id       = int(post['training_week_id'])

            env = request.env

            # Split name into first/last for op.student
            name_parts = student_name.split(' ', 1)
            first_name = name_parts[0]
            last_name  = name_parts[1] if len(name_parts) > 1 else ''

            # Map year level id → year_level selection value
            level_rec = env['level.year'].sudo().browse(level_id)
            level_name_map = {
                '1st': 'one', '2nd': 'two', '3rd': 'three', '4th': 'four',
            }
            year_level_val = level_name_map.get(level_rec.name if level_rec else '', 'one')

            # Find or create op.student by national ID
            existing_student = env['op.student'].sudo().search([
                ('vat', '=', national_id),
            ], limit=1)

            if existing_student:
                student = existing_student
            else:
                student_vals = {
                    'first_name': first_name,
                    'last_name':  last_name,
                    'name':       student_name,
                    'mobile':     phone,
                    'vat':        national_id,
                    'student_id': university_id,
                    'gender':     'm',
                }
                student = env['op.student'].sudo().create(student_vals)

            # Create training.registration record
            env['training.registration'].sudo().create({
                'student_namee':       student.id,
                'vat':                 national_id,
                'phone':               phone,
                'student_id':          university_id,
                'weekly_schedule_id':  week_id,
                'training_course_id':  program_id,
                'partner_id':          company_id,
                'year_level':          year_level_val,
                'registration_status': 'draft',
            })

        except ValidationError as e:
            companies = request.env['masrtech.register.partner'].sudo().search([
                ('is_training', '=', True)
            ])
            levels = request.env['level.year'].sudo().search([])
            error_message.append(str(e))
            return request.render('training_portal.training_portal_registration_form', {
                'error':         error,
                'error_message': error_message,
                'form_data':     post,
                'companies':     companies,
                'levels':        levels,
            })

        return request.render('training_portal.training_portal_registration_success', {
            'student_name': post['student_name'].strip(),
        })
