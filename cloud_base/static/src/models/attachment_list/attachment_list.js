/** @odoo-module **/

import { registerPatch } from "@mail/model/model_core";


registerPatch({
    name: "AttachmentList",
    fields: {
        /**
         * Re-write to consider synced attachments as not images
         */
        imageAttachments: {
            compute() {
                return this.attachments.filter(attachment => attachment.isImage && !attachment.cloudSynced);
            },
        },
        /**
         * Re-write to consider synced images as cards
         */
        nonImageAttachments: {
            compute() {
                return this.attachments.filter(attachment => !attachment.isImage || attachment.cloudSynced);
            },
        },
    },
});
