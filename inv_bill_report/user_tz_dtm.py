import pytz
from odoo.exceptions import UserError

def get_tz_date_time_str(self,dtm,user_id=False):
    return dtm.astimezone(pytz.timezone(get_timezone(self,user_id))).strftime(get_date_time_format(self,user_id))

def get_date_str(self,dt,user_id=False):
    return dt.strftime(get_date_format(self,user_id))

def get_language(self,user_id=False):
    self = user_id and self.sudo(user_id) or self
    return self.env['res.lang'].sudo().search([('code','=',self.env.user.lang or 'en_US')])
    
def get_date_format(self,user_id=False):
    return get_language(self,user_id).date_format

def get_time_format(self,user_id=False):
    return get_language(self,user_id).time_format
    
def get_date_time_format(self,user_id=False):
    langauge_id = get_language(self,user_id)
    return f"{langauge_id.date_format} {langauge_id.time_format}"
    
def get_timezone(self,user_id=False):
    self = user_id and self.sudo(user_id) or self
    tz =  self.env.user.tz
    if not tz:
        tz_info = f""
        country_id = self.env.user.country_id or self.env.user.company_id.country_id
        if country_id:
            zones = '\n'.join(pytz.country_timezones(country_id.code))
            tz_info  = f"As per country ({country_id.display_name}) defined in user / company the timezone may comes like.\n * {zones}"
        raise UserError(f"Please set Timezone for user '{self.env.user.display_name}'\n\n" \
                        f"Settings -> Users & Companies -> Users -> {self.env.user.display_name} -> Preferences -> Localization -> Timezone" \
                        f"\n\n{tz_info}")
    return tz
    
def get_tz_dtm_detals(self,user_id=False):
    return {'timezone':get_timezone(self,user_id),
            'date_format':get_date_format(self,user_id),
            'time_format':get_time_format(self,user_id),
            'date_time_format':get_date_time_format(self,user_id),
            'langauge':get_language(self,user_id)
            }


    
        