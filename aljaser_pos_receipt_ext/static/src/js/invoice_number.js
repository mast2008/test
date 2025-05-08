odoo.define('aljaser_pos_receipt_ext.invoice_number', function (require) {
"use strict";
    var rpc = require('web.rpc')

    var models = require('point_of_sale.models');
    models.load_fields('account.move', ['name']);
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
         export_for_printing: async function(){
            var receipt =  _super_order.export_for_printing.apply(this,arguments);
             await rpc.query({
                model: 'pos.order',
                method: 'get_invoice',
                args: [receipt.name]
                }).then(function(result){
                    receipt.invoice  = result.invoice_name
                });
                console.log("receipt",receipt,receipt.invoice);
                return receipt;
        },

           async validateOrder(isForceValidate) {
            const receipt_order = await super.validateOrder(...arguments);

            var receipt_number = this.env.pos.attributes.selectedOrder.name
            var orders = this.env.pos.attributes.selectedOrder
            var self= this;
         await rpc.query({
                model: 'pos.order',
                method: 'get_invoice',
                args: [receipt_number]
                }).then(function(result){
                self.env.pos.invoice  = result.invoice_name
                });
                console.log("receipt_order",self.env.pos.invoice);
                return receipt_order;
         }

    });

});


