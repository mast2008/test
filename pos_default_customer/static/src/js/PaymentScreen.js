odoo.define('pos_default_customer.PaymentScreen', function(require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;


    const DefaultCustomerPaymentScreen = PaymentScreen => class extends PaymentScreen {
        //@Override
        constructor() {
            super(...arguments);
            //lkp
            if (!this.env.pos.config.restrict_auto_inv_creation && this.env.pos.config.module_account){
                this.toggleIsToInvoice();
            }
        }
        async validateOrder(isForceValidate) {
            //console.log("DefaultCustomerPaymentScreen");
            if (this.env.pos.get_order()){
                var order = this.env.pos.get_order()
                var customer = order.get_client()
                //if (!customer && this.env.pos.config.pos_default_customer){
                //    order.set_default_pos_customer(this.env.pos.config.pos_default_customer[0]);
                //}
                if(!customer) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Customer Required'),
                        body  : this.env._t("Must select a customer."),
                        //body: _.str.sprintf(this.env._t('Customer is required for Order: %s .'), order.name),
                    });
                    return;
                }
            }


            await super.validateOrder(...arguments);
        }




    };

    Registries.Component.extend(PaymentScreen, DefaultCustomerPaymentScreen);

    return DefaultCustomerPaymentScreen;
});




