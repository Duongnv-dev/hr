odoo.define('allocate.resource.line.chart.widget', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;


var AllocateResourceLineChartWidget = AbstractField.extend({
    events: _.extend({
//        'click .open-button': '_open_parent_tr',
//        'click .close-button': '_close_parent_tr',
    }, AbstractField.prototype.events),
    supportedFieldTypes: ['char'],

    isSet: function() {
        return true;
    },

    _get_data: function() {
        var _id = self.view.datarecord.id;
    },

    clear_chart: function(ElementId) {
        var e = document.getElementById(ElementId);
        var we = e.parentNode;
        we.removeChild(e);
        we.innerHTML = '<canvas id="' + ElementId + '"></canvas>';
    },

    drawMultiLineChart: function(data, ElementId) {
        var self = this;
        self.clear_chart(ElementId);

        new Chart(document.getElementById(ElementId), {
                  type: 'line',
                  data: data,
                  options: {
                    title: {
                      display: true,
                      text: ''
                    }
                  }
                });
    },

    _render: function() {
        var self = this;

        var _id = self.recordData.id;
        var el = this.$el;

        el.html(QWeb.render('AllocateResourceLineChartTemplate', {}));

        var ElementId = 'allocate-resource-line-chart';

        this._rpc({
                model: 'report.allocate.resource.line.chart',
                method: 'get_allocate_resource_line_chart_widget_data',
                args: [_id],
            }).then(function (datas) {
                if (Object.keys(datas).length === 0) {
                return;
                }
                self.drawMultiLineChart(datas, ElementId)

            });
    },

});

field_registry.add('allocate_resource_line_chart', AllocateResourceLineChartWidget);

return {
    AllocateResourceLineChartWidget: AllocateResourceLineChartWidget
};

});
