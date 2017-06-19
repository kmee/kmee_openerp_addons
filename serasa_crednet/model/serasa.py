# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Luiz Felipe do Divino (luiz.divino@kmee.com.br)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from ..serasa import consulta
from datetime import datetime
import openerp.addons.decimal_precision as dp


class Serasa(models.Model):

    _name = 'consulta.serasa'
    _order = "id desc"

    @api.multi
    @api.depends('cheque_ids', 'pefin_ids', 'refin_ids', 'protesto_ids')
    def _count_serasa(self):
        for rec in self:
            for pefin in rec.pefin_ids:
                rec.pefin_count += 1
                rec.pefin_sum += pefin.value
            for refin in rec.refin_ids:
                rec.refin_count += 1
                rec.refin_sum += refin.value
            for cheque in rec.cheque_ids:
                rec.cheque_count += 1
                rec.cheque_sum += cheque.value
            for protesto in rec.protesto_ids:
                rec.protesto_count += 1
                rec.protesto_sum += protesto.value

    data_consulta = fields.Datetime(
        'Data Consulta',
        default=datetime.now(),
        readonly=True
    )
    status = fields.Char('Estado', readonly=True)
    partner_id = fields.Many2one('res.partner', required=True)
    partner_fundation = fields.Date('Data de Fundação', readonly=True)
    partner_identification = fields.Char('Documento', readonly=True)
    string_retorno = fields.Text('StringRetorno')

    protesto_count = fields.Integer('Protestos', compute='_count_serasa')
    protesto_sum = fields.Float('Valor', compute='_count_serasa')
    protesto_ids = fields.One2many('serasa.protesto', 'serasa_id')
    protesto_data_inicio = fields.Char("Data Ocorrencia Antiga")
    protesto_data_fim = fields.Char("Data Ultima Ocorrencia")
    protesto_num_ocorrencias = fields.Integer(
        'Total de ocorrências Protestos Estaduais',
        readonly=True
    )
    protesto_valor_total = fields.Float(
        'Valor total Protestos Estaduais',
        readonly=True,
        digits_compute=dp.get_precision('Account')
    )

    pefin_count = fields.Integer('Pefin', compute='_count_serasa')
    pefin_sum = fields.Float('Valor', compute='_count_serasa')
    pefin_ids = fields.One2many('serasa.pefin', 'serasa_id')
    pefin_data_inicio = fields.Char("Data Ocorrencia Antiga")
    pefin_data_fim = fields.Char("Data Ultima Ocorrencia")
    pefin_num_ocorrencias = fields.Integer(
        'Total de ocorrências Pendências Financeiras',
        readonly=True
    )
    pefin_valor_total = fields.Float(
        'Valor total Pendências Financeiras',
        readonly=True,
        digits_compute=dp.get_precision('Account')
    )

    refin_count = fields.Integer('Refin', compute='_count_serasa')
    refin_sum = fields.Float('Valor', compute='_count_serasa')
    refin_ids = fields.One2many('serasa.refin', 'serasa_id')
    refin_data_inicio = fields.Char("Data Ocorrencia Antiga")
    refin_data_fim = fields.Char("Data Ultima Ocorrencia")
    refin_num_ocorrencias = fields.Integer(
        'Total de ocorrências Pendências Financeiras',
        readonly=True
    )
    refin_valor_total = fields.Float(
        'Valor total Pendências Financeiras',
        readonly=True,
        digits_compute=dp.get_precision('Account')
    )

    cheque_count = fields.Integer('Cheques', compute='_count_serasa')
    cheque_sum = fields.Float('Valor', compute='_count_serasa')
    cheque_ids = fields.One2many('serasa.cheque', 'serasa_id')
    cheque_num_ocorrencias = fields.Integer(
        'Total de ocorrências Cheques',
        readonly=True
    )

    def _check_partner(self):
        id_consulta_serasa = self.id
        company = self.env.user.company_id

        if not company.cnpj_cpf:
            from openerp.exceptions import Warning
            raise Warning(
                "O CNPJ da empresa consultante não pode estar em branco."
            )
        elif not self.partner_id.cnpj_cpf:
            from openerp.exceptions import Warning
            raise Warning("O CNPJ/CPF do consultado não pode estar em branco.")

        retorno_consulta = consulta.consulta_cnpj(self.partner_id, company)

        if retorno_consulta == 'Usuario ou senha do serasa invalidos' \
                or retorno_consulta == u"Há inconsistencias nos " \
                                       u"dados enviados, verificar " \
                                       u"o cpf/cnpj e se o cliente é " \
                                       u"empresa ou pessoa fisica":
            from openerp.exceptions import Warning
            raise Warning(retorno_consulta)

        result = self.write({
                'data_consulta': datetime.now(),
                'status': retorno_consulta['status'],
                'string_retorno': retorno_consulta['texto'],
                'partner_fundation': retorno_consulta['fundacao'],
                'partner_identification': self.partner_id.cnpj_cpf,
            })

        if retorno_consulta['total_pefin']:
            self.write({
                'pefin_data_inicio': retorno_consulta['total_pefin']
                ['pefin_inicio'],
                'pefin_data_fim': retorno_consulta['total_pefin']['pefin_fim'],
                'pefin_num_ocorrencias': retorno_consulta['total_pefin'][
                    'num_ocorrencias'],
                'pefin_valor_total': retorno_consulta['total_pefin']['total'],
            })
        else:
            self.write({
                'pefin_num_ocorrencias': 0,
                'pefin_valor_total': 0,
            })

        if retorno_consulta['total_refin']:
            self.write({
                'refin_data_inicio': retorno_consulta['total_refin']
                ['refin_inicio'],
                'refin_data_fim': retorno_consulta['total_refin']['refin_fim'],
                'refin_num_ocorrencias': retorno_consulta['total_refin'][
                    'num_ocorrencias'],
                'refin_valor_total': retorno_consulta['total_refin']['total'],
            })
        else:
            self.write({
                'refin_num_ocorrencias': 0,
                'refin_valor_total': 0,
            })

        if retorno_consulta['total_protesto']:
            self.write({
                'protesto_data_inicio': retorno_consulta['total_protesto']
                ['protesto_inicio'],
                'protesto_data_fim': retorno_consulta['total_protesto']
                ['protesto_fim'],
                'protesto_num_ocorrencias': retorno_consulta['total_protesto'][
                        'num_ocorrencias'],
                'protesto_valor_total': retorno_consulta['total_protesto'][
                        'total'],
            })
        else:
            self.write({
                'protesto_num_ocorrencias': 0,
                'protesto_valor_total': 0,
            })

        if retorno_consulta['total_cheque']:
            self.write({
                'cheque_num_ocorrencias': retorno_consulta['total_cheque'][
                    'num_ocorrencias'],
            })
        else:
            self.write({
                'cheque_num_ocorrencias': 0,
            })

        pefin_obj = self.env['serasa.pefin']
        for pefin in retorno_consulta['pefin']:
            pefin_obj.create({
                'value': pefin['value'],
                'date': pefin['date'],
                'modalidade': pefin['modalidade'],
                'origem': pefin['origem'],
                'contrato': pefin['contrato'],
                'avalista': pefin['avalista'],
                'serasa_id': id_consulta_serasa,
            })

        refin_obj = self.env['serasa.refin']
        for refin in retorno_consulta['refin']:
            refin_obj.create({
                'value': refin['value'],
                'date': refin['date'],
                'modalidade': refin['modalidade'],
                'origem': refin['origem'],
                'contrato': refin['contrato'],
                'avalista': refin['avalista'],
                'serasa_id': id_consulta_serasa,
            })

        protesto_obj = self.env['serasa.protesto']
        for protesto in retorno_consulta['protestosEstados']:
            protesto_obj.create({
                'value': protesto['value'],
                'date': protesto['date'],
                'cartorio': protesto['cartorio'],
                'city': protesto['city'],
                'uf': protesto['uf'],
                'serasa_id': id_consulta_serasa,
            })

        cheque_obj = self.env['serasa.cheque']
        for cheque in retorno_consulta['cheque']:
            cheque_obj.create({
                'value': cheque['value'],
                'date': cheque['date'],
                'num_cheque': cheque['num_cheque'],
                'alinea': cheque['alinea'],
                'serasa_id': id_consulta_serasa,
                'name_bank': cheque['name_bank'],
                'city': cheque['city'],
                'uf': cheque['uf'],
            })

        return result

    @api.model
    def create(self, vals):
        rec = super(Serasa, self).create(vals)
        rec._check_partner()
        return rec


