/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { CloudManagerKanbanRecord } from "./cloud_manager_kanban_record";
import { CloudManager } from "@cloud_base/components/cloud_manager/cloud_manager";
import { CloudNavigation } from "@cloud_base/components/cloud_navigation/cloud_navigation";


export class CloudManagerKanbanRenderer extends KanbanRenderer {
    /*
    * Prepare props for the CloudManagerManager (right navigation & mass actions component)
    */
    getCloudManagerManagerProps() {
        return {
            currentSelection: this.props.list.selection,
            selection: this.props.list.model.selectedRecords,
            kanbanModel: this.props.list.model,
            canCreate: this.props.archInfo.activeActions.create,
        };
    }
    /*
    * The method to CloudManagerNavigation (left navigation)
    */
    getCloudManagerNavigationProps() {
        return {
            kanbanList: this.props.list,
            kanbanModel: this.props.list.model,
        }
    }
};

CloudManagerKanbanRenderer.template = "cloud_base.CloudManagersKanbanRenderer";
CloudManagerKanbanRenderer.components = Object.assign({}, KanbanRenderer.components, {
    CloudManager,
    CloudNavigation,
    KanbanRecord: CloudManagerKanbanRecord,
});
