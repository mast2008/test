odoo.define('pricelist_ext.ProductScreen', function(require) {
    "use strict";

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    //console.log("loading  - pricelist_ext.ProductScreen")
    const PriceListExtProductScreen = ProductScreen => class extends ProductScreen {
        //@Override
        async _barcodeProductAction(code) {
            try {
                //console.log('_barcodeProductAction ext=',code)
                var code_type = code.type;
                if (code_type === 'product')
                {
                    var curr_order = this.env.pos.get_order();
                    var no_lines = curr_order.get_orderlines().length;
                    //console.log('no_lines 1=',no_lines)
                    //is_barcode_scanned for skip merge used in can_be_merged_with function.
                    curr_order.is_barcode_scanned = true;
                    await super._barcodeProductAction(...arguments);
                    curr_order.is_barcode_scanned = false;
                    //check whether new line is added or not  - no_lines < lines.length
                    //console.log('no_lines 2=',no_lines)
                    //console.log('no_lines current=',curr_order.get_orderlines().length)
                    if (no_lines < curr_order.get_orderlines().length)
                    {
                        //console.log("New product Added with barcode=",code)
                        this.env.pos.set_line_with_barcode(code.base_code);
                    }
                }
                else
                    await super._barcodeProductAction(...arguments);
            } catch(error) {
                throw error;
            }
        }
    }
    Registries.Component.extend(ProductScreen, PriceListExtProductScreen);
    return ProductScreen;
});
