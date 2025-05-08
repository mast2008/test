/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";

export class NoArchiveListController extends ListController {
    setup() {
        super.setup(...arguments);
        this.archiveEnabled = false;
    }
}
