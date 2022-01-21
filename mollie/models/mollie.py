# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

""" This file manages all the operations and the functionality of the gateway
integration """

import json
import logging
import urllib.parse
import werkzeug
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_mollie_73lines.controllers.main import\
    MollieController
from odoo import fields, models
from odoo.tools.translate import _
import requests

_logger = logging.getLogger(__name__)


class AcquirerMollie(models.Model):

    """ Class to handle all the functions required in integration """
    _inherit = 'payment.acquirer'

    def _get_mollie_urls(self, environment):
        """ Mollie URLS """
        if environment == 'prod':
            return {
                'mollie_form_url':
                'https://api.mollie.nl/v1/payments',
            }
        else:
            return {
                'mollie_form_url':
                'https://api.mollie.nl/v1/payments',
            }

    provider = fields.Selection(selection_add=[('mollie_73lines',
                                                'Mollie')])
    mollie_api_key = fields.Char('Mollie Api Key',
                                 required_if_provider='mollie_73lines')

    def mollie_73lines_form_generate_values(self, values):
        """ Gathers the data required to make payment """
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        headers = {'Authorization': 'Bearer' + ' ' + self.mollie_api_key,
                   "Content-Type": "application/json; charset=utf-8"
                   }
        mollie_tx_values = dict(values)
        data = {"description": 'Payment',
                "amount": values['amount'] or '',
                'metadata': {
                    'order_nr': values['reference']
                },
                "redirectUrl":  '%s' % urllib.parse.urljoin
                (base_url, MollieController.WebhookUrl),
                "webhookUrl":  '%s' % urllib.parse.urljoin
                (base_url, MollieController.WebhookUrl),
                }
        data = json.dumps(data)
        mollie_tx_values.update(json.loads(data))
        if mollie_tx_values['metadata']['order_nr'] != '/':
            environment = 'prod' if self.state == 'enabled' else 'test'
            url = self._get_mollie_urls(environment)['mollie_form_url']
            a = requests.post(url, data=data, headers=headers)
            if not json.loads(a.text)['id']:
                return_url = '%s' % urllib.parse.urljoin(base_url,
                                                  MollieController.CancelUrl
                                                  )
                werkzeug.utils.redirect(return_url)
            else:
                mollie_tx_values.update(json.loads(a.text))
        return mollie_tx_values

    def mollie_73lines_get_form_action_url(self):
        """ Get the form url of payulatam"""
        return '/payment/mollie/return/'


class Txmollie(models.Model):

    """ Handles the functions for validation after transaction is processed """
    _inherit = 'payment.transaction'

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    def _mollie_73lines_form_get_tx_from_data(self, data):
        """ Given a data dict coming from mollie, verify it and find '
        'the related transaction record. Create a payment method if '
        'an alias is returned."""

        if data['id']:
            reference = data['metadata']['order_nr']
            if not reference:
                error_msg = _(
                    'mollie: received data with missing reference (%s)'
                ) % (reference)
                _logger.info(error_msg)
                raise ValidationError(error_msg)

            # find tx -> @TDENOTE use txn_id ?
            transaction = self.search([('reference', '=', reference)])

            if not transaction:
                error_msg = (_('Mollie: received data for reference %s; no '
                               'order found') % (reference))
                raise ValidationError(error_msg)
            elif len(transaction) > 1:
                error_msg = (_('Mollie: received data for reference %s; '
                               'multiple orders found') % (reference))
                raise ValidationError(error_msg)
            return transaction

    def _mollie_73lines_form_validate(self, data):
        """ Verify the validity of data coming from mollie"""
        res = {}
        if data['id']:
            status = data['status']
            if status in ['paid']:
                _logger.info(
                    'Validated mollie payment for tx %s: set as '
                    'done' % (self.reference))
                #self.write({
                 #   'payment_date': fields.datetime.now(),
                #})
                self._set_transaction_done()
                return True
            else:
                error = 'Received unrecognized data for mollie payment %s,'\
                    ' set as error' % (self.reference)
                _logger.info(error)
                res.update(state_message=error)
                self.write(res)
                self._set_transaction_error(error)
                return False
