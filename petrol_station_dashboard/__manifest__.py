{
    'name': 'Fuel Station Management System',
    'version': '17.1',
    'summary': 'The fuel station management system assists users in managing pumps, nozzles, staff shifts, and daily '
               'fuel collections from allocated personnel. It tracks credit-based sales information, including vehicle'
               ' numbers, and generates various reports such as Day End, Shift-wise, Payment Mode, Stock Summary,'
               ' and Nozzle Summary in PDF and Excel formats. Additionally, it facilitates purchase management by'
               ' automatically calculating unit prices based on entered subtotal and total quantity. The system also '
               'handles expenses, sales, stocks inventory, and accounting tasks, providing comprehensive ledger reports'
               ' for effective tracking.',
    'images': ['static/description/banner.png'],
    'sequence': 1,
    'description': """ The fuel station management system efficiently handles pump and nozzle management, staff shifts,
     and daily fuel collections, along with credit-based sales tracking including vehicle numbers. It generates diverse
      reports like Day End and Shift-wise summaries in PDF and Excel formats. Moreover, it streamlines purchase 
      management by automatically calculating unit prices and offers comprehensive accounting features with ledger 
      reports for thorough tracking.""",
    'author': "AppsComp Widgets Pvt Ltd",
    'website': "www.appscomp.com",
    'category': 'Extra Tools',
    'license': 'OPL-1',
    'depends': ['hr', 'stock', 'sale', 'hr_contract', 'hr_expense', 'fleet', 'sale_stock', 'purchase', 'account'],
    'data': [
        'security/security.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/pump_data.xml',
        'views/fuel_pump.xml',
        'views/product_view.xml',
        'views/employee_view.xml',
        'views/hr_employee.xml',
        'views/petrol_pump_line.xml',
        'wizard/bouches_entry.xml',
        'wizard/create_sale_order_wizard.xml',
        'wizard/customer_outstanding.xml',
        'wizard/customer_summary.xml',
        'wizard/day_end_report.xml',
        'wizard/detailed_report.xml',
        'wizard/month_daily_report.xml',
        'wizard/payment_mode_report.xml',
        'wizard/shift_report.xml',
        'report/customer_outstanding_report.xml',
        'report/customer_summary_report.xml',
        'report/detailed_report.xml',
        'report/fuel_day_end_report_template.xml',
        'report/payment_mode_report_template.xml',
        'report/purchase_order_report.xml',
        'report/shift_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'petrol_station_dashboard/static/src/css/fuel_style.css',
            'petrol_station_dashboard/static/src/js/fuel_dashboard.js',
            'petrol_station_dashboard/static/src/xml/fuel_dashboard.xml',
        ]
    },
    'demo': [],
    'qweb': [],
    'price': '575',
    #'price': '477.42',
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
}
