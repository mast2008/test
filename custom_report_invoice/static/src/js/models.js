odoo.define('custom_report_invoice.models', function (require) {
"use strict";

var models = require('point_of_sale.models');
var _super_posorderline = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({

    export_for_printing: function()
    {
        //console.debug('Ext export_for_printing order line=',);
        var printing_data = _super_posorderline.export_for_printing.call(this);
        printing_data.taxes = this.get_taxes();
        //console.debug('Ext export_for_printing = ',printing_data);
        return printing_data;
    },

});

});
