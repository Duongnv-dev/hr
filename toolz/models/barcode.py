from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError
try:
    import barcode
except ImportError:
    raise ImportError('Need intall module python-barcode')
from barcode.writer import ImageWriter

import base64


class Barcodez(models.Model):
    _name = 'tool.barcodez'

    def barcode(self, code, type):
        if not code:
            pass
        class_ = 'code128'
        if type:
            class_ = type

        EAN = barcode.get_barcode_class(class_)
        ean = EAN(code, writer=ImageWriter())
        fullname = ean.save('/tmp/ean_barcode')
        with open(fullname, "rb") as img_file:
            ean64 = base64.b64encode(img_file.read())
        return ean64

