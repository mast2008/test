/** @odoo-module **/

import { CloudManagerKanbanDynamicRecordList } from "./cloud_manager_kanban_dynamic_list";
import { KanbanModel } from "@web/views/kanban/kanban_model";

export class CloudManagerKanbanModel extends KanbanModel {
    /*
    * Re-write to introduce selected records, so our list will be able to save previous selection
    */
    setup(params) {
        this.cloudsFolderId = false;
        if (params.rootState) {
            // restore from previous list (used especially for switching between views)
            this.selectedRecords = params.rootState.selectedRecords || [];
        }
        else {
            this.selectedRecords = [];
        }
        super.setup(...arguments);
    }
    /*
    * The method to add/remove record from SelectedRecords
    */
    _updateModelSelection(record, selected, noReselection) {
        if (!noReselection) {
            if (selected) {
                this.selectedRecords.push(record)
            }
            else {
                this.selectedRecords = this.selectedRecords.filter(rec => rec.id != record.id)
            };
        }
    }
};

export class CloudManagerKanbanRecord extends KanbanModel.Record {
    /**
    * The method to manage kanban records clicks: to add an item to selection
    */
    onRecordClick(ev, options = {}) {
        this.toggleSelection(!this.selected);
    }
    /*
    * Overwrite to save selection for model, not only in a record. The idea is to not update selection after each reload
    */
    toggleSelection(selected, noReselection) {
        super.toggleSelection(selected);
        this.model._updateModelSelection({"id": this.resId, "name": this.data.name}, selected, noReselection);
    }
};

CloudManagerKanbanModel.Record = CloudManagerKanbanRecord;
CloudManagerKanbanModel.DynamicRecordList = CloudManagerKanbanDynamicRecordList;
