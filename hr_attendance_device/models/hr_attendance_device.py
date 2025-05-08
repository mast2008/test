# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)
from datetime import datetime , timedelta
from odoo import api, models, fields
from odoo import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from . import zklib
import time

from socket import socket

import socket


class hr_attendance_device(models.Model):

    _name = 'hr.attendance.device'
    _description = 'Finger Print'
    _order = 'name'

    name = fields.Char('Name', required=True, translate=True)
    status = fields.Boolean('Active', default=True)
    timezone = fields.Integer('Timezone', required=True, default=0)
    hours = fields.Float('Dif. Hours', required=True, default=1.0,help="Minimum different hours between sign-in and sign-out")
    sign = fields.Integer('Auto Sign out', required=True, default=16,help="Make auto action if employee does not make sign out after x hours")
    ip = fields.Char('IP Address', required=True)
    port = fields.Char('Port', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    
    def check_fingerprint(self):
        ip = self.ip
        port = self.port
        zk = zklib.ZKLib(ip, int(port))
        res = False
        try:
            res = zk.connect()
        except:
            pass
        if res != True:
            try:
                ip = socket.gethostbyname(ip).strip()
                zk = zklib.ZKLib(ip, int(port))
                res = zk.connect()
            except:
                pass
        if res == True:
            raise UserError(_("Successful connection"))
        else:
            raise UserError(_("Unable to connect, please check the parameters and network connections."))
            
    def get_fingerprint(self):
        return self.all_fingerprint()
            
    def all_fingerprint(self):
        fingerprints =  self.search([('status','=',True)])
        attendances=None
        for finger in fingerprints:
            ip = finger.ip
            port = finger.port
            zk = zklib.ZKLib(ip, int(port))
            res = False
            try:
                res = zk.connect()
            except:
                pass
            if res != True:
                ip = socket.gethostbyname(ip).strip()
                zk = zklib.ZKLib(ip, int(port))
                res = zk.connect()
            if res == True:
                z=zk.getAttendance()
                if attendances and z!=False and z!=True:
                    attendances=attendances+z
                elif z!=False and z!=True:
                    attendances=z
        hr_attendance =  self.env["hr.attendance"]
        hr_employee = self.env["hr.employee"]
        if (attendances):
            attendances.sort(key=lambda tup: tup[2])
            seconds=finger.hours*60*60
            sign=finger.sign*60*60
            for attendance in attendances:
                test = str(attendance[0]).replace('\\','').replace('x00','')
                employee_id=hr_employee.search([('fingerid','=',str(test))])
                if employee_id:
                    checks=hr_attendance.search([('employee_id','=',employee_id[0].id)],order="id DESC")
                else:
                    continue
                check={}
                attend = attendance[2] - timedelta(hours=finger.timezone)
                if checks:
                    check=checks[0]
                if not checks:
                    action='sign_in'
                elif check.check_out!=False and (attend-check.check_out).total_seconds()>=seconds:
                    action='sign_in'
                elif (attend-check.check_in).total_seconds()>=sign:
                    action='action'
                elif (attend-check.check_in).total_seconds()>=seconds:
                    action='sign_out'
                else:
                    action=False
                if action:
                    if action=='action':
                        action='sign_out'
                        check.check_out = check.check_in+ timedelta(hours=1)
                        action='sign_in'
                    if action=='sign_out':
                        check.check_out = attend
                    else:
                        hr_attendance.create({'check_in':attend ,'employee_id':employee_id[0].id})
        return True

    def clear_fingerprints(self):
        fingerprints =  self.search([('status','=',True)])
        for finger in fingerprints:
            finger.get_fingerprint()
            finger.clear_fingerprint()

    def all_fingerprints(self):
        fingerprints =  self.search([('status','=',True)])
        for finger in fingerprints:
            finger.get_fingerprint()
        
 
            
    def clear_fingerprint(self):
        ip = self.ip
        port = self.port
        zk = zklib.ZKLib(ip, int(port))
        res = False
        try:
            res = zk.connect()
        except:
            pass
        if res != True:
            ip = socket.gethostbyname(ip).strip()
            zk = zklib.ZKLib(ip, int(port))
            res = zk.connect()
        if res == True:
            zk.clearAttendance()
            return True
        else:
            raise UserError(_("Unable to connect, please check the parameters and network connections."))
            

class hr_employee(models.Model):

    _inherit = 'hr.employee'

    fingerprint = fields.Many2one('hr.attendance.device', string='Finger Print')
    fingerid = fields.Char('Finger ID')
    
    _sql_constraints = [
        ('finger_id_uniq', 'unique(fingerprint,fingerid)', 'The finger id of the device must be unique per company!'),]

class hr_employee(models.Model):

    _inherit = 'hr.employee.public'

    fingerprint = fields.Many2one('hr.attendance.device', string='Finger Print')
    fingerid = fields.Char('Finger ID')

class hr_document(models.Model):

    _name = 'hr.document'
    _inherit = ['mail.thread']
    _description = 'Documents'
    _order = 'expiry'

    @api.depends('expiry')
    def _get_document_reminder_fnc(self):
        for record in self:
            overdue = False
            due_soon = False
            if record.expiry:
                current_date = datetime.utcnow().date()
                due_time = record.expiry
                diff_time = (due_time-current_date).days
                if diff_time < 0:
                    overdue = True
                if diff_time < 15 and diff_time >= 0:
                    due_soon = True
            record.document_renewal_overdue = overdue
            record.document_renewal_due_soon = due_soon
        
    def check_all(self):
        records = self.search([])
        for record in records:
            overdue = False
            due_soon = False
            if record.expiry:
                current_date = datetime.utcnow().date()
                due_time = record.expiry
                diff_time = (due_time-current_date).days
                if diff_time < 0:
                    overdue = True
                if diff_time < 15 and diff_time >= 0:
                    due_soon = True
            record.document_renewal_overdue = overdue
            record.document_renewal_due_soon = due_soon

    name = fields.Char('Document Name')
    number = fields.Char('Document No.')
    expiry = fields.Date('Expiry Date')
    reminder = fields.Date('Reminder Date')
    employee = fields.Many2one('hr.employee', string='Employee')
    remind = fields.Boolean(string='Remind', default=False)
    document_renewal_due_soon = fields.Boolean(compute='_get_document_reminder_fnc', string='Has Document to renew',store=True)
    document_renewal_overdue = fields.Boolean(compute='_get_document_reminder_fnc', string='Has Documents Overdued',store=True)

    def check_expire(self):
        documents =  self.search([('reminder','<=',time.strftime(DEFAULT_SERVER_DATE_FORMAT)), ('remind','=',False)])
        for document in documents:
            document.remind = True
            document.message_post(body='Dear Sir,\n\n We would like to inform you that you have document will be expire soon.', subtype='mt_comment',message_type="email", partner_ids=document.message_follower_ids)