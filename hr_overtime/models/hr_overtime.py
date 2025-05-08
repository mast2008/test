# -*- coding: utf-8 -*-

import time
import pytz
from odoo import tools
from odoo import api, fields, models, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import netsvc
#from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.exceptions import UserError

import logging
_l = logging.getLogger(__name__)

class hr_contract(models.Model):

    _inherit = 'hr.contract'

    policy_id = fields.Many2one('hr.policy', string='Policy')
    multi_schedule = fields.Boolean(string='Flexible Schedule', default=False)
    schedule_hours = fields.Float(string='Schedule Hours', default=0.0)
    weekend = fields.Integer(string='No. Dayoff', default=0)
    launch_break = fields.Boolean(string='Flexible Break', default=False)
    launch_hours = fields.Float(string='Break Hours', default=0.0)
    launch_start = fields.Float(string='Break Start', default=0.0)
    launch_end = fields.Float(string='Break End', default=23.99)

    @api.onchange('multi_schedule')
    def onchange_schedule(self):
        self.launch_break = False


class hr_policy(models.Model):

    _name = 'hr.policy'
    _description = 'HR Policy'

    name = fields.Char(string='Name', required=True)
    sign_in = fields.Integer(string='Late sign in', help="Minutes after which this policy applies")
    sign_out = fields.Integer(string='Early sign out', help="Minutes after which this policy applies")
    line_ids = fields.One2many('hr.policy.line', 'policy_id', string='Policy Lines')


class hr_policy_line(models.Model):

    _name = 'hr.policy.line'
    _description = 'HR Policy Line'

    name = fields.Char(string='Name', required=True)
    policy_id = fields.Many2one('hr.policy', string='Policy')
    type = fields.Selection([('restday', 'Rest Day'),('holiday', 'Public Holiday')],string='Type', required=True)
    active_after = fields.Integer(string='Active After', help="Minutes after which this policy applies")
    rate = fields.Float(string='Rate', required=True, help='Multiplier of employee wage.')
    starttime = fields.Float(string='Start Time', default=0.0)
    endtime = fields.Float(string='End Time', default=23.99)

class hr_employee(models.Model):

    _inherit = 'hr.employee'
    
    def get_worked_hours(self, contract, date_from, date_to):
        res=0
        if not contract.resource_calendar_id:
            return res
        day_from = date_from
        day_to = date_to
        nb_of_days = (day_to - day_from).days + 1
        for day in range(0, nb_of_days):
            datetime_day=datetime.strptime(day_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT),DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=day)
            weekday = datetime_day.weekday()
            for work in contract.resource_calendar_id.attendance_ids:
                if str(work.dayofweek)==str(weekday):
                    start=(datetime_day + timedelta(hours=work.hour_from))
                    end=(datetime_day + timedelta(hours=work.hour_to))
                    res+=(end-start).seconds/3600.0
        return res
        
    def get_rest_rate(self, contract):
        res=0
        if not contract.policy_id:
            return res
        for line in contract.policy_id.line_ids:
            if line.type=='restday':
                res=line.rate
        return res
        
    def get_holiday_rate(self, contract):
        res=0
        if not contract.policy_id:
            return res
        for line in contract.policy_id.line_ids:
            if line.type=='holiday':
                res=line.rate
        return res
    
