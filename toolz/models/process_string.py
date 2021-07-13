# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import re

class ProcessString(models.Model):
    _name = 'process.string'
    _auto = False

    @api.model
    def no_accent(self, src):
        INTAB = u"ạảãàáâậầấẩẫăắằặẳẵóòọõỏôộổỗồốơờớợởỡéèẻẹẽêếềệểễúùụủũưựữửừứíìịỉĩýỳỷỵỹđẠẢÃÀÁÂẬẦẤẨẪĂẮẰẶẲẴÓÒỌÕỎÔỘỔỖỒỐƠỜỚỢỞỠÉÈẺẸẼÊẾỀỆỂỄÚÙỤỦŨƯỰỮỬỪỨÍÌỊỈĨÝỲỶỴỸĐ"
        INTAB = [ch for ch in INTAB]

        OUTTAB = "a" * 17 + "o" * 17 + "e" * 11 + "u" * 11 + "i" * 5 + "y" * 5 + "d" + \
                 "A" * 17 + "O" * 17 + "E" * 11 + "U" * 11 + "I" * 5 + "Y" * 5 + "D"

        r = re.compile("|".join(INTAB))
        replaces_dict = dict(zip(INTAB, OUTTAB))

        return r.sub(lambda m: replaces_dict[m.group(0)], src)