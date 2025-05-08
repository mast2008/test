/** @odoo-module **/

import { registerPatch } from "@mail/model/model_core";

var promises = []

registerPatch({
    name: "FileUploader",
    recordMethods: {
        /*
        * Re-write to update folder
        * We do not change _createFormData since in this case it will be needed to fully redevelop the controller
        */
        _onAttachmentUploaded({ attachmentData, composer, thread }) {
            if (thread && thread.cloudsFolderId && !composer) {
                // When we are from composer (so !composer is true), message will be allocated to the folder in postprocess
                promises.push(this.messaging.rpc({
                    model: "ir.attachment",
                    method: "write",
                    args: [[attachmentData.id], {"clouds_folder_id": thread.cloudsFolderId}]
                }))
            };
            return this._super(...arguments);
        },
        /*
        * Re-write to trigger reload since attachment folder might be updated
        */
        async uploadFiles(files) {
            await this._super(...arguments);
            if (this.thread && this.thread.cloudsFolderId) {
                await Promise.all(promises);
                await this.thread.fetchFolderAttachments();
            }
        },
    },
});
