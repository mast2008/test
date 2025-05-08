/** @odoo-module **/

import { AttachmentBox } from "@mail/components/attachment_box/attachment_box";
import { patch } from "@web/core/utils/patch";

patch(AttachmentBox.prototype, {
    /*
    * Getter for threadRecord
    */
    get threadRecord() {
        return this.props.record.chatter.thread;
    },
    /*
    * The method to prepare jstreecontainer props
    */
    getJsTreeProps(key) {
        return {
            jstreeId: key,
            onUpdateSearch: this.onRefreshAttachmentBoxWithFolder.bind(this),
            kanbanView: false,
            parentModel: this,
            resModel: this.threadRecord.model,
            resId: this.threadRecord.id,
        };
    },
    /*
    * The method to prepare the domain by the JScontainer and notify searchmodel
    */
    async onRefreshAttachmentBoxWithFolder(jstreeId, domain) {
        await this.threadRecord.refreshForFolder(domain, this.cloudsFolderId);
    },
});