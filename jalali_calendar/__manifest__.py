# -*- coding: utf-8 -*-
{
    'name': "jalali-calendar",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'web', 'survey', 'web_gantt', 'event'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/g2j.sql',
        'data/j2quarter.sql',
        'static/src/xml/survay_kanban.xml',
        'static/src/xml/event_kanban.xml',
        'static/src/xml/sale_portal.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            
            'jalali_calendar/static/src/js/main.js',
            'jalali_calendar/static/src/js/persian-date.js',
            'jalali_calendar/static/src/js/farvardin.js',
            
            'jalali_calendar/static/src/js/activity_mail_duedate.js',
            'jalali_calendar/static/src/js/datetimepicker_service.js',
            'jalali_calendar/static/src/js/loader.js',

            'jalali_calendar/static/src/xml/gant_calendar.xml',
            'jalali_calendar/static/src/xml/activity_mail_duedate.xml',

        ],
        'jalali_calendar.calendar_persian':[
            'jalali_calendar/static/src/js/format_utils.js',

            'jalali_calendar/static/src/js/list.js',

            'jalali_calendar/static/src/js/searchbar_utils.js',
            'jalali_calendar/static/src/js/search_model.js',

            'jalali_calendar/static/src/js/datetime_field.js',
            'jalali_calendar/static/src/js/jdatetime.js',

            'jalali_calendar/static/src/js/calendar_hook.js',
            'jalali_calendar/static/src/js/jfullcalendar.js',


            'jalali_calendar/static/src/js/gantt_renderer.js',
            'jalali_calendar/static/src/js/grid_model.js',
            'jalali_calendar/static/src/js/kanban_record.js',
        ]
    }
}

