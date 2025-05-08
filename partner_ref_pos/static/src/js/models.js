odoo.define('partner_ref_pos.models', function (require) {
"use strict";
var rpc = require('web.rpc');
var models = require('point_of_sale.models');
var _super_posproduct = models.Product.prototype;
var _super_posmodel = models.PosModel.prototype;


models.PosModel = models.PosModel.extend({
    initialize: function (session, attributes) {
        var res_partner_model = _.find(this.models, function(model){
            return model.model === 'res.partner';
        });
        res_partner_model.fields.push('ref');
        return _super_posmodel.initialize.call(this, session, attributes);
    },
});

var _super_posorder = models.Order.prototype;
var _super_paymentline= models.Paymentline.prototype;
models.Order = models.Order.extend({

    
});

//end
});