odoo.define('general.delivery.report.widget', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;


var GeneralDeliveryReportWidget = AbstractField.extend({
    events: _.extend({
        'click .open-button': '_open_parent_tr',
        'click .close-button': '_close_parent_tr',
        'click .open-employee-td': '_open_popup_employee',
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
        var groupby = 'project_id';
        var groupby_label = ['Project', 'Employee'];

        this._rpc({
                model: 'report.delivery.allocate.resource',
                method: 'get_general_delivery_report_data',
                args: [_id],
            }).then(function (grid_dict) {
                if (Object.keys(grid_dict).length === 0) {
                return;
                }
               el.html(QWeb.render('GeneralDeliverReportTemplate', grid_dict));
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

    _open_popup_employee: function (event) {
        if (event.target.classList.contains('element-popup')){
            event.target.parentElement.setAttribute('open', '0');
            event.target.parentElement.removeChild(event.target);
            return;
        }

        if (event.target.classList.contains('ul-element-popup')){
            var div = event.target.parentElement;
            div.parentElement.setAttribute('open', '0');
            div.parentElement.removeChild(div);
            return;
        }

        if (event.target.classList.contains('li-element-popup')){
            var ul = event.target.parentElement;
            var div = ul.parentElement;
            div.parentElement.setAttribute('open', '0');
            div.parentElement.removeChild(div);
            return;
        }

        if (event.target.classList.contains('span-element-popup')){
            var li = event.target.parentElement;
            var ul = li.parentElement;
            var div = ul.parentElement;
            div.parentElement.setAttribute('open', '0');
            div.parentElement.removeChild(div);
            return;
        }

        if (!event.target.classList.contains('open-employee-td')){
            return;
        }

        var self = this;
        var open = event.target.getAttribute('open');

        if (open == '0'){
            event.target.setAttribute('open', '1');
            var employee = event.target.getAttribute('employee');
            var employee_list = JSON.parse(employee);
            var el = this.$el;

            var div = document.createElement("div");
            div.setAttribute('class', 'element-popup');
            div.style.left = event.pageX;
            div.style.top = event.pageY;

            var ul = document.createElement("ul");
            ul.setAttribute('class', 'ul-element-popup');

            employee_list.forEach(function(e){
                var li = document.createElement("li");
                li.setAttribute('class', 'li-element-popup');

                var span = document.createElement("span");
                span.setAttribute('class', 'span-element-popup');

                var text = document.createTextNode(e[1]);
                span.appendChild(text)
                li.appendChild(span)

                ul.appendChild(li);
            })

            div.appendChild(ul);
            event.target.appendChild(div);
        }
        else {
            event.target.setAttribute('open', '0');
            var popup = event.target.children[0];
            event.target.removeChild(popup);
        }
    },

});

field_registry.add('general_delivery_report', GeneralDeliveryReportWidget);

return {
    GeneralDeliveryReportWidget: GeneralDeliveryReportWidget
};

});
