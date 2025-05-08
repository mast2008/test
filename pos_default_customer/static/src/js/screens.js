odoo.define('pos_default_customer.screens', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    /*
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var _t = core._t;
    var models = require('pos_orders_history.models');
    */
    var core = require('web.core');
    var _t = core._t;

    //PaymentScreenWidget
    screens.PaymentScreenWidget.include({
    	show: function(){

    		this._super();
    		this.click_invoice();
    	},
    })






    //

    //return screens;
});
