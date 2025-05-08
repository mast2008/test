/** @odoo-module **/

import { registerPatch } from "@mail/model/model_core";
import { attr } from "@mail/model/model_field";

registerPatch({
    name: "Attachment",
    modelMethods: {
        /*
         * Rewrite to pass sync-related properties
        */
        convertData(data) {
            const data2 = this._super(data);
            if ("cloudSynced" in data && data.cloudSynced) { data2.cloudSynced = true }; 
            if ("mimetype" in data) {
                if (data.mimetype != "application/octet-stream") { data2.cloudDownloadable = true };
            };
            if ("url" in data) {
                if (data.url) { data2.cloudURL = data.url };
            };
            return data2
        },
    },
    fields: {
        cloudURL: attr({ default: false }),
        cloudSynced: attr({ default: false }),
        cloudDownloadable: attr({ default: false }),
        forDelete: attr({ default: false }),
        cloud_key: attr({ default: false })
    },
});
