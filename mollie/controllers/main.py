# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

""" File to manage the functions used while redirection"""

import logging
import json
import ast
import pprint
import werkzeug
from odoo import http
from odoo.http import request
import requests

_logger = logging.getLogger(__name__)


class MollieController(http.Controller):

    """ Handles the redirection back from payment gateway to merchant site """

    ReturnUrl = '/payment/mollie/return/'
    WebhookUrl = 'payment/mollie/webhook/'
    CancelUrl = '/payment/mollie/cancel/'

    def _get_return_url(self, **post):
        """ Extract the return URL from the data coming from mollie. """
        return_url = post.pop('return_url', '')
        if not return_url:
            return_url = '/payment/process'
        return return_url

    def mollie_validate_data(self, **post):
        """ Validate the data coming from mollie. """
        res = False
        reference = post['metadata']['order_nr']
        if reference:
            _logger.info('mollie: validated data')
            res = request.env['payment.transaction'].sudo().form_feedback(
                post, 'mollie_73lines')
            return res

    @http.route('/payment/mollie/webhook', type='http', auth='none',
                methods=['GET', 'POST'], csrf=False, website=True)
    def mollie_webhook(self, **post):
        """ Gets the Post data from mollie after making payment """
        _logger.info('Beginning mollie Return form_feedback with post data'
                     ' %s', pprint.pformat(post))  # debug
        acquirer = request.env['payment.acquirer'].sudo().search(
            [('provider', '=', 'mollie_73lines')])
        if acquirer and post:
            environment = 'prod' if acquirer.state == 'enabled' else 'test'
            url = acquirer.sudo()._get_mollie_urls(environment)[
                'mollie_form_url'
            ]
            headers = {'Authorization': 'Bearer' + ' ' +
                       acquirer.mollie_api_key,
                       "Content-Type": "application/json; charset=utf-8"
                       }
            resp = requests.get(str(url) + '/' + post['id'], headers=headers)
            post.update(json.loads(resp.text))
            return_url = self._get_return_url(**post)
            self.mollie_validate_data(**post)
        else:
            return_url = self._get_return_url(**post)
            return werkzeug.utils.redirect(return_url)

    @http.route('/payment/mollie/return', type='http', auth='none',
                methods=['GET', 'POST'], csrf=False, website=True)
    def mollie_return(self, **post):
        """ Returns the url of the payment page of mollie payment acquirer"""
        links = post['links']
        links = ast.literal_eval(json.loads(json.dumps(links)))
        _logger.info('Beginning mollie Return form_feedback with post data %s',
                     pprint.pformat(post))  # debug
        if links['paymentUrl']:
            return werkzeug.utils.redirect(links['paymentUrl'])
        else:
            return_url = self._get_return_url(**post)
            return werkzeug.utils.redirect(return_url)

    @http.route('/payment/mollie/cancel', type='http', auth="none",
                csrf=False, website=True)
    def mollie_cancel(self, **post):
        """ When the user cancels its mollie payment: GET on this route """
        _logger.info('Beginning mollie cancel with post data %s',
                     pprint.pformat(post))  # debug
        return_url = self._get_return_url(**post)
        return werkzeug.utils.redirect(return_url)