class hr_payslip(models.Model):
    _inherit="hr.payslip"

    def unlink(self):
        for payslip in self:
            weekend = self.env['schedule.weekend'].search([('employee_id','=',payslip.employee_id.id), ('date','>=',payslip.date_from), ('date','<=',payslip.date_to)])
            weekend.unlink()
        return super(hr_payslip, self).unlink()

    @api.model
    def _get_worked_day_lines(self):

        def check_absents(contract, datetime_day):
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            yr = datetime_day.isocalendar()[0]
            weekNumber = datetime_day.isocalendar()[1]
            week = str(yr) + "/" + str(weekNumber)
            weekend = self.env['schedule.weekend'].search([('employee_id','=',contract.employee_id.id), ('name','=',week), ('date','!=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                if not attendance_ids and len(weekend)>=contract.weekend:
                    res+= contract.schedule_hours
                elif not attendance_ids:
                    weekend_new = self.env['schedule.weekend'].create({'name':week, 'date':day, 'employee_id':contract.employee_id.id})
            return res

        def was_on_leave(employee_id, datetime_day):
            res = False
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',employee_id),('date_from','<=',day),('date_to','>=',day)])
            if holiday_ids:
                res = holiday_ids[0].holiday_status_id
            return res

        def check_absent(contract, datetime_day):
            weekday = datetime_day.strftime("%w")
            if weekday=="0":
                weekday=str(6)
            else:
                weekday=str(int(weekday)-1)
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                if not attendance_ids:
                    for work in contract.resource_calendar_id.attendance_ids:
                        if work.dayofweek==weekday and (work.date_from==False or work.date_from<datetime_day) and (work.date_to==False or work.date_to>datetime_day):
                            start=(sday + timedelta(hours=work.hour_from))
                            end=(sday + timedelta(hours=work.hour_to))
                            res+=(end-start).seconds/3600.0
            return res
		
        def check_attend(contract, datetime_day):
            weekday = datetime_day.strftime("%w")
            if weekday=="0":
                weekday=str(6)
            else:
                weekday=str(int(weekday)-1)
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_out','<=',eday)],order='check_in ASC')
                if attendance_ids and not contract.multi_schedule:
                    for work in contract.resource_calendar_id.attendance_ids:
                        if work.dayofweek==weekday and (work.date_from==False or work.date_from<=datetime_day) and (work.date_to==False or work.date_to>=datetime_day):
                            start=(sday + timedelta(hours=work.hour_from))
                            end=(eday + timedelta(hours=work.hour_to))
                            res+=(end-start).seconds/3600.0
            return res

        def check_attends(contract, datetime_day):
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                for attend in attendance_ids:
                    res+=attend.worked_hours
            return res

        def check_late(contract, datetime_day, context=None):
            weekday = datetime_day.strftime("%w")
            if weekday=="0":
                weekday=str(6)
            else:
                weekday=str(int(weekday)-1)
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                for work in contract.resource_calendar_id.attendance_ids:
                    if work.dayofweek==weekday and (work.date_from==False or work.date_from<datetime_day) and (work.date_to==False or work.date_to>datetime_day):
                        start=(sday + timedelta(hours=work.hour_from))
                        end=(eday + timedelta(hours=work.hour_to))
                        for attendance_id in attendance_ids:
                            attend=attendance_id
                            now=attend.check_in + timedelta(hours=3)
                            now_first=attendance_ids[0].check_in + timedelta(hours=3)
                            if now>start and now<end and contract.policy_id.sign_in<=(now-start).seconds/60:
                                if contract.launch_break and now_first!=now:
                                    if now>=datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_start * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT) and now<=datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_end * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT):
                                        continue
                                    elif now<datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_start * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT):
                                        continue
                                    elif now>datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_end * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT):
                                        res+=(now-datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_end * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)).seconds/3600.0
                                else:
                                    res+=(now-start).seconds/3600.0
            return res

        def check_lates(contract, datetime_day):
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                total = 0
                for attend in attendance_ids:
                    total+=attend.worked_hours
                if attendance_ids and (total+contract.policy_id.sign_in+contract.policy_id.sign_out)<contract.schedule_hours:
                    res+=contract.schedule_hours - total
            return res

        def check_early(contract, datetime_day):
            weekday = datetime_day.strftime("%w")
            if weekday=="0":
                weekday=str(6)
            else:
            	weekday=str(int(weekday)-1)
            res = 0
            day = datetime_day.strftime("%Y-%m-%d")
            date_day=datetime.strftime(datetime_day, "%Y-%m-%d")
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                for work in contract.resource_calendar_id.attendance_ids:
                    if work.dayofweek==weekday and (work.date_from==False or work.date_from<datetime_day) and (work.date_to==False or work.date_to>datetime_day):
                        start=(sday + timedelta(hours=work.hour_from))
                        end=(sday + timedelta(hours=work.hour_to))
                        for attendance_id in attendance_ids:
                            attend=attendance_id
                            if not attend.check_out:
                                return
                            now = attend.check_out + timedelta(hours=3)
                            now_first = attendance_ids[0].check_out + timedelta(hours=3)
                            if now>start and now<end and contract.policy_id.sign_out<=(end-now).seconds/60:
                                if contract.launch_break and now_first==now:
                                    if now>=datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_start * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT) and now<=datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_end * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT):
                                        continue
                                    elif now<datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_start * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT):
                                        res+=(datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_start * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)-now).seconds/3600.0
                                    elif now>datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(contract.launch_end * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT):
                                        res+=(end-now).seconds/3600.0
                                else:
                                    res+=(end-now).seconds/3600.0
            return res

        def holiday_overtime(contract, datetime_day):
            if contract.multi_schedule:
                return 0
            weekday = datetime_day.strftime("%w")
            if weekday=="0":
                weekday=str(6)
            else:
                weekday=str(int(weekday)-1)
            res = 0
            day = datetime_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_day=datetime.strftime(datetime_day, DEFAULT_SERVER_DATE_FORMAT)
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            for holiday_id in holiday_ids:
                holiday = holiday_id
                sday=holiday.date_from
                eday=holiday.date_to
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_out','<=',eday)],order='check_in ASC')
                for attend in attendance_ids:
                    active=0
                    overtime = True
                    for policy in contract.policy_id.line_ids:
                        starttime = datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(policy.starttime * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)
                        endtime = datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(policy.endtime * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)
                        if policy.type=='holiday' and attend.check_in<=endtime and attend.check_out>=starttime:
                            active = policy.active_after
                            overtime = True
                            worked_hours = 0
                            if attend.check_in>=starttime and attend.check_out<=endtime:
                                worked_hours = (attend.check_out - attend.check_in).seconds/60
                            elif attend.check_in>=starttime and attend.check_out>endtime:
                                worked_hours = (endtime - attend.check_in).seconds/60
                            elif attend.check_in<starttime and attend.check_out<=endtime:
                                worked_hours = (attend.check_out - starttime).seconds/60
                            elif attend.check_in<starttime and attend.check_out>endtime:
                                worked_hours = (endtime - starttime).seconds/60
                            if worked_hours>=active:
                                res += worked_hours
            if not holiday_ids:
                x=False
                for work in contract.resource_calendar_id.attendance_ids:
                    if work.dayofweek==weekday and (work.date_from==False or work.date_from<datetime_day) and (work.date_to==False or work.date_to>datetime_day):
                        x=True
                if x==False:
                    sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                    eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                    attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_out','<=',eday)],order='check_in ASC')
                    for attend in attendance_ids:
                        active=0
                        overtime = True
                        for policy in contract.policy_id.line_ids:
                            starttime = datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(policy.starttime * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)
                            endtime = datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(policy.endtime * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)
                            if policy.type=='holiday' and attend.check_in<=endtime and attend.check_out>=starttime:
                                active = policy.active_after
                                overtime = True
                                worked_hours = 0
                                if attend.check_in>=starttime and attend.check_out<=endtime:
                                    worked_hours = (attend.check_out - attend.check_in).seconds/3600
                                elif attend.check_in>=starttime and attend.check_out>endtime:
                                    worked_hours = (endtime - attend.check_in).seconds/3600
                                elif attend.check_in<starttime and attend.check_out<=endtime:
                                    worked_hours = (attend.check_out - starttime).seconds/3600
                                elif attend.check_in<starttime and attend.check_out>endtime:
                                    worked_hours = (endtime - starttime).seconds/3600
                                if worked_hours>=active:
                                    res += worked_hours*policy.rate
            return res

        def holiday_overtimes(contract, datetime_day):
            res = 0
            day = datetime_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_day=datetime.strftime(datetime_day, DEFAULT_SERVER_DATE_FORMAT)
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            for holiday_id in holiday_ids:
                holiday = holiday_id
                sday=holiday.date_from
                eday=holiday.date_to
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                for attend in attendance_ids:
                    active=0
                    overtime = True
                    for policy in contract.policy_id.line_ids:
                        starttime = (day + " " + str(policy.starttime)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        endtime = (day + " " + str(policy.endtime)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if policy.type=='holiday' and attend.check_in<=endtime and attend.check_out>=starttime:
                            active = policy.active_after
                            overtime = True
                            worked_hours = 0
                            if attend.check_in>=starttime and attend.check_out<=endtime:
                                worked_hours = (attend.check_out - attend.check_in).seconds/60
                            elif attend.check_in>=starttime and attend.check_out>endtime:
                                worked_hours = (endtime - attend.check_in).seconds/60
                            elif attend.check_in<starttime and attend.check_out<=endtime:
                                worked_hours = (attend.check_out - starttime).seconds/60
                            elif attend.check_in<starttime and attend.check_out>endtime:
                                worked_hours = (endtime - starttime).seconds/60
                            if worked_hours>=active:
                                res += worked_hours*policy.rate
            return res
        	
        def rest_overtime(contract, datetime_day):
            weekday = datetime_day.strftime("%w")
            if weekday=="0":
                weekday=str(6)
            else:
                weekday=str(int(weekday)-1)
            res = 0
            active=0
            date_day=datetime.strftime(datetime_day, DEFAULT_SERVER_DATE_FORMAT)
            day = datetime_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if not holiday_ids:
                sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
                time = {}
                for work in contract.resource_calendar_id.attendance_ids:
                    if work.dayofweek==weekday and (work.date_from==False or work.date_from<datetime_day) and (work.date_to==False or work.date_to>datetime_day):
                        if str(datetime_day + timedelta(hours=work.hour_from)) not in time:
                            time[str(datetime_day + timedelta(hours=work.hour_from))]={'start':(sday + timedelta(hours=work.hour_from)),'end':(sday + timedelta(hours=work.hour_to))}

                if time:
                    for attendance_id in attendance_ids:
                        attend=attendance_id
                        if attend.check_out:
                            y=0.0
                            now=attend.check_out + timedelta(hours=3)
                            for key,value in sorted(time.items()):
                                start=value['start']
                                end=value['end']
                                for policy in contract.policy_id.line_ids:
                                    starttime = datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(policy.starttime * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)
                                    endtime = datetime.strptime(day + " " + str('{0:02.0f}:{1:02.0f}'.format(*divmod(policy.endtime * 60, 60)) + ":00"),DEFAULT_SERVER_DATETIME_FORMAT)
                                    if policy.type=='restday':
                                        active = policy.active_after
                                        overtime = True
                                        worked_hours = 0
                                        if attend.check_in>=starttime and attend.check_in<start and attend.check_in<=endtime:
                                            worked_hours += (start - attend.check_in).seconds/3600
                                        if attend.check_out<=endtime and attend.check_out>=starttime and attend.check_out>end:
                                            worked_hours += (attend.check_out - end).seconds/3600
                                        if (worked_hours*60)>=active:
                                            res+=worked_hours*policy.rate
            return res

        def rest_overtimes(contract, datetime_day):
            res = 0
            active=0
            date_day=datetime.strftime(datetime_day, DEFAULT_SERVER_DATE_FORMAT)
            day = datetime_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            holiday_ids = self.env['hr.leave'].search([('state','=','validate'),('employee_id','=',contract.employee_id.id),('date_from','<=',day),('date_to','>=',day)])
            if holiday_ids:
                return res

            sday=datetime.strptime(str(datetime_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
            eday=datetime.strptime(str(datetime_day) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            attendance_ids=self.env['hr.attendance'].search([('employee_id','=',contract.employee_id.id),('check_in','>=',sday),('check_in','<=',eday)],order='check_in ASC')
            total = 0
            for attendance_id in attendance_ids:
                total += attendance_id.worked_hours
            if total>contract.schedule_hours:
                if attendance_id.check_out:
                    for policy in contract.policy_id.line_ids:
                        starttime = datetime.strptime((day + " " + '{0:02.0f}:{1:02.0f}'.format(*divmod(float(policy.starttime) * 60, 60)) + ":00"), DEFAULT_SERVER_DATETIME_FORMAT)
                        endtime = datetime.strptime((day + " " + '{0:02.0f}:{1:02.0f}'.format(*divmod(float(policy.endtime) * 60, 60)) + ":00"), DEFAULT_SERVER_DATETIME_FORMAT)
                        if policy.type=='restday':
                            active = policy.active_after
                            overtime = True
                            worked_hours = total - contract.schedule_hours
                            if attendance_id.check_out>=starttime and attendance_id.check_out<=endtime and (worked_hours*60)>=active:
                                res+=worked_hours*policy.rate
            return res

        contract_ids = self.contract_id
        date_from = self.date_from
        date_to = self.date_to

        res = []
        for contract in contract_ids:
            absents = {}
            attends = {}
            lates = {}
            earlys = {}
            holidays = {}
            rests = {}
            leaves= {}
            day_from = date_from
            day_to = date_to
            nb_of_days = (day_to - day_from).days + 1
            for day in range(0, nb_of_days):
                absent = check_absent(contract, day_from + timedelta(days=day))
                attend = check_attend(contract, day_from + timedelta(days=day))
                late = check_late(contract, day_from + timedelta(days=day))
                early = check_early(contract, day_from + timedelta(days=day))
                holiday = holiday_overtime(contract, day_from + timedelta(days=day))
                rest = rest_overtime(contract, day_from + timedelta(days=day))
                if contract.multi_schedule:
                    absent = check_absents(contract, day_from + timedelta(days=day))
                    attend = check_attends(contract, day_from + timedelta(days=day))
                    late = check_lates(contract, day_from + timedelta(days=day))
                    early = {}
                    holiday = holiday_overtimes(contract, day_from + timedelta(days=day))
                    rest = rest_overtimes(contract, day_from + timedelta(days=day))
                if not contract.multi_schedule:
                    working_hours_on_day = contract.resource_calendar_id._attendance_intervals(datetime.combine((day_from + timedelta(days=day)), datetime.min.time()).replace(tzinfo=pytz.UTC), datetime.combine((day_from + timedelta(days=day)), datetime.max.time()).replace(tzinfo=pytz.UTC))
                    if working_hours_on_day:
                        #the employee had to work
                        leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day))
                        if leave_type:
                            hours = 0
                            for w in working_hours_on_day:
                                hours +=(w[1] - w[0]).seconds/3600
                            #if he was on leave, fill the leaves dict
                            leave_type_name = leave_type.name.replace(' ','_')
                            if leave_type in leaves:
                                leaves[leave_type_name]['number_of_days'] += 1.0
                                leaves[leave_type_name]['number_of_hours'] += hours
                            else:
                                leaves[leave_type_name] = {'work_entry_type_id': leave_type.work_entry_type_id.id,'sequence': 10, 'number_of_days': 1.0,'number_of_hours': hours,'contract_id': contract.id,}
                if absent:
                    if 'Absents' in absents:
                        absents['Absents']['number_of_days'] += 1.0
                        absents['Absents']['number_of_hours'] += absent
                    else:
                        absents['Absents'] = {'work_entry_type_id': self.env.ref('hr_overtime.work_entry_type_absent').id,'sequence': 11, 'number_of_days': 1.0,'number_of_hours': absent,'contract_id': contract.id,}
                if late:
                    if 'Lates' in lates:
                        lates['Lates']['number_of_days'] += 0
                        lates['Lates']['number_of_hours'] += late
                    else:
                        lates['Lates'] = {'work_entry_type_id': self.env.ref('hr_overtime.work_entry_type_sign_in').id,'sequence': 12,'code': 'Lates','number_of_days': 0,'number_of_hours': late,'contract_id': contract.id,}
                if early:
                    if 'Earlys' in earlys:
                        earlys['Earlys']['number_of_days'] += 0
                        earlys['Earlys']['number_of_hours'] += early
                    else:
                        earlys['Earlys'] = {'work_entry_type_id': self.env.ref('hr_overtime.work_entry_type_sign_out').id,'sequence': 13,'code': 'Earlys','number_of_days': 0,'number_of_hours': early,'contract_id': contract.id,}
                if holiday:
                    if 'Holidays' in holidays:
                        holidays['Holidays']['number_of_days'] += 0
                        holidays['Holidays']['number_of_hours'] += holiday
                    else:
                        holidays['Holidays'] = {'work_entry_type_id': self.env.ref('hr_overtime.work_entry_type_ot_holiday').id,'sequence': 14,'code': 'Holidays','number_of_days': 0,'number_of_hours': holiday,'contract_id': contract.id,}
                if rest:
                    if 'Rests' in rests:
                        rests['Rests']['number_of_days'] += 0
                        rests['Rests']['number_of_hours'] += rest
                    else:
                        rests['Rests'] = {'work_entry_type_id': self.env.ref('hr_overtime.work_entry_type_ot_normal').id,'sequence': 15,'code': 'Rests','number_of_days': 0,'number_of_hours': rest,'contract_id': contract.id,}
            absents = [value for key,value in absents.items()]
            attends = [value for key,value in attends.items()]
            lates = [value for key,value in lates.items()]
            earlys = [value for key,value in earlys.items()]
            holidays = [value for key,value in holidays.items()]
            rests = [value for key,value in rests.items()]
            leaves = [value for key,value in leaves.items()]
            res += absents + attends + lates + earlys + holidays + rests + leaves
        return res

class schedule_weekend(models.Model):

    _name = 'schedule.weekend'
    _description = 'Schedule Weekend'

    name = fields.Char(string='Name', required=True)
    date = fields.Date(string='Date')
    employee_id = fields.Many2one('hr.employee')

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _check_undefined_slots(self, work_entries, payslip_run):
        return