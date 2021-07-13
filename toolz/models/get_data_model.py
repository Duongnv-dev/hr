# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import ValidationError

class GetDataModel(models.Model):
    _name = 'get.data.model'

    # Hàm trả về dict có key là các field chỉ định thuộc model và giá trị là id
    # model_table: tên bảng
    # key_field: field làm key để search data
    # key_fields: keys output
    # value_list: list làm domain search
    # active: Boolean có search active hay ko?
    # is_trim: có search tương đối hay không?
    # ex: partner_dict = self.env['get.data.model'].get_dict_data('res_partner', 'name', ['name', 'email', 'phone'], [], active=False, is_trim=True)

    def get_dict_data(self, model_table, key_field, key_fields, value_list, active=False, is_trim=False):
        data_dict = {}
        key_fields.append('id')
        if is_trim:
            select_strim = []
            for k in key_fields:
                if k == 'id':
                    select_strim.append(k)
                else:
                    k_strim = 'trim(lower({}::text)) as {}'.format(k, k)
                    select_strim.append(k_strim)
            select_list_string = ', '.join(select_strim)
        else:
            select_list_string = ', '.join(key_fields)
        where_clause = """1=1 """
        if value_list:
            value_tuple = "('" + "','".join(value_list) + "')"
            if active:
                if is_trim:
                    where_clause += """and active is True and trim(lower({})) in {}""".format(key_field, value_tuple)
                else:
                    where_clause += """and active is True and {} in {}""".format(key_field, value_tuple)
            else:
                if is_trim:
                    where_clause += """and trim(lower({})) in {}""".format(key_field, value_tuple)
                else:
                    where_clause += """and {} in {}""".format(key_field, value_tuple)
        query = u"""
                    select {} from {}
                    where {}
                """.format(select_list_string, model_table, where_clause)
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        key_fields.remove('id')
        if len(key_fields) == 1:
            for s in datas:
                data_dict[s[key_fields[0]]] = s['id']
        else:
            for s in datas:
                tupl = tuple([s[key] for key in key_fields])
                data_dict[tupl] = s['id']
        return data_dict


