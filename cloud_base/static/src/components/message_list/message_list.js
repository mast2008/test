/** @odoo-module **/

import { MessageList } from "@mail/components/message_list/message_list";
import { patch } from "@web/core/utils/patch";


patch(MessageList.prototype, "cloud_base_message_list_prototype", {
    /*
    * Re-write to fix the scroll error when there is no getScrollableElement
    */
    _willPatch() {
        const lastRenderedValues = this._lastRenderedValues();
        if (!lastRenderedValues) {
            return;
        }
        const { messageListView } = lastRenderedValues;
        if (!messageListView.exists()) {
            return;
        }
        const scrollableElement = messageListView.getScrollableElement();
        if (!scrollableElement) {
            return;
        }
        this._willPatchSnapshot = {
            scrollHeight: scrollableElement.scrollHeight,
            scrollTop: scrollableElement.scrollTop,
        };
    }
});
