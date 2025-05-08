odoo.define('stock_no_negative_pos.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const StockNoNegativePosProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _onClickPay() {
                var validate_order_ext = this.env.pos.validate_order_stock(this.currentOrder);
                if (validate_order_ext)
                    await super._onClickPay(...arguments)
            }
        };

    Registries.Component.extend(ProductScreen, StockNoNegativePosProductScreen);

    return ProductScreen;
});
