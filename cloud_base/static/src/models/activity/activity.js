/** @odoo-module **/

import { registerPatch } from "@mail/model/model_core";

registerPatch({
    name: "Activity",
    recordMethods: {
        /*
         * Rewrite to await loaded attachments
        */
        async markAsDone({ attachments = [], feedback = false }) {
            const _super = this._super.bind(this);
            const attachmentsUploaded = await Promise.all(attachments);
            return _super({attachmentsUploaded, feedback});
        },
    },
});
