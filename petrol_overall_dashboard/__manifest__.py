{
    'name': 'Fuel Station Management Dashboard',
    'version': '17.1',
    'category': 'Extra Tools',
    'website': 'www.appscomp.com',
    'images': ['static/description/banner.png'],
    #'images': ['static/description/banner.gif'],
    'author': 'AppsComp Widgets Pvt Ltd',
    'summary': 'The dashboard maintains and displays the values of nozzle-wise petrol, diesel, and oil sales, along '
               'with the total amounts sold and purchased. It also provides insights into profit and loss, as well as '
               'shift-wise amount collections, represented in visually appealing graphs. All relevant data is captured '
               'and presented in an attractive dashboard, offering various filter options for users to analyze and '
               'track performance effectively.',
    'depends': ['base', 'purchase', 'sale', 'stock', 'petrol_station_dashboard', 'hr'],
    'data': [
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
            'petrol_overall_dashboard/static/src/css/dashboard.css',
            'petrol_overall_dashboard/static/src/js/dashboard.js',
            'petrol_overall_dashboard/static/src/xml/dashboard.xml'
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': '150',
    #'price': '91.59',
    'currency': 'EUR',
}
