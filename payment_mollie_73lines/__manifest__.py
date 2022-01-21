# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Mollie Payment Acquirer',
    'category': 'Payment Gateway',
    'summary': 'Payment Acquirer: Mollie Implementation',
    'version': '13.0.1.0.1',
    'author': '73Lines',
    'description': """Mollie Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/mollie.xml',
        'views/payment_acquirer.xml',
        'data/mollie.xml',
    ],
    'images': [
        'static/description/mollie_payment_gateway_banner.png',
    ],
    'price': 49.99,
    'license': 'Other proprietary',
    'currency': 'EUR',
}
