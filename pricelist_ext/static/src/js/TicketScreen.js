odoo.define('pricelist_ext.TicketScreen', function (require) {
'use strict';

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');

    const PricelistExtTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            _getToRefundDetail(orderline) {
                //console.log("_getToRefundDetail ex=",orderline)
                var res = super._getToRefundDetail(orderline);
                if (orderline.product_uom)
                    res.orderline.product_uom_id = orderline.product_uom;
                if (orderline.barcode_id)
                    res.orderline.barcode_id = orderline.barcode_id;
                if (orderline.barcode)
                    res.orderline.barcode = orderline.barcode;
                return res;
            }
            _prepareRefundOrderlineOptions(toRefundDetail) {
                const { qty, orderline } = toRefundDetail;
                var res = super._prepareRefundOrderlineOptions(toRefundDetail);
                if (orderline.product_uom_id)
                    res.product_uom_id = orderline.product_uom_id;
                if (orderline.barcode_id)
                    res.barcode_id = orderline.barcode_id;
                if (orderline.barcode)
                    res.barcode = orderline.barcode;
                return res;
            }


        };
    Registries.Component.extend(TicketScreen, PricelistExtTicketScreen);
});
