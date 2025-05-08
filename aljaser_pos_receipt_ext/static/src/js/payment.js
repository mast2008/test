odoo.define('aljaser_pos_receipt_ext.PaymentScreen', function (require) {
    'use strict';
    var rpc = require('web.rpc')
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { onMounted } = owl;
    var models = require('point_of_sale.models');

    var _super_order = models.Order.prototype;

    const PosPaymentReceiptExtend = PaymentScreen => class extends PaymentScreen {
        setup() {
        super.setup();


        }
//         async validateOrder(isForceValidate) {
//            var receipt_order =  super.validateOrder(...arguments);
//            console.log("receipt_order",receipt_order);
//            var receipt_number = this.env.pos.attributes.selectedOrder.name
//            var orders = this.env.pos.attributes.selectedOrder
//            var self= this;
//          await rpc.query({
//                model: 'pos.order',
//                method: 'get_invoice',
//                args: [receipt_number]
//                }).then(function(result){
//                self.env.pos.invoice  = result.invoice_name
//                const address = `${result.base_url}/my/invoices/${result.invoice_id}?`
//
//                });
//                console.log("receipt_order",receipt_order,self.env.pos.invoice);
//                console.log("super.validateOrder(...arguments)", receipt_order);
//                return   receipt_order;
//         }

//         async _finalizeValidation() {
//            var receipt_order =  super._finalizeValidation(...arguments);
//            console.log("receipt_order",receipt_order);
//            var receipt_number = this.env.pos.attributes.selectedOrder.name
//            console.log("this.currentOrder",this.currentOrder.name,receipt_number);
//            if (this.currentOrder.is_to_invoice()){
//            var self=this;
//            rpc.query({
//                model: 'pos.order',
//                method: 'get_invoice',
//                args: [this.currentOrder.name]
//                }).then(function(result){
//                    //var order = self.pos.get_order();
//                    //var order = self.pos.get_order();
//                        self.currentOrder.invoice_number = result.invoice_name;
//                        self.showScreen(self.nextScreen);
//                });
//            }
//            //else
////            {
////            this.showScreen(this.nextScreen);
////            }
//            return   receipt_order;
//         }


        async _finalizeValidation() {
            if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                this.env.pos.proxy.printer.open_cashbox();
            }

            this.currentOrder.initialize_validation_date();
            this.currentOrder.finalized = true;

            let syncedOrderBackendIds = [];

            try {
                if (this.currentOrder.is_to_invoice()) {
                    syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                        this.currentOrder
                    );
                } else {
                    syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                }
            } catch (error) {
                if (error.code == 700 || error.code == 701)
                    this.error = true;

                if ('code' in error) {
                    // We started putting `code` in the rejected object for invoicing error.
                    // We can continue with that convention such that when the error has `code`,
                    // then it is an error when invoicing. Besides, _handlePushOrderError was
                    // introduce to handle invoicing error logic.
                    await this._handlePushOrderError(error);
                } else {
                    // We don't block for connection error. But we rethrow for any other errors.
                    if (isConnectionError(error)) {
                        this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Connection Error'),
                            body: this.env._t('Order is not synced. Check your internet connection'),
                        });
                    } else {
                        throw error;
                    }
                }
            }
            if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                const result = await this._postPushOrderResolve(
                    this.currentOrder,
                    syncedOrderBackendIds
                );

                if (!result) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Error: no internet connection.'),
                        body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
                    });
                }
            }
            if (this.currentOrder.is_to_invoice()){
            console.log("this.currentOrder",this.currentOrder.account_move);
            var self=this;
            rpc.query({
                model: 'pos.order',
                method: 'get_invoice',
                args: [this.currentOrder.name]
                }).then(function(result){
                    //var order = self.pos.get_order();
                    //var order = self.pos.get_order();
                        self.currentOrder.invoice_number = result.invoice_name;
                        self.showScreen(self.nextScreen);
                });
            }
            else
            {
            this.showScreen(this.nextScreen);
            }






            // If we succeeded in syncing the current order, and
            // there are still other orders that are left unsynced,
            // we ask the user if he is willing to wait and sync them.
            if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Remaining unsynced orders'),
                    body: this.env._t(
                        'There are unsynced orders. Do you want to sync these orders?'
                    ),
                });
                if (confirmed) {
                    // NOTE: Not yet sure if this should be awaited or not.
                    // If awaited, some operations like changing screen
                    // might not work.
                    this.env.pos.push_orders();
                }
            }
        }




         }


       Registries.Component.extend(PaymentScreen, PosPaymentReceiptExtend);

    return PaymentScreen;
       });

