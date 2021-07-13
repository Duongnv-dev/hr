odoo.define('allocate.resource.widget', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;


var AllocateResourceWidget = AbstractField.extend({
    events: _.extend({
        'change .percent-input': '_onchange_percent_input',
        'change .billable-checkbox': '_onchange_billable_checkbox',
        'click .save-button': '_save_action',
        'click .open-date-detail': '_show_detail',
    }, AbstractField.prototype.events),
    supportedFieldTypes: ['char'],

    isSet: function() {
        return true;
    },

    _get_data: function() {
        var _id = self.view.datarecord.id;
    },

    _render: function() {
        var self = this;

        var _id = self.recordData.id;
        var el = this.$el;

        this._rpc({
                model: 'report.allocate.resource',
                method: 'get_allocate_resource_widget_data',
                args: [_id],
            }).then(function (grid_dict) {
                if (Object.keys(grid_dict).length === 0) {
                return;
                }
               el.html(QWeb.render('AllocateResourceTemplate', {
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
                    show_detail: grid_dict['show_detail'],
                    editable: grid_dict['editable'],
                    ot: grid_dict['ot'],
                    public_holiday_list: grid_dict['public_holiday_list'],
                    sum_line: grid_dict['sum_line']
                }));
            });
    },

    _onchange_percent_input: function (event) {
        var self = this;
        event.target.classList.add('edited');

    },

    _onchange_billable_checkbox: function (event) {
        var self = this;

        var project_id = event.target.getAttribute('project_id');
        var employee_id = event.target.getAttribute('employee_id');
        var date = event.target.getAttribute('date');
        var checked = event.target.checked;

        var allocate_inputs = document.querySelectorAll(
        '[project_id="' + project_id + '"]' + '[employee_id="' + employee_id + '"]' + '[date="' + date + '"]' + '[type="number"]');

        if (allocate_inputs.length > 0) {
            allocate_inputs[0].classList.add('edited');

            var billable_class = 'billable-class';

            if (!checked){
                billable_class = 'none-billable-class';
            }

            var percent = parseInt(allocate_inputs[0].value || '0');
            if (percent === 0){
                billable_class = '';
            }

            allocate_inputs[0].classList.remove('billable-class');
            allocate_inputs[0].classList.remove('none-billable-class');

            event.target.classList.remove('billable-class');
            event.target.classList.remove('none-billable-class');

            event.target.parentElement.classList.remove('billable-class');
            event.target.parentElement.classList.remove('none-billable-class');

            if (billable_class){
                allocate_inputs[0].classList.add(billable_class);

                event.target.classList.add(billable_class);

                event.target.parentElement.classList.add(billable_class);
            }

            if (checked) {
                allocate_inputs[0].setAttribute("billable", "1");

//                allocate_inputs[0].classList.add('billable-class');
//
//                event.target.classList.add('billable-class');
//
//                event.target.parentElement.classList.add('billable-class');
//
//                allocate_inputs[0].classList.remove('none-billable-class');
//
//                event.target.classList.remove('none-billable-class');
//
//                event.target.parentElement.classList.remove('none-billable-class');
            }
            else {
                allocate_inputs[0].setAttribute("billable", "0");

//                allocate_inputs[0].classList.remove('billable-class');
//
//                event.target.classList.remove('billable-class');
//
//                event.target.parentElement.classList.remove('billable-class');
            }
        }

    },

    _show_detail: function (event) {
        var self = this;

        var project_id = parseInt(event.target.getAttribute('project_id'));
        var employee_id = parseInt(event.target.getAttribute('employee_id'));
        var date = event.target.getAttribute('date');
        var lock = event.target.getAttribute('lock');

        var form_view_ref = 'bnk_project.allocate_resource_form';
        if (lock !== "true"){
            form_view_ref = 'bnk_project.allocate_resource_form';
        }

        var tree_view_ref = 'bnk_project.allocate_resource_not_create_tree';
        if (lock !== "true" && project_id){
            tree_view_ref = 'bnk_project.allocate_resource_tree';
        }

//        this.do_action({
//                name: 'Allocate resource ' + date,
//                type: 'ir.actions.act_window',
//                res_model: 'allocate.resource',
//                domain: [['project_id', '=', project_id], ['employee_id', '=', employee_id], ['date', '=', date]],
//                context: {
//                    default_project_id: project_id,
//                    default_employee_id: employee_id,
//                    default_date: date,
//                    form_view_ref: form_view_ref
//                },
//                views: [[false, 'form']],
//                target: 'new'
//            });
        var domain = [['employee_id', '=', employee_id], ['date', '=', date]];

        if (project_id){
            domain.push(['project_id', '=', project_id])
        }

        this.do_action({
                name: 'Allocate resource ' + date,
                type: 'ir.actions.act_window',
                res_model: 'allocate.resource',
                domain: domain,
                context: {
                    default_project_id: project_id,
                    default_employee_id: employee_id,
                    default_date: date,
                    tree_view_ref: tree_view_ref
                },
                views: [[false, 'list']],
                target: 'new'
            });

    },

    _save_action: function (event) {
        var self = this;

        var change_elements = document.getElementsByClassName("edited");
        var edit_info = [];

        while (change_elements.length > 0) {
            var element = change_elements[0];
            element.classList.remove('edited');
            var project_id = element.getAttribute('project_id');
            var employee_id = element.getAttribute('employee_id');
            var date = element.getAttribute('date');
            var ot = element.getAttribute('ot');
            var line_ids = element.getAttribute('line_ids');
            var percent = element.value;
            var billable = element.getAttribute('billable');

            edit_info.push({
                project_id: project_id,
                employee_id: employee_id,
                date: date,
                ot: ot,
                line_ids: line_ids,
                percent: percent,
                billable: billable,

            })
        };

        var _id = self.recordData.id;

        this._rpc({
                model: 'report.allocate.resource',
                method: 'save',
                args: [_id, edit_info],
            }).then(function (save_result) {
                self.trigger_up('reload');

            });

    },

});

field_registry.add('allocate_resource', AllocateResourceWidget);

return {
    AllocateResourceWidget: AllocateResourceWidget
};

});
