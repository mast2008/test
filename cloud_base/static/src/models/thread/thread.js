/** @odoo-module **/

import { registerPatch } from "@mail/model/model_core";
import { attr, many } from "@mail/model/model_field";


registerPatch({
    name: "Thread",
    fields: {
        folderExist: attr({ default: 0 }),
        cloudsFolderId: attr({ default: false }),
        folderDomain: attr({ default: false }),
        folderOriginThreadAttachments: many("Attachment"),
        /*
         * Re-write to show our folder-related attachments, but keep OriginThreadAttachments for messages
         * When folder is not chosen, we show standard attachments
        */ 
        allAttachments: {
            compute() {
                const originAttachments = this.cloudsFolderId ? this.folderOriginThreadAttachments : this.originThreadAttachments;
                const allAttachments = [...new Set(originAttachments.concat(this.attachments))]
                    .filter((a) => {
                        return !a.forDelete;
                    })
                    .sort((a1, a2) => {
                        if (!a1.isUploading && a2.isUploading) { return 1 }
                        if (a1.isUploading && !a2.isUploading) { return -1 }
                        return Math.abs(a2.id) - Math.abs(a1.id);
                    });
                return allAttachments;
            },
        },
    },
    recordMethods: {
        /*
        * Re-write to fetch the folder associated with the current object
        * Here we only check whether the folded actually exists, it will be updated when jstree is triggered
        */
        async fetchData(requestList) {
            const _super = this._super.bind(this);
            const folderExist = await this.messaging.rpc({
                route: "/cloud_base/folder",
                params: { thread_id: this.id, thread_model: this.model },
            }, { shadow: true });
            this.update({ folderExist: folderExist });
            if (this.folderDomain && this.cloudsFolderId) {
                await this.fetchFolderAttachments();
            };
            return _super(...arguments);
        },
        /*
        * The method to get attachments linked to the currently selected folder
        */
        async fetchFolderAttachments() {
            const attachmentsData = await this.messaging.rpc({
                route: "/cloud_base/attachments/data",
                params: {
                    thread_id: this.id,
                    thread_model: this.model,
                    folder_domain: this.folderDomain,
                    checked_folder: this.cloudsFolderId,
                },
            }, { shadow: true });
            if (!this.exists()) {
                return;
            };
            this.update({
                areAttachmentsLoaded: true,
                isLoadingAttachments: false,
                folderOriginThreadAttachments: attachmentsData,
            });
        },
        /*
         * Refresh attachment box when checked folder is changed
        */
        async refreshForFolder(folderDomain, cloudsFolderId) {
            if (this.isTemporary) { return };
            this.update({
                isLoadingAttachments: true,
                cloudsFolderId: cloudsFolderId,
                folderDomain: folderDomain,  
            });
            await this.fetchFolderAttachments();
        },
    },
});
