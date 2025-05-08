/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Domain } from "@web/core/domain";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { loadCSS, loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";

const componentModel = "clouds.folder";

export class CloudJsTreeContainer extends Component {
    setup() {
        this.state = useState({ treeData: null });
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.userService = useService("user");
        this.searchString = "";
        this.lastSearch = false;

        onWillStart(async () => {
            const proms = [
                loadJS("/cloud_base/static/lib/jstree/jstree.min.js"),
                loadCSS("/cloud_base/static/lib/jstree/themes/default/style.css"),
                this._loadTreeData(this.props),
                this._loadSettings(this.props),
            ];
            return Promise.all(proms);
        });

        onMounted(() => {
            this.jsTreeAnchor = $(`#${this.id}`);
            this.jsTreeSearchInput = $(`#jstr_input_${this.id}`)[0];
            this._renderJsTree();
        });
    }

    get id() {
        return this.props.jstreeId;
    }

    async _loadTreeData(props) {
        const jstreeData = await this.orm.call(
            componentModel,
            "action_get_hierarchy",
            [this.id, props.resModel, props.resId]
        );
        this.state.treeData = jstreeData;
    }

    async _loadSettings(props) {
        this.fileManagerRigths = props.kanbanView
            ? false
            : await this.userService.hasGroup("cloud_base.group_cloud_base_user");
    }

    _getJsTreeContextMenu() {
        return {
            select_node: false,
            items: ($node) => {
                const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
                const items = {};

                if ($node.data) {
                    items.downloadZip = {
                        label: _t("Download as archive"),
                        action: () => { window.location = `/cloud_base/folder_upload/${$node.id}` }
                    };
                }

                if ($node.data?.edit_right) {
                    items.createNew = {
                        separator_after: true,
                        label: _t("Create subfolder"),
                        action: () => {
                            const newNode = jsTreeAnchor.create_node($node);
                            jsTreeAnchor.edit(newNode);
                        }
                    };
                }

                if ($node.data?.url) {
                    items.openInClouds = {
                        label: _t("Open in clouds"),
                        action: () => {
                            if ($node.data.url) {
                                window.open($node.data.url, "_blank").focus();
                            } else {
                                alert(_t("This folder is not synced yet"));
                            }
                        }
                    };
                }

                if ($node.data && this.props.kanbanView && $node.data.res_model && $node.data.res_id) {
                    items.openParentObject = {
                        label: _t("Open linked object"),
                        action: () => this._onOpenOdooObject($node)
                    };
                }

                if (this.fileManagerRigths && $node.data) {
                    items.openParentObject = {
                        label: _t("Open in File Manager"),
                        action: () => this._onOpenFileManager(parseInt($node.id))
                    };
                }

                if ($node.data?.rule_related || !$node.data?.edit_right) {
                    items.openNode = {
                        label: _t("Settings"),
                        action: () => this._onEditNodeForm(jsTreeAnchor, $node, true)
                    };
                } else {
                    items.renameNode = {
                        label: _t("Rename"),
                        action: () => jsTreeAnchor.edit($node)
                    };
                    items.editNode = {
                        label: _t("Edit Settings"),
                        action: () => this._onEditNodeForm(jsTreeAnchor, $node, false)
                    };
                    items.archiveNode = {
                        separator_before: true,
                        label: _t("Archive"),
                        action: () => jsTreeAnchor.delete_node($node)
                    };
                }

                return items;
            }
        };
    }

    async _renderJsTree() {
        const defaultChosenFolder = this.props.parentModel.rootParams?.context?.default_chosen_folder;
        const jsTreeKey = this.props.resModel && this.props.resId
            ? `${this.id}_${this.props.resModel}_${this.props.resId}`
            : this.id;

        const jsTreeOptions = {
            core: {
                check_callback: (operation, node, node_parent, node_position) => {
                    if (operation === "move_node" && (!node_parent?.data?.edit_right)) {
                        return false;
                    }
                    return true;
                },
                themes: { icons: true },
                stripes: true,
                multiple: false,
                data: this.state.treeData,
                strings: { "New node": _t("New Folder") },
            },
            plugins: ["state", "changed", "search", "dnd", "contextmenu"],
            state: { key: jsTreeKey },
            search: {
                case_sensitive: false,
                show_only_matches: true,
                fuzzy: false,
                show_only_matches_children: true,
            },
            dnd: {
                is_draggable: (nodes) => {
                    const node = nodes[0];
                    return node.data?.edit_right && !node.data.rule_related;
                }
            },
            contextmenu: this._getJsTreeContextMenu(),
        };

        this.jsTreeAnchor.jstree(jsTreeOptions);
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);

        const eventHandlers = {
            "rename_node.jstree": (event, data) => this._onUpdateNode(jsTreeAnchor, data, false),
            "move_node.jstree": (event, data) => this._onUpdateNode(jsTreeAnchor, data, true),
            "delete_node.jstree": (event, data) => this._onDeleteNode(data),
            "copy_node.jstree": (event, data) => this._onUpdateNode(jsTreeAnchor, data, true),
            "state_ready.jstree": (event, data) => {
                this.jsTreeAnchor.on("changed.jstree", () => this._onUpdateDomain(jsTreeAnchor));
                this.jsTreeAnchor.on("open_node.jstree", () =>
                    this._highlightParent(jsTreeAnchor, jsTreeAnchor.get_selected(), `#${this.id}`)
                );
                this.jsTreeAnchor.on("search.jstree", (event, data) => {
                    if (data.res.length !== 0) {
                        this.lastSearch = data.res[0];
                    }
                });
                this.jsTreeAnchor.on("clear_search.jstree", () => {
                    this.lastSearch = false;
                });

                if (!defaultChosenFolder) {
                    this._onUpdateDomain(jsTreeAnchor);
                } else {
                    jsTreeAnchor.deselect_all(true);
                    jsTreeAnchor.select_node(defaultChosenFolder);
                    this._onUpdateDomain(jsTreeAnchor);
                }
            }
        };

        Object.entries(eventHandlers).forEach(([event, handler]) => {
            this.jsTreeAnchor.on(event, handler);
        });
    }

    async _onUpdateDomain(jsTreeAnchor) {
        const checkedTreeItems = jsTreeAnchor.get_selected();
        if (!checkedTreeItems?.length) {
            let firstShowParentNode = this.lastSearch ||
                jsTreeAnchor.get_node("#").children.find(node => !jsTreeAnchor.is_hidden(node));

            if (firstShowParentNode) {
                jsTreeAnchor.deselect_all(true);
                jsTreeAnchor.select_node(firstShowParentNode);
                return;
            }
        }

        this._highlightParent(jsTreeAnchor, checkedTreeItems, `#${this.id}`);
        await this.props.onUpdateSearch(this.id, this._getDomain(checkedTreeItems));
    }

    _onSearchChange(event) {
        this.searchString = event.target.value;
    }

    _onSearchExecute() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.deselect_all(true);
        this.searchString
            ? this.jsTreeAnchor.jstree("search", this.searchString)
            : this.jsTreeAnchor.jstree("clear_search");
        this._onUpdateDomain(jsTreeAnchor);
    }

    _onSearchkeyUp(event) {
        if (event.key === "Enter") {
            this._onSearchExecute();
        }
    }

    _onSearchClear() {
        this.jsTreeSearchInput.value = "";
        this.searchString = "";
        this.jsTreeAnchor.jstree("clear_search");
    }

    async _onUpdateNode(jsTreeAnchor, data, position) {
        const nodeId = parseInt(data.node.id);
        const newNodeId = isNaN(nodeId)
            ? await this.orm.call(componentModel, "action_create_node", [data.node])
            : await this.orm.call(
                componentModel,
                "action_update_node",
                [nodeId, data.node, position && parseInt(data.position)]
              );

        this._refreshNodeAfterUpdate(data.node, newNodeId);
    }

    async _onDeleteNode(data) {
        await this.orm.call(componentModel, "action_delete_node", [parseInt(data.node.id)]);
    }

    _onAddRootTag() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        const newNode = jsTreeAnchor.create_node("#");
        if (newNode) {
            jsTreeAnchor.edit(newNode);
        }
    }

    async _onEditNodeForm(jsTreeAnchor, node, nodePreventEdit) {
        this.dialogService.add(FormViewDialog, {
            resModel: componentModel,
            resId: parseInt(node.id),
            title: _t("Settings"),
            preventCreate: true,
            preventEdit: nodePreventEdit,
            onRecordSaved: async (formRecord) => {
                jsTreeAnchor.set_text(node, formRecord.data.name);
                if (formRecord.data.parent_id?.[0] && formRecord.data.parent_id[0] !== node.parent) {
                    jsTreeAnchor.move_node(node, formRecord.data.parent_id[0].toString());
                }
                const newNodeId = await this.orm.call(
                    componentModel,
                    "action_js_format_folder_for_js_tree",
                    [[parseInt(node.id)]]
                );
                this._refreshNodeAfterUpdate(node, newNodeId);
            },
        });
    }

    async _onOpenOdooObject(node) {
        this.dialogService.add(FormViewDialog, {
            resModel: node.data.res_model,
            resId: node.data.res_id,
            preventCreate: true,
        });
    }

    async _onOpenFileManager(resId) {
        this.actionService.doAction("cloud_base.ir_attachment_action", {
            additionalContext: { default_chosen_folder: resId },
        });
    }

    _refreshNodeAfterUpdate(node, newData) {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.set_id(node, newData.id);
        jsTreeAnchor.set_text(node, newData.text);
        jsTreeAnchor.set_icon(node, newData.icon);
        node.data = newData.data;
        jsTreeAnchor.deselect_all(true);
        jsTreeAnchor.select_node(node);
    }

    _getDomain(checkedTreeItems) {
        return this.id === "folders"
            ? this._getFolderDomain(checkedTreeItems, "clouds_folder_id")
            : [];
    }

    _getFolderDomain(checkedTreeItems, field) {
        const checkedIds = checkedTreeItems.map(id => parseInt(id));
        this.props.parentModel.cloudsFolderId = checkedIds.length ? checkedIds[0] : false;
        return [[field, "=", this.props.parentModel.cloudsFolderId || -1]];
    }

    _highlightParent(jsTreeAnchor, checkedNodes, jsSelector) {
        $(`${jsSelector} * .jstr-selected-parent`).removeClass("jstr-selected-parent");
        const allParentNodes = [...new Set(
            checkedNodes.flatMap(node => jsTreeAnchor.get_path(node, false, true))
        )];
        allParentNodes.forEach(nodeID => {
            $(`${jsSelector} * .jstree-node#${nodeID}`).addClass("jstr-selected-parent");
        });
    }
}

CloudJsTreeContainer.props = {
    jstreeId: { type: String, required: true },
    kanbanView: { type: Boolean, optional: true },
    parentModel: { type: Object, optional: true },
    resModel: { type: String, optional: true },
    resId: { type: Number, optional: true },
    onUpdateSearch: { type: Function, required: true },
};

CloudJsTreeContainer.defaultProps = {
    jstreeKey: "folders",
};

CloudJsTreeContainer.template = "cloud_base.CloudJsTreeContainer";

registry.category("components").add("CloudJsTreeContainer", CloudJsTreeContainer);