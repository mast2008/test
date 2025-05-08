/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { KANBAN_BOX_ATTRIBUTE } from "@web/views/kanban/kanban_arch_parser";
const { xml } = owl;

const notGlobalActions = ["a", ".dropdown", ".oe_kanban_action"].join(",");


export class CloudManagerKanbanRecord extends KanbanRecord {
    /*
    * Re-write to add its own classes for selected kanban record
    */
    getRecordClasses() {
        let result = super.getRecordClasses();
        if (this.props.record.selected) {
            result += " jstr-kanban-selected";
        }
        return result;
    }
    /*
    * The method to manage clicks on kanban record
    */
    onGlobalClick(ev) {
        if (ev.target.closest(notGlobalActions)) {
            // A real action or button is clicked --> need to proceed that
            return;
        }
        else if (ev.target.closest(".o_kanban_image")) {
            // An image is clicked --> standard open record action
            const { openRecord, record } = this.props;
            openRecord(record);
        }
        else {
            // Others clicks --> add to selection/remove from selection
            this.props.record.onRecordClick(ev, {});
        }
    }
    /*
    * The method to manage key presses on kanban view (always add to selection)
    */
    onKeydown(ev) {
        if (ev.key !== "Enter" && ev.key !== " ") {
            return;
        }
        ev.preventDefault();
        return this.props.record.onRecordClick(ev, {});
    }
};

CloudManagerKanbanRecord.template = xml`
    <div
        role="article"
        t-att-class="getRecordClasses()"
        t-on-click.synthetic="onGlobalClick"
        t-on-keydown.synthetic="onKeydown"
        t-ref="root">
        <t t-call="{{ templates['${KANBAN_BOX_ATTRIBUTE}'] }}"/>
    </div>`;