class SerasaProtesto(models.Model):

    _name = 'serasa.protesto'

    cartorio = fields.Char('Cartorio')
    city = fields.Char('Cidade')
    uf = fields.Char('UF')
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    date = fields.Date('Data')
    value = fields.Float('Valor')


class SerasaPefin(models.Model):

    _name = 'serasa.pefin'

    modalidade = fields.Char('Modalidade')
    origem = fields.Char('Origem')
    avalista = fields.Char('Avalista')
    contrato = fields.Char('Contrato')
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    date = fields.Date('Data')
    value = fields.Float('Valor')


class SerasaRefin(models.Model):

    _name = 'serasa.refin'

    modalidade = fields.Char('Modalidade')
    origem = fields.Char('Origem')
    avalista = fields.Char('Avalista')
    contrato = fields.Char('Contrato')
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    date = fields.Date('Data')
    value = fields.Float('Valor')


class SerasaCheque(models.Model):

    _name = 'serasa.cheque'

    num_cheque = fields.Char(u'Número do Cheque')
    alinea = fields.Integer(u'Alínea', default=0)
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    name_bank = fields.Char('Nome do Banco')
    city = fields.Char('Cidade')
    uf = fields.Char('UF')
    date = fields.Date('Data')
    value = fields.Float('Valor', default=0.00)