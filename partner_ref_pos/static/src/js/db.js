odoo.define('partner_ref_pos.DB', function (require) {
"use strict";
//var core = require('web.core');
/* The PosDB holds reference to data that is either
 * - static: does not change between pos reloads
 * - persistent : must stay between reloads ( orders )
 */
var PosDB = require('point_of_sale.DB');
PosDB.include({
	_partner_search_string: function(partner){
		var str = this._super(partner);
		if (partner.ref)
        	str = str.replace('\n','')+'|' + partner.ref + '\n';
		return str;
    },
});
});


