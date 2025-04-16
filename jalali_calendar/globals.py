import datetime
import jdatetime
import dateutil
import math
import copy

class jdate_utils:

    @staticmethod
    def get_year(date):
        date_from = jdatetime.datetime(date.year, 1, 1)
        date_to = jdatetime.datetime(date.year+1, 1, 1) - jdatetime.timedelta(seconds=1)

        return date_from, date_to


    @staticmethod
    def get_quarter(date):
        quarter_number = jdate_utils.get_quarter_number(date)

        month_from = ((quarter_number - 1) * 3) + 1
        date_from = jdatetime.datetime(date.year, month_from, 1)

        if quarter_number == 1 or quarter_number == 2:
            date_to = jdatetime.datetime(date.year, month_from+2, 31, 23, 59, 59)
        elif quarter_number == 3:
            date_to = jdatetime.datetime(date.year, month_from+2, 30, 23, 59, 59)
        else:
            if date.isleap():
                date_to = jdatetime.datetime(date.year, month_from+2, 30, 23, 59, 59)
            else:
                date_to = jdatetime.datetime(date.year, month_from+2, 29, 23, 59, 59)

        return date_from, date_to


    @staticmethod
    def jget_quarter(date):
        
        date = jdatetime.datetime.fromgregorian(year=date.year, month=date.month, day=date.day)
        quarter_number = jdate_utils.get_quarter_number(date)

        month_from = ((quarter_number - 1) * 3) + 1
        date_from = jdatetime.datetime(date.year, month_from, 1)

        if quarter_number == 1 or quarter_number == 2:
            date_to = jdatetime.datetime(date.year, month_from+2, 31, 23, 59, 59)
        elif quarter_number == 3:
            date_to = jdatetime.datetime(date.year, month_from+2, 30, 23, 59, 59)
        else:
            if date.isleap():
                date_to = jdatetime.datetime(date.year, month_from+2, 30, 23, 59, 59)
            else:
                date_to = jdatetime.datetime(date.year, month_from+2, 29, 23, 59, 59)

        return jdatetime.date.togregorian(date_from), jdatetime.date.togregorian(date_to)

    @staticmethod
    def get_month(date):
        date_from = jdatetime.datetime(date.year, date.month, 1)

        if date.month <= 6:
            date_to = jdatetime.datetime(date.year, date.month, 31, 23, 59, 59)
        elif date.month <= 11:
            date_to = jdatetime.datetime(date.year, date.month, 30, 23, 59, 59)
        else:
            if date.isleap():
                date_to = jdatetime.datetime(date.year, date.month, 30, 23, 59, 59)
            else:
                date_to = jdatetime.datetime(date.year, date.month, 29, 23, 59, 59)
        return date_from, date_to
    
    @staticmethod
    def jget_month(date):
        
        jdate_org = jdatetime.datetime.fromgregorian(year=date.year, month=date.month, day=date.day)
        jdate_from = copy.deepcopy(jdate_org)
        jdate_from._date__day=1
        day = 0
        if jdate_org.month <= 6:
            day = 31
        elif jdate_org.month <= 11:
            day = 30
        else:
            if jdate_org.isleap():
                day = 30
            else:
                day = 29
        jdate_to = copy.deepcopy(jdate_org)
        jdate_to._date__day = day      
        return jdatetime.date.togregorian(jdate_from), jdatetime.date.togregorian(jdate_to)


    @staticmethod
    def get_week(date):
        date_from = jdatetime.datetime(date.year, date.month, date.day)
        while date_from.weekday() != 0:
            date_from -= jdatetime.timedelta(days=1)
        
        date_to = (date_from + jdatetime.timedelta(days=6)).replace(hour=23, minute=59, second=59)

        return date_from, date_to


    @staticmethod
    def get_day(date):
        date_from = jdatetime.datetime(date.year, date.month, date.day)
        date_to = date_from.replace(hour=23, minute=59, second=59)

        return date_from, date_to


    @staticmethod
    def get_quarter_number(date):
        return math.ceil(date.month / 3)


    @staticmethod
    def get_quarter_name(date, lang):
        if lang == 'en_US':
            quarter_names = {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'}
        else:
            quarter_names = {1: 'بهار', 2: 'تابستان', 3: 'پاییز', 4: 'زمستان'}
        return quarter_names[jdate_utils.get_quarter_number(date)]


    @staticmethod
    def get_month_name(date, lang):
        if lang == 'en_US':
            month_names = {1: 'Farvardin', 2: 'Ordibehesht', 3: 'Khordad', 4: 'Tir', 5: 'Mordad', 6: 'Shahrivar', 7: 'Mehr', 8: 'Aban', 9: 'Azar', 10: 'Dey', 11: 'Bahman', 12: 'Esfand'}
        else:
            month_names = {1:"فروردین", 2:"اردیبهشت", 3:"خرداد", 4:"تیر", 5:"مرداد", 6:"شهریور", 7:"مهر", 8:"آبان", 9:"آذر", 10:"دی", 11:"بهمن", 12:"اسفند"}
        return month_names[date.month]


    @staticmethod
    def get_weekday_name(date, lang):
        if lang == 'en_US':
            weekday_names = {1: 'Saturday', 2: 'Sunday', 3: 'Monday', 4: 'Tuesday', 5: 'Wednesday', 6: 'Thursday', 7: 'Friday'}
        else:
            weekday_names = {1: 'شنبه', 2: 'یک‌شنبه', 3: 'دوشنبه', 4: 'سه‌شنبه', 5: 'چهارشنبه', 6: 'پنج‌شنبه', 7: 'جمعه'}
        return weekday_names[date.weekday() + 1]


    @staticmethod
    def get_date_range(start, end, step):
        def get_next_month(dt):
            days_of_month = {1: 31, 2: 31, 3: 31, 4: 31, 5: 31, 6: 31, 7: 30, 8: 30, 9: 30, 10: 30, 11: 30, 12: jdate_utils.get_month(jdatetime.datetime(dt.year, 12, 1))[1].day}
            
            year = dt.year if dt.month <= 11 else dt.year + 1
            month = dt.month + 1 if dt.month <= 11 else 1
            if dt.day == days_of_month[dt.month]:
                day = days_of_month[month]
            else:
                day = dt.day
                
            return jdatetime.datetime(year,month,day)

        def get_timedelta(dt, step):
            if step == dateutil.relativedelta.relativedelta(days=1):
                return jdatetime.timedelta(days=1)
            elif step == datetime.timedelta(7):
                return jdatetime.timedelta(days=7)                            
            elif step == dateutil.relativedelta.relativedelta(months=1):
                return get_next_month(dt) - dt.replace(tzinfo=None)
            elif step == dateutil.relativedelta.relativedelta(months=3):
                delta = 0
                temp_dt = dt.replace(tzinfo=None)
                for _ in range(3):
                    next_month = get_next_month(temp_dt)
                    delta += (next_month - temp_dt).days
                    temp_dt = next_month
                return jdatetime.timedelta(days=delta)
            elif step == dateutil.relativedelta.relativedelta(years=1):
                return dt.replace(year=dt.year+1, tzinfo=None) - dt.replace(tzinfo=None)

        result = []
        dt = start
        while dt <= end:
            result.append(dt)
            dt += get_timedelta(dt, step)
        return result
    
    def e2p(persiannumber):
    
        number={
            '0':'۰',
            '1':'۱',
            '2':'۲',
            '3':'۳',
            '4':'۴',
            '5':'۵',
            '6':'۶',
            '7':'۷',
            '8':'۸',
            '9':'۹',
    }

        for i,j in number.items():
            persiannumber=persiannumber.replace(i,j)
            
        return persiannumber

    @staticmethod
    def display_format_changer(df):
        return {
            "hh:00 dd MMM": "%d %b %H",
            "dd MMM yyyy": "%d %b %Y",
            "'W'w YYYY": "%A %Y",
            "MMMM yyyy": "%b %Y",
            "QQQ yyyy": "%b %Y",
            "yyyy": "%Y",
        }.get(df, "%d %b %Y")