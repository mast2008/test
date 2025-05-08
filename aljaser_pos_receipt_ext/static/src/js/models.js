odoo.define('point_of_sale_receipt_ext.models', function (require) {
    "use strict";
	var models = require('point_of_sale.models');
    //var screens = require('point_of_sale.screens');
    //var core = require('web.core');
    //var QWeb = core.qweb;
    var _super_orderline = models.Orderline.prototype;
	var _super_order = models.Order.prototype;
	//var utils = require('web.utils');
    //var round_pr = utils.round_precision;
    //var _super_posmodel = models.PosModel.prototype;
    //var moduls = models.PosModel.prototype.models;
	//importing fields
	models.load_fields("res.company", ['logo','street']);
	models.load_fields("res.partner", ['contact_address']);
	models.load_fields("account.tax", ['description']);
	var rpc = require('web.rpc')
	var utils = require('web.utils');
	var round_pr = utils.round_precision;

	//fkp

	//Extend POS Orderline
	//Extend POS Orderline
	models.Orderline = models.Orderline.extend({
		export_for_printing: function() {
			var line = _super_orderline.export_for_printing.apply(this,arguments);
			line.taxDetails = this.get_all_prices().taxDetails;
			line.product = this.get_product();

			line.disc_amt=round_pr ((this.get_unit_price() * (this.get_discount()/100) * this.get_quantity()), this.pos.currency.rounding);
			var val=round_pr(this.get_all_prices().priceSumTaxVoid, this.pos.currency.rounding);
			console.log("val",val,line.disc_amt);
			var taxes_ids = _.filter(this.get_product().taxes_id);
			line.tax_descrp_list=this.get_tax_descriptions().join(',');
			return line;
		},
		get_all_prices: function(){
			//
			var res = _super_orderline.get_all_prices.apply(this,arguments);
			var self = this;
			var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
			var product_taxes = [];
			var product =  this.get_product();
			var taxes =  this.pos.taxes;
			var taxes_ids = _.filter(product.taxes_id, t => t in this.pos.taxes_by_id);
			_(taxes_ids).each(function(el){
				var tax = _.detect(taxes, function(t){
					return t.id === el;
				});
				product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
			});
			product_taxes = _.uniq(product_taxes, function(tax) { return tax.id; });
			//extra goes down
			var basedetail = {};
			var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
			_(all_taxes.taxes).each(function(tax) {
				//console.log('all_taxes - each=',tax);
				basedetail[tax.id] = tax.base;


			});
			res['baseDetails'] = basedetail;
			//console.log('res[\'baseDetails\']==',res['baseDetails'])
			return res;
		},

		get_tax_descriptions:function(){
		    var tax_descrp_list=[];
		    var taxes_ids = _.filter(this.get_product().taxes_id);
		    var self=this;
		    taxes_ids.forEach(function(el){
                tax_descrp_list.push(
						 self.pos.taxes_by_id[el].description,
				);

			});
			return tax_descrp_list;
		},



	});

	models.Order = models.Order.extend({
		//Create a function for show tax name,amount in POS receipt




		get_tax_details: function(){
			var bases = {};
			var details = {};
			var fulldetails = [];

			this.orderlines.each(function(line){
				var ldetails = line.get_tax_details();
				for(var id in ldetails){
					if(ldetails.hasOwnProperty(id)){
						details[id] = (details[id] || 0) + ldetails[id];
					}
				}
				//extra

				var lbases = line.get_all_prices().baseDetails;
				for(var id in lbases){
					if(ldetails.hasOwnProperty(id)){
						bases[id] = (bases[id] || 0) + lbases[id];
					}
				}
				//
			});

			for(var id in details){
				if(details.hasOwnProperty(id)){
					fulldetails.push({amount: details[id], tax: this.pos.taxes_by_id[id], name: this.pos.taxes_by_id[id].name,
						 description: this.pos.taxes_by_id[id].description,
						percent: this.pos.taxes_by_id[id].amount, base_amount: bases[id], price_include: this.pos.taxes_by_id[id].price_include}
						);
				}
			}
			//console.log("fulldetails",fulldetails);
			return fulldetails;
		},







	});
});
    