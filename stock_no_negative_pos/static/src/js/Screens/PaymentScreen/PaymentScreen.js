odoo.define('stock_no_negative_pos.PaymentScreen', function (require) {
'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const StockNoNegativePaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen{
            async validateOrder(isForceValidate) {
                var validate_order_ext = this.env.pos.validate_order_stock(this.env.pos.get_order());
                if (validate_order_ext)
                    await super.validateOrder(...arguments);
            }
    };
    Registries.Component.extend(PaymentScreen, StockNoNegativePaymentScreen);
    return PaymentScreen;
});
