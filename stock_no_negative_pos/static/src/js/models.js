odoo.define('stock_no_negative_pos.models', function (require) {
    "use strict";

var models = require('point_of_sale.models');
var posmodel_super = models.PosModel.prototype;
var { Gui } = require('point_of_sale.Gui');
var core = require('web.core');
var _t = core._t;
var field_utils = require('web.field_utils');

models.load_fields("product.category", ['allow_negative_stock']);
models.load_fields("product.product", ['allow_negative_stock','type']);
/*
models.Product = models.Product.extend({
    format_float_value: function(val) {
        var value = parseFloat(val);
        value = field_utils.format.float(value, {digits: [69, 3]});
        return String(parseFloat(value));
    },
    rounded_qty: function() {
        return this.format_float_value(this.qty_available);
    },
});
*/
models.PosModel = models.PosModel.extend({
    has_to_check_stock: function (product)
    {
        //console.log("has_to_check_stock=",product)
        if (product.type === 'product' && !this.config.allow_negative_stock_location
        && !product.allow_negative_stock && !product.categ.allow_negative_stock)
            return true;
        return false;
    },
    push_single_order: async function (order, opts) {
        if (!this.config.allow_negative_stock_location)
            this.update_product_qty_from_order_lines(order);
        return await posmodel_super.push_single_order.apply(this, arguments);
    },
    push_and_invoice_order: async function (order) {
        if (!this.config.allow_negative_stock_location)
            this.update_product_qty_from_order_lines(order);
        return await posmodel_super.push_and_invoice_order.apply(this, arguments);
    },
    update_product_qty_from_order_lines: function(order) {
        var self = this;
        if (!this.config.allow_negative_stock_location)
        {
            order.orderlines.each(function(line) {
                var product = line.get_product();
                if (self.has_to_check_stock(product) && product.qty_available !== undefined)
                    self.db.get_product_by_id(product.id).qty_available = product.qty_available - line.get_quantity();
            });
        }
    },
    get_product_model: function() {
        return _.find(this.models, function(model) {
            return model.model === "product.product";
        });
    },
    add_product_qty: function(products) {
        //console.log("add_product_qty=",products)
        var self = this;
        _.each(products, function(p) {
            var product = self.db.get_product_by_id(p.id);
            if (product && self.has_to_check_stock(product) && p.qty_available !== undefined)
                _.extend(self.db.get_product_by_id(p.id), p);
        });
    },
    /*
    set_product_qty_available: function(product, qty) {
        product.qty_available = qty;
        this.refresh_qty_available(product);
    },
    */
    validate_order_stock: function(order)
    {
        var res = true;
        var self = this;
        if (!self.config.allow_negative_stock_location  && order) {
            order.get_orderlines().forEach(function (orderline) {
                var product = orderline.product;
                if (product && self.has_to_check_stock(product))
                {
                    var total_qty = order.get_product_total_qty(product);
                    if (!self.validate_product_stock(product, total_qty))
                    {
                        res = false;
                        return res;
                    }
                }
            });
        }
        return res;
    },
    validate_product_stock: function(product, qty=0)
    {
        if (qty && qty > 0 && product && this.has_to_check_stock(product) && product.qty_available !== undefined)
        {
            var self = this;
            product = self.db.get_product_by_id(product.id)
            if (product.qty_available < qty)
            {
                Gui.showPopup('ErrorPopup', {
                    title: _t('Not enough stock.'),
                    body: _.str.sprintf(
                        _t(
                        "Product '%s' hasn't enough stock !!\nPlanning Qty : %s \n Available Qty : %s\nDifference : %s\n"),
                        product.display_name,self.formatProductQty(parseFloat(qty)),self.formatProductQty(product.qty_available),
                        self.formatProductQty(parseFloat(qty)) - self.formatProductQty(product.qty_available)
                    ),
                });
                return false;
            }
        }
        return true;
    },
    load_available_qty: async function(product_ids)
    {
        var self = this;
        var product_product_model = self.get_product_model();
        if (self.config.allow_negative_stock_location === false && self.config.default_location_src_id)
        {
            if (product_ids)
            {
                var contt = _.extend(product_product_model.context, {
                        location: self.config.default_location_src_id[0],
                    });
                //console.log("contt11111111=",contt)
                var records = self.rpc({
                    model: 'product.product',
                    method: "search_read",
                    args: [],
                    fields: ["qty_available", "type"],
                    domain: [['id','in',product_ids]],//product_product_model.domain,
                    //context: _.extend(product_product_model.context, {
                    //    location: self.config.default_location_src_id[0],
                    //}),
                    context: {location: self.config.default_location_src_id[0]}
                });
                return records.then(function (products) {
                    self.add_product_qty(products);
                });
            }
        }
    },
    //hided
    /*
    after_load_server_data_hided: async function() {
        console.log("after_load_server_data ext")
        var self = this;
        return posmodel_super.after_load_server_data.apply(this, arguments).then(function () {
            console.log("may be after_load_server_data  - finished")
            if (self.config.allow_negative_stock_location === false
            && self.config.default_location_src_id)
                self.load_available_qty();
        });
    },
    */
    load_server_data: function () {
        //console.log("load_server_data ext")
        var self = this;
        //var product_product_model = self.get_product_model();
        self.db.pos = this;
        return posmodel_super.load_server_data.apply(this, arguments).then(function () {
            /*
            //console.log("pos config=",self.config)
            if (!self.config.limited_products_loading && self.config.allow_negative_stock_location === false
            && self.config.default_location_src_id)
            {
                var records = self.rpc({
                    model: 'product.product',
                    method: "search_read",
                    args: [],
                    fields: ["qty_available", "type"],
                    domain: product_product_model.domain,
                    context: _.extend(product_product_model.context, {
                        location: self.config.default_location_src_id[0],
                    }),
                });
                return records.then(function (products) {
                    self.add_product_qty(products);
                });
            }
            */

        });
    },
});

    var _order_super = models.Order.prototype;
    var _super_orderline = models.Orderline.prototype;

    models.Order = models.Order.extend({
        get_product_total_qty: function(product, qty=0)
        {
            for (var i = 0; i < this.orderlines.length; i++)
            {
                if (product.id === this.orderlines.at(i).product.id)
                {
                    qty += this.orderlines.at(i).quantity;
                }
            }
            return parseFloat(qty)
        },
        add_product: async function (product, options)
        {
            //console.log("add_product_ext=",options)
            if (product && this.pos.has_to_check_stock(product))
            {
                var product_qty = this.get_product_total_qty(product, options.quantity || 1)
                if (!this.pos.validate_product_stock(product,product_qty))
                    return false;
            }
            return _order_super.add_product.apply(this, arguments);
        },
    });
    //order line class
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function(json) {
            this.is_from_init_from_JSON = true;
            _super_orderline.init_from_JSON.apply(this,arguments);
        },
        set_quantity: function(quantity, keep_price) {
            //console.log("set quantity=",quantity,typeof(quantity) )
            if (quantity !== 'remove')
            {
                var product = this.get_product()
                var quant = typeof(quantity) === 'number' ? quantity : (field_utils.parse.float('' + quantity) || 0);
                if (quant && !this.is_from_init_from_JSON && product && this.pos.has_to_check_stock(product))
                {
                    var total_qty = this.order.get_product_total_qty(product,quant) - this.get_quantity();
                    //console.log("total_qty 121=",total_qty)
                    if (!this.pos.validate_product_stock(this.get_product(), total_qty))
                        return false
                }
            }
            this.is_from_init_from_JSON = false;
            return _super_orderline.set_quantity.apply(this,arguments);
        },
    });
});