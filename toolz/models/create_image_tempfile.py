# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from odoo import models, api, _
from odoo.exceptions import ValidationError
try:
    import tempfile
    import xlrd
except Exception:
    raise ValidationError(_('xlrd is required to install this module'))


class CreateTempfile(models.Model):
    _name = 'create.tempfile'
    _auto = False

    @api.multi
    def create_tempfile(self, data, path=False):
        return create_tempfile(data, path)


def create_tempfile(data, path=False):
    if not path:
        path = '/file.png'
    try:
        file_path = tempfile.gettempdir() + path
        f = open(file_path, 'wb')
        f.write(base64.b64decode(data))
        f.close()

    except Exception as e:
        raise ValidationError(
            _('File format incorrect, please upload file image format'))

    return file_path
