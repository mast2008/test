odoo.define('pricelist_ext.models', function (require) {
"use strict";

var models = require('point_of_sale.models');
var core = require('web.core');
//var utils = require('web.utils');
var _super_posmodel = models.PosModel.prototype;
var _super_posorder= models.Order.prototype;
var _t = core._t;
//var round_di = utils.round_decimals;

models.load_fields('product.product','barcode_line');

models.load_models([{
    model: 'product.barcode.line',
    label: 'Product Barcodes',
    fields: ['barcode','uom_id','price'],
    loaded: function(self,lines){
        //self.product_barcodes = lines;
        _.each(lines, function(line){
            self.barcode_by_id[line.id] = line;
            self.db.barcode_by_id[line.id] = line;
            self.db.id_by_barcode[line.barcode] = line;
            //self.db.uom_by_barcode[line.name] = line.uom_id;
        });
    },
}],{'before': 'product.product'});

models.PosModel = models.PosModel.extend({
    initialize: function (attributes) {
        //this.product_barcodes = [];
        this.barcode_by_id= {};
        // Product Model
        /*
        var product_product_model = _.find(this.models, function(model){
            return model.model === 'product.product';
        });
        product_product_model.loaded = function(self, products){
            var using_company_currency = self.config.currency_id[0] === self.company.currency_id[0];
            var conversion_rate = self.currency.rate / self.company_currency.rate;
            self.db.add_products(_.map(products, function (product) {
                if (!using_company_currency) {
                    product.lst_price = round_pr(product.lst_price * conversion_rate, self.currency.rounding);
                }
                product.categ = _.findWhere(self.product_categories, {'id': product.categ_id[0]});
                product.pos = self;
                return new models.Product({uom:self.units_by_id[product.uom_id[0]]}, product);
            }));   
        }
         */
        return _super_posmodel.initialize.call(this, attributes);
    },
    set_line_with_barcode: function(barcode_str)
    {
    	var barcode_uom = this.db.get_uom_by_barcode(barcode_str);
    	//console.log('set_line_with_barcode=',barcode_uom)
		if(barcode_uom)
		{
    		var selectedOrder = this.get_order();
    		var order_line_selected = selectedOrder.get_selected_orderline();
    		order_line_selected.set_uom(barcode_uom[0]);
    		var barcode_id = this.db.get_id_by_barcode(barcode_str);
    		if(barcode_id)
    			order_line_selected.set_barcode_id(barcode_id);
    		order_line_selected.set_unit_price(order_line_selected.price);
		}
    },
    /* deprecated since 15
    scan_product: function(parsed_code){
        var curr_order = this.get_order();
        //is_barcode_scanned for skip merge used in can_be_merged_with function.
        curr_order.is_barcode_scanned = true;
    	var res = _super_posmodel.scan_product.call(this,parsed_code);
        curr_order.is_barcode_scanned = false;
        ////console.log('scan_product=',res,parsed_code.base_code)
    	if (res === true)
    		this.set_line_with_barcode(parsed_code.base_code);
    	return res
    },
    */
});

var _super_posproduct = models.Product.prototype;
models.Product = models.Product.extend({
    initialize: function(attr, options){
        //////console.log('init product = ',this)
        //this.uom   = attr.uom;
        return _super_posproduct.initialize.call(this, attr, options);
    },
    // Port of get_product_price on product.pricelist.
    //
    // Anything related to UOM can be ignored, the POS will always use
    // the default UOM set on the product and the user cannot change
    // it.
    //
    // Pricelist items do not have to be sorted. All
    // product.pricelist.item records are loaded with a search_read
    // and were automatically sorted based on their _order by the
    // ORM. After that they are added in this order to the pricelists.
    get_price: function(pricelist, quantity, price_extra){
        //////console.log('get_price extended=',this);
        var self = this;
        var date = moment();

        //extra fkp
        var uom_id = this.get_unit();
        if (uom_id)
            uom_id = uom_id.id;
        //end extra
        // In case of nested pricelists, it is necessary that all pricelists are made available in
        // the POS. Display a basic alert to the user in this case.
        if (pricelist === undefined) {
            alert(_t(
                'An error occurred when loading product prices. ' +
                'Make sure all pricelists are available in the POS.'
            ));
        }

        var category_ids = [];
        var category = this.categ;
        while (category) {
            category_ids.push(category.id);
            category = category.parent;
        }

        var pricelist_items = _.filter(pricelist.items, function (item) {
            return (! item.product_tmpl_id || item.product_tmpl_id[0] === self.product_tmpl_id) &&
                   (! item.product_id || item.product_id[0] === self.id) &&
                   (! item.categ_id || _.contains(category_ids, item.categ_id[0])) &&
                   (! item.date_start || moment.utc(item.date_start).isSameOrBefore(date)) &&
                   (! item.date_end || moment.utc(item.date_end).isSameOrAfter(date));
        });
        ////console.log('pricelist_items main=',pricelist_items)

        var price = self.lst_price;
        if (price_extra){
            price += price_extra;
        }
        _.find(pricelist_items, function (rule) {
            if (rule.min_quantity && quantity < rule.min_quantity) {
                return false;
            }
            //extra fkp
            // if rule by product and uom not match product uom - return false
            if ((rule.applied_on === '0_product_variant' || rule.applied_on === '1_product') && rule.uom_id && rule.uom_id[0] !== uom_id) {
                return false;
            }
            //end extra
            if (rule.base === 'pricelist') {
                price = self.get_price(rule.base_pricelist, quantity);
            } else if (rule.base === 'standard_price') {
                price = self.standard_price;
            }

            if (rule.compute_price === 'fixed') {
                price = rule.fixed_price;
                return true;
            } else if (rule.compute_price === 'percentage') {
                price = price - (price * (rule.percent_price / 100));
                return true;
            } else {
                var price_limit = price;
                price = price - (price * (rule.price_discount / 100));
                if (rule.price_round) {
                    price = round_pr(price, rule.price_round);
                }
                if (rule.price_surcharge) {
                    price += rule.price_surcharge;
                }
                if (rule.price_min_margin) {
                    price = Math.max(price, price_limit + rule.price_min_margin);
                }
                if (rule.price_max_margin) {
                    price = Math.min(price, price_limit + rule.price_max_margin);
                }
                return true;
            }

            return false;
        });

        // This return value has to be rounded with round_di before
        // being used further. Note that this cannot happen here,
        // because it would cause inconsistencies with the backend for
        // pricelist that have base == 'pricelist'.

        return price;
    },
});

models.Order = models.Order.extend({
	 add_product: function(product, options){
	    options = options || {};
	    _super_posorder.add_product.call(this, product, options);
	  },
	 set_orderline_options: function (orderline, options) {
	    //console.log('set_orderline_options ext=',options)
	    // in case of refund - the set_price is called before setting price_manually_set for line in set_orderline_options its making problem in set_unit_price (price not keeping same as line)
        if(options.extras !== undefined && options.extras.price_manually_set)
            orderline.price_manually_set = options.extras.price_manually_set;
        //coming from ticketscreen.js
        //setting uom_id from refund_line_id
        if (options.product_uom_id)
            orderline.set_uom(options.product_uom_id)
        //setting barcode_id
        if (options.barcode_id)
            orderline.set_barcode_id(options.barcode_id)
        //setting barcode
        if (options.barcode)
            orderline.set_barcode(options.barcode)

        _super_posorder.set_orderline_options.apply(this, [orderline, options]);
      },
});

var _super_posorderline = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({
    initialize: function(attr,options){
        _super_posorderline.initialize.call(this, attr, options);
        //console.log('initialize - orderline pricelist_ext==',options)
        //hided because of uom rare issue - refer ticket # 1202
        if(options.product && 1===2)
            this.set_uom(options.product.uom_id[0]);
        //refund case - passing from back office _export_for_ui (only to set in refund window left panel)
        if (options.json && options.json.product_uom_id)
            this.set_uom(options.json.product_uom_id)
        //
        if (options.json && options.json.barcode_id)
            this.set_barcode_id(options.json.barcode_id)
        if (options.json && options.json.barcode)
            this.set_barcode(options.json.barcode)
    },
    init_from_JSON: function(json)
    {
      //console.log('init_from_JSON - orderline pricelist_ext==',json)
      _super_posorderline.init_from_JSON.call(this, json);
      if (json.product_uom)
        this.set_uom(json.product_uom);
      if(json.barcode_id)
    	  this.set_barcode_id(json.barcode_id);
      if(json.barcode)
    	  this.set_barcode(json.barcode);
    },
    clone: function()
    {
        var orderline = _super_posorderline.clone.call(this); 
        order_line.uomStr = this.uomStr;
        order_line.product_uom = this.product_uom; 
        order_line.barcode_id = this.barcode_id;
        order_line.barcode = this.barcode;
        return orderline;
    },
    // return the unit of measure of the product
    get_unit: function(){
        ////console.log("get_unit orderline=",this)
        //full replace
        //////////////console.log('get_unit order line=',this.pos.units_by_id[this.product_uom]);
        if (this.get_uom())
            return this.pos.units_by_id[this.get_uom()];
        return _super_posorderline.get_unit.call(this);
        //return this.product.get_unit();
    },
    can_be_merged_with: function(orderline){
        //////////console.log('is_barcode_scanned=',orderline.order.is_barcode_scanned);
        /*  this one we tried maximum to merge same barcode
        //to do - call set_line_with_barcode from scan_product if ordelines length zero
        but in merge:func (calling from add_product:func) they calling set_qty and set_qty again recompute set_unit_price (ie, price unit calc goes through pricelist)
        !imp: may be possible - later inherited set_unit_price for recompute barcode price if the line hasn't set manual price
        if (orderline.order.barcode_scanned)
        {
            this.pos.set_line_with_barcode(orderline.order.barcode_scanned,orderline);
            //////////console.log('after set_line_with_barcode=',orderline.price);
            orderline.order.barcode_scanned = false;
        }
        */
        var res = _super_posorderline.can_be_merged_with.call(this, orderline);
        /*
        //checking whether the merge false coming because of unit price. (unit price in org func they calculated) . but we have barcode
        if (orderline.barcode_id)
        {
            var price = parseFloat(round_di(this.price || 0, this.pos.dp['Product Price']).toFixed(this.pos.dp['Product Price']));
            var order_line_price_barcode = parseFloat(round_di(orderline.price || 0, this.pos.dp['Product Price']).toFixed(this.pos.dp['Product Price']));
            var order_line_price = orderline.get_product().get_price(orderline.order.pricelist, this.get_quantity());
            if (res === false && !utils.float_is_zero(price - order_line_price - orderline.get_price_extra(),
                this.pos.currency.decimals) && utils.float_is_zero(price - order_line_price_barcode - orderline.get_price_extra(),
                this.pos.currency.decimals))
                res = true;
        }
        */
        //checking uom equal to both
        if (res === true && (orderline.get_unit().id !== this.get_unit().id || orderline.order.is_barcode_scanned === true || orderline.get_product().barcode_line.length > 0))
            res = false;
        return res;
	 },
    set_uom: function(uom_id)
    {
        this.order.assert_editable();
        this.uomStr=this.pos.units_by_id[uom_id].name;
        this.product_uom = uom_id;
        this.trigger('change',this);
    },
    get_uom: function(){
        return this.product_uom;
    },
    get_uomStr: function()
    {
        return this.uomStr;
    },

    //refund case - eg: if they deleted barcode_id of old line - we have to read barcode string
    set_barcode: function(barcode_str)
    {
        this.barcode = barcode_str;
    },
    get_barcode: function(barcode_str)
    {
        return this.barcode;
    },
    set_barcode_id: function(barcode_id)
    {
        this.barcode_id = barcode_id;
    },
    get_barcode_id: function(){
    	if(this.barcode_id)
	    	if(this.pos.barcode_by_id[this.barcode_id])
	    		return this.barcode_id;
    	return undefined;
    },
    /*
    inherited get_unit()
    get_quantity_str_with_unit: function()
    {
        //var qty_str_with_unit = _super_posorderline.get_quantity_str_with_unit.call(this);
        var unit = this.pos.units_by_id[this.get_uom()];
        if(unit && !unit.is_pos_groupable){
            return this.quantityStr + ' ' + unit.name;
        }else{
            return this.quantityStr;
        }
    },

     */
    export_as_JSON: function() 
    {
        var json = _super_posorderline.export_as_JSON.call(this);
        json.product_uom = this.get_uom();
        var barcode_id = this.get_barcode_id();
        if (this.get_barcode())
            json.barcode = this.get_barcode();
        if (barcode_id)
        {
            if (!json.barcode)
        	    json.barcode = this.pos.barcode_by_id[barcode_id].barcode;
        	json.barcode_id = barcode_id;
        }
        if (!json.barcode)
            json.barcode = this.product.barcode;
        //console.debug('Json Barcode=',json.barcode);
        return json;
    },
    export_for_printing: function()
    {
        var printing_data = _super_posorderline.export_for_printing.call(this);
        printing_data.unit_name = this.get_uomStr();
        return printing_data;
    },
    set_unit_price: function(price){
        //console.log('set_unit_price called=',this.barcode_id,this.product_uom,this.price_manually_set);
        _super_posorderline.set_unit_price.call(this,price);
        // if (this.product_uom && this.get_barcode() && !this.price_manually_set)
        if (this.product_uom && !this.price_manually_set)
        {
            ////////////console.log('set_unit_price 1=',price);
            //this.order.assert_editable();
            var sec_price = this.get_price(this.order.pricelist, this.get_quantity(),this.get_price_extra());
            ////console.log('set_unit_price ext=',sec_price,price)
            ////////////console.log('set_unit_price 2=',sec_price);
            if (sec_price && sec_price !== price){
                _super_posorderline.set_unit_price.call(this,sec_price);
                /*
                price = sec_price;
                //org code belows
	            var parsed_price = !isNaN(price) ?
                    price :
                    isNaN(parseFloat(price)) ? 0 : field_utils.parse.float('' + price)
                this.price = round_di(parsed_price || 0, this.pos.dp['Product Price']);
                ////////////console.log('Priceeeeee==',price);
                this.trigger('change',this);
                 */
            }
        }
    },
    //extra func
    //duplicate get_price Product backbone + some changes
    get_price: function(pricelist, quantity, price_extra){
        ////console.log('get_price copy=');
        var product = this.product;
        var self = this;
        var date = moment();

        //extra fkp
        var uom_id = this.get_unit();
        if (uom_id)
            uom_id = uom_id.id;
        //end extra
        // In case of nested pricelists, it is necessary that all pricelists are made available in
        // the POS. Display a basic alert to the user in this case.
        if (pricelist === undefined) {
            alert(_t(
                'An error occurred when loading product prices. ' +
                'Make sure all pricelists are available in the POS.'
            ));
        }

        var category_ids = [];
        var category = this.categ;
        while (category) {
            category_ids.push(category.id);
            category = category.parent;
        }

        var pricelist_items = _.filter(pricelist.items, function (item) {
            return (! item.product_tmpl_id || item.product_tmpl_id[0] === product.product_tmpl_id) &&
                   (! item.product_id || item.product_id[0] === product.id) &&
                   (! item.categ_id || _.contains(category_ids, item.categ_id[0])) &&
                   (! item.date_start || moment.utc(item.date_start).isSameOrBefore(date)) &&
                   (! item.date_end || moment.utc(item.date_end).isSameOrAfter(date));
        });
        ////console.log('pricelist_items copy=',pricelist_items)

        var price = product.lst_price;
        if (price_extra){
            price += price_extra;
        }
        var rule_found;
        rule_found = _.find(pricelist_items, function (rule) {
            if (rule.min_quantity && quantity < rule.min_quantity) {
                return false;
            }
            //extra fkp
            // if rule by product and uom not match product uom - return false
            if ((rule.applied_on === '0_product_variant' || rule.applied_on === '1_product') && rule.uom_id && rule.uom_id[0] !== uom_id) {
                return false;
            }
            //end extra
            if (rule.base === 'pricelist') {
                price = self.get_price(rule.base_pricelist, quantity);
            } else if (rule.base === 'standard_price') {
                price = product.standard_price;
            }

            if (rule.compute_price === 'fixed') {
                price = rule.fixed_price;
                return true;
            } else if (rule.compute_price === 'percentage') {
                price = price - (price * (rule.percent_price / 100));
                return true;
            } else {
                var price_limit = price;
                price = price - (price * (rule.price_discount / 100));
                if (rule.price_round) {
                    price = round_pr(price, rule.price_round);
                }
                if (rule.price_surcharge) {
                    price += rule.price_surcharge;
                }
                if (rule.price_min_margin) {
                    price = Math.max(price, price_limit + rule.price_min_margin);
                }
                if (rule.price_max_margin) {
                    price = Math.min(price, price_limit + rule.price_max_margin);
                }
                return true;
            }

            return false;
        });
        var barcode_id = this.get_barcode_id();
        if(rule_found == undefined)
    	{
        	// same price , no rules found - check barcode price available or not
        	if(barcode_id)
        	{
            	barcode_id = this.pos.barcode_by_id[barcode_id];
            	if(barcode_id && barcode_id.price != 0)
            		price = barcode_id.price;
        	}
    	}
        // This return value has to be rounded with round_di before
        // being used further. Note that this cannot happen here,
        // because it would cause inconsistencies with the backend for
        // pricelist that have base == 'pricelist'.
        return price;
    },
});
});
