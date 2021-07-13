from odoo import api, fields, models, _, tools, modules
from odoo.modules import get_module_path
import os
import logging
_logger = logging.getLogger(__name__)


class base_language_update(models.TransientModel):
    _name = "base.language.update"

    module_upgrade = fields.Many2many(
        'ir.module.module', string='Module Upgrade',
        domain=[('state', 'in', ('installed', 'to install', 'to upgrade'))]
    )

    lang = fields.Many2one('res.lang', required=True)

    @api.multi
    def update_language(self):
        _logger.info('act_translate() BEGIN')
        module_domain = [('state', 'in', ('installed', 'to install', 'to upgrade'))]
        lang_code = self.lang.code
        lang_iso_code = self.lang.iso_code
        if self.module_upgrade:
            module_domain.append(('id', 'in', self.module_upgrade._ids))

        module_s = self.env['ir.module.module'].search(module_domain)
        module_lst = module_s.mapped('name')

        # self.env.cr.execute(
        #     "delete from ir_translation where module in %s",
        #     (tuple(module_lst),))
        # self.env.cr.commit

        quick_translate_path = get_module_path('quick_translate')
        quick_translate_i18n_path = os.path.join(quick_translate_path, 'i18n/{}'.format(lang_code))
        for module_name in module_lst:
            translate_file_module_name = module_name + '.po'
            trans_file = os.path.join(quick_translate_i18n_path, translate_file_module_name)

            if not os.path.exists(trans_file):
                trans_file = False

            if not trans_file:
                trans_file = modules.get_module_resource(
                    module_name, 'i18n', '{}.po'.format(lang_code))

            if not trans_file:
                trans_file = modules.get_module_resource(
                    module_name, 'i18n', '{}.po'.format(lang_iso_code))

            if trans_file:
                _logger.info(
                    'module %s: loading translation file (%s) for language %s',
                    module_name, lang_code, lang_code)
                self.env.cr.execute(
                    "delete from ir_translation where module in %s and lang = %s",
                    (tuple(module_lst), lang_code)
                )
                self.env.cr.commit
                tools.trans_load(self._cr, trans_file, lang_code,
                                 verbose=False, module_name=module_name)
        return True

