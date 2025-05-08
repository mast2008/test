odoo.define('pos_default_customer.models', function (require) {
    "use strict";
	var models = require('point_of_sale.models');
	var utils = require('web.utils');
    var round_pr = utils.round_precision;
    //var _super_posmodel = models.PosModel.prototype;


//fkp
var _super_order = models.Order.prototype;
models.Order = models.Order.extend({

    set_to_invoice: function(to_invoice) {

	 	     var result = _super_order.set_to_invoice.apply(this,arguments);
	 	     //console.log("posssssssss",this);
	 	     //lkp
	 	     if (!this.pos.config.restrict_auto_inv_creation && this.pos.config.module_account){
	 	        this.pos.get_order().to_invoice = true;
	 	     }
             //return result;
	 	},
});

    // lkp
    var posModelSuper = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        push_and_invoice_order: function (order) {
            //console.log("push_and_invoice_order00000000000");
            var self = this;
            return new Promise((resolve, reject) => {
                if (!order.get_client()) {
                    reject({ code: 400, message: 'Missing Customer', data: {} });
                } else {
                    var order_id = self.db.add_order(order.export_as_JSON());
                    self.flush_mutex.exec(async () => {
                        try {
                            const server_ids = await self._flush_orders([self.db.get_order(order_id)], {
                                timeout: 30000,
                                to_invoice: true,
                            });
                            if (server_ids.length) {
                                const [orderWithInvoice] = await self.rpc({
                                    method: 'read',
                                    model: 'pos.order',
                                    args: [server_ids, ['account_move']],
                                    kwargs: { load: false },
                                });
                                // lkp
                                if (!this.env.pos.config.restrict_inv_download){
                                    await self
                                        .do_action('account.account_invoices', {
                                            additional_context: {
                                                active_ids: [orderWithInvoice.account_move],
                                            },
                                        })
                                        .catch(() => {
                                            reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
                                        });
                                }
                            } else {
                                reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
                            }
                            resolve(server_ids);
                        } catch (error) {
                            reject(error);
                        }
                    });
                }
            });
        },


    });


});


