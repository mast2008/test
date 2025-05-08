odoo.define('pricelist_ext.screens', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    //not suing moreeeeeeeeeeeeeeeeeeeeee
    /*
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var _t = core._t;
    var models = require('pos_orders_history.models');
    */
    screens.ProductScreenWidget.include({
    	click_product: function(product) {
	    	this._super(product);
	    	if(!product.to_weight || !this.pos.config.iface_electronic_scale){
	    		var search_value = this.product_categories_widget.el.querySelector('.searchbox input').value;
	    		//console.log("Click_prodyct ext = search_value=",search_value);
	    		if (search_value && product.barcode_line.length > 0)
    			{
	    			this.pos.set_line_with_barcode(search_value);
    			}
	    			
	    	}
    	}
    });

    screens.ProductCategoriesWidget.include({
    	perform_search: function(category, query, buy_result){
    		this._super(category, query, buy_result);
        	//console.log('perform_search query ext = ',query);
            var products;
            if(query){
                products = this.pos.db.search_product_in_category(category.id,query);
                if(buy_result && products.length === 1){
                	this.pos.set_line_with_barcode(query);
                }
            }
        },
    });
  
   
    //
    
    //return screens;
});
