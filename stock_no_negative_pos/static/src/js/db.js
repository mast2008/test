odoo.define('stock_no_negative_pos.DB', function (require) {
"use strict";
var core = require('web.core');
/* The PosDB holds reference to data that is either
 * - static: does not change between pos reloads
 * - persistent : must stay between reloads ( orders )
 */
var PosDB = require('point_of_sale.DB');

PosDB.include({
    add_products: async function(products){
        //console.log("add_products ext=",products)
        this._super(products);
        var pos = this.pos;
        if (pos && pos.config.allow_negative_stock_location === false
            && pos.config.default_location_src_id)
        {
            //copy from super
            if(!products instanceof Array)
            {
                products = [products];
            }
            var product_ids_to_update_avail_qty = [];
            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                if (pos.has_to_check_stock(product) && product.qty_available === undefined)
                    product_ids_to_update_avail_qty.push(product.id);
            }
            if (product_ids_to_update_avail_qty)
                await pos.load_available_qty(product_ids_to_update_avail_qty);
        }
    },
});

});