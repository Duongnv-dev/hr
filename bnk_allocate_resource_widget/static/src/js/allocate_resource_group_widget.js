odoo.define('allocate.resource.group.widget', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;


var AllocateResourceGroupWidget = AbstractField.extend({
    events: _.extend({
        'click .open-button': '_open_parent_tr',
        'click .close-button': '_close_parent_tr',
    }, AbstractField.prototype.events),
    supportedFieldTypes: ['char'],

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     * @returns {boolean}
     */
    isSet: function() {
        return true;
    },

    _get_data: function() {
        var _id = self.view.datarecord.id;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @override
     */
    _render: function() {
        var self = this;

//        if (!info) {
//            this.$el.html('');
//            return;
//        }

        var _id = self.recordData.id;
        var el = this.$el;
//        var groupby = 'project_id';
//        var groupby_label = ['Project', 'Employee'];

        this._rpc({
                model: 'report.allocate.resource',
                method: 'get_allocate_resource_group_widget_data',
                args: [_id],
            }).then(function (grid_dict) {
                if (Object.keys(grid_dict).length === 0) {
                return;
                }
               el.html(QWeb.render('AllocateResourceGroupTemplate', {
                    date_list: grid_dict['date_list'],
                    allocate_dict: grid_dict['allocate_dict'],
                    holiday_list: grid_dict['holiday_list'],
                    group_field_key_dict: grid_dict['group_field_key_dict'],
                    group_field_value_dict: grid_dict['group_field_value_dict'],
                    grid: grid_dict['grid'],
                    month_list: grid_dict['month_list'],
                    groupby: grid_dict['groupby'],
                    groupby_label: grid_dict['groupby_label'],
                    group_by_project: grid_dict['group_by_project'],
                    public_holiday_list: grid_dict['public_holiday_list'],
                    sum_line: grid_dict['sum_line']
                }));
            });
    },
    _open_parent_tr: function (event) {
        var self = this;
        var data_id = event.target.getAttribute('data-line-id');
        var el = this.$el;
        var found = $('.FindMe', el);
        var sub_lines = document.querySelectorAll('[parent-line-id="' + data_id + '"]');
        var buttons = document.querySelectorAll('[data-line-id="' + data_id + '"]');
        if (sub_lines.length === 0){
            return;
        }
        sub_lines.forEach(function(element) {
            element.classList.remove("hide-element");
        });

        buttons.forEach(function(button) {
            if (button.classList.contains("hide-element")){
                button.classList.remove("hide-element");
            }
            else {
                button.classList.add("hide-element");
            }

        });
    },

    _close_parent_tr: function (event) {
        var self = this;
        var data_id = event.target.getAttribute('data-line-id');
        var el = this.$el;
        var found = $('.FindMe', el);
        var sub_lines = document.querySelectorAll('[parent-line-id="' + data_id + '"]');
        var buttons = document.querySelectorAll('[data-line-id="' + data_id + '"]');
        if (sub_lines.length === 0){
            return;
        }
        sub_lines.forEach(function(element) {
            element.classList.add("hide-element");
        });

        buttons.forEach(function(button) {
            if (button.classList.contains("hide-element")){
                button.classList.remove("hide-element");
            }
            else {
                button.classList.add("hide-element");
            }

        });
    },

});

field_registry.add('allocate_resource_group', AllocateResourceGroupWidget);

return {
    AllocateResourceGroupWidget: AllocateResourceGroupWidget
};

});
