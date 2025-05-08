odoo.define('pricelist_ext.DB', function (require) {
"use strict";
var core = require('web.core');
/* The PosDB holds reference to data that is either
 * - static: does not change between pos reloads
 * - persistent : must stay between reloads ( orders )
 */
var PosDB = require('point_of_sale.DB');

PosDB.include({
	init: function(options){
		this._super(options);
		this.barcode_by_id=  {};
		this.id_by_barcode = {};
		//this.uom_by_barcode = {};
	},
	
	_product_search_string: function(product){
		var str = this._super(product);
        var barcode_str = undefined;
        for(var j = 0, lenn = product.barcode_line.length; j < lenn; j++){
        	var barcode = this.barcode_by_id[product.barcode_line[j]]
			////console.log('barcode=',barcode);
        	if (barcode_str)
        		barcode_str += '|' + barcode.barcode;
        	else
        		barcode_str = barcode.barcode;
        }
        //////console.log('barcode_str=',barcode_str);
		if (barcode_str)
        	str = str.replace('\n','')+ '|' + barcode_str + '\n';
		return str;
    },
	
	add_products: function(products){
		////console.log('db add_products=',products);
		this._super(products);
		for(var i = 0, len = products.length; i < len; i++){
            var product = products[i];
            for(var j = 0, lenn = product.barcode_line.length; j < lenn; j++){
            	var barcode = this.barcode_by_id[product.barcode_line[j]]
            	this.product_by_barcode[barcode.barcode] = product;
            	//console.log("Barcode Added=",product.name,barcode.barcode);
            }
            
		}
		////console.log('add_products finished');
		
    },
    get_uom_by_barcode: function(barcode_str){
    	var barcode = this.id_by_barcode[barcode_str];
        if(barcode){
            return barcode.uom_id;
        } else {
            return undefined;
        }
    },
    get_id_by_barcode: function(barcode_str){
    	var barcode = this.id_by_barcode[barcode_str];
        if(barcode){
            return barcode.id;
        } else {
            return undefined;
        }
    },
});

});