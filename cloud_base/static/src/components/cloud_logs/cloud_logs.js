/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillDestroy, onWillStart, useState } from "@odoo/owl";

const componentModel = "clouds.log";

export class CloudLogs extends Component {
    setup() {
        this.searchString = "";
        this.refreshInterval = false;
        this.needPatch = false;
        this.state = useState({
            loadMore: false,
            firstLog: false,
            lastLog: false,
            cloudClients: [],
            selectedClients: [],
            activeTasks: 0,
            failedTasks: 0,
            logLevels: ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
            selectedLogLevels: [],
            searchString: false,
        });

        this.orm = useService("orm");
        this.actionService = useService("action");
        this.uiService = useService("ui");

        onWillStart(async () => {
            await this._onLoadAllElements();
        });

        onMounted(async () => {
            this.logsWrapContainer = document.querySelector(".cloud-logs-screen-wrap");
            this.logsMainContainer = document.querySelector(".cloud-logs-main");
            this.logsMain = this.logsMainContainer;
            this.logsMoreBtn = document.querySelector(".clouds-logs-more-btn-div");
            this.cloudLogsSearchInput = document.getElementById("cloud_logs_search_input");
            this.logsMain.innerHTML = this.htmlLogs;
            this._scrollToTheBottom(false);
            this._setRefreshInterval();
        });

        onWillDestroy(() => {
            this._clearRefreshInterval();
        });
    }

    async _onLoadSyncLogs() {
        const syncLogsDict = await this._loadSyncLogs();
        Object.assign(this.state, {
            loadMore: syncLogsDict.load_more_btn,
            firstLog: syncLogsDict.first_log,
            lastLog: syncLogsDict.last_log,
        });
        this.htmlLogs = syncLogsDict.log_html || "";
        if (this.logsMain) {
            this.logsMain.innerHTML = this.htmlLogs;
        }
    }

    async _onRefreshSyncLogs() {
        const newLogsDict = await this._loadSyncLogs({ last_log: this.state.lastLog });
        if (newLogsDict.log_html) {
            this.state.lastLog = newLogsDict.last_log;
            this.logsMain.innerHTML += newLogsDict.log_html;
        }
    }

    async _onLoadCloudClients() {
        const cloudClients = await this.orm.call(
            componentModel,
            "action_get_cloud_clients",
            [this.state.selectedClients]
        );
        if (JSON.stringify(this.state.cloudClients) !== JSON.stringify(cloudClients)) {
            this.state.cloudClients = cloudClients;
        }
    }

    async _onLoadQueue() {
        const logsQueue = await this.orm.call(
            componentModel,
            "action_get_cloud_queue",
            [this.state.selectedClients]
        );
        if (
            this.state.activeTasks !== logsQueue.active_tasks ||
            this.state.failedTasks !== logsQueue.failed_tasks
        ) {
            this.state.activeTasks = logsQueue.active_tasks;
            this.state.failedTasks = logsQueue.failed_tasks;
        }
    }

    async _onLoadAllElements() {
        await Promise.all([
            this._onLoadQueue(),
            this._onLoadCloudClients(),
            this._onLoadSyncLogs(),
        ]);
    }

    async _onRefreshAllElements() {
        await Promise.all([
            this._onLoadQueue(),
            this._onLoadCloudClients(),
            this._onRefreshSyncLogs(),
        ]);
    }

    async onLoadMoreLogs(event) {
        event.preventDefault();
        event.stopPropagation();
        const newLogsDict = await this._loadSyncLogs({ first_log: this.state.firstLog });
        if (newLogsDict.log_html) {
            this.state.firstLog = newLogsDict.first_log;
            this.state.loadMore = newLogsDict.load_more_btn;
            this.logsMain.innerHTML = newLogsDict.log_html + this.logsMain.innerHTML;
        }
    }

    _onSearchChange(event) {
        this.searchString = event.target.value;
    }

    async _onSearchExecute() {
        this._clearRefreshInterval();
        this.state.searchString = this.searchString;
        await this._onLoadAllElements();
        this.needPatch = true;
    }

    _onSearchkeyUp(event) {
        if (event.key === "Enter") {
            this._onSearchExecute();
        }
    }

    _onSearchClear() {
        this.cloudLogsSearchInput.value = "";
        this.searchString = "";
        this._onSearchExecute();
    }

    async _onToggleCloudClient(event, cloudClient) {
        this._clearRefreshInterval();
        if (event.target.checked) {
            if (!this.state.selectedClients.includes(cloudClient)) {
                this.state.selectedClients.push(cloudClient);
            }
        } else {
            this.state.selectedClients = this.state.selectedClients.filter(
                (value) => value !== cloudClient
            );
        }
        await this._onLoadAllElements();
        this.needPatch = true;
    }

    async _onToggleLogLevel(event, logLevel) {
        this._clearRefreshInterval();
        if (event.target.checked) {
            if (!this.state.selectedLogLevels.includes(logLevel)) {
                this.state.selectedLogLevels.push(logLevel);
            }
        } else {
            this.state.selectedLogLevels = this.state.selectedLogLevels.filter(
                (value) => value !== logLevel
            );
        }
        await this._onLoadAllElements();
        this.needPatch = true;
    }

    async _onOpenCloudClient(cloudClient) {
        if (Number.isInteger(cloudClient)) {
            const action = await this.orm.call(
                "clouds.client",
                "action_get_formview_action",
                [cloudClient]
            );
            this.actionService.doAction(action);
        }
    }

    async _onOpenQueue(onlyFailed) {
        const action = await this.orm.call(
            "clouds.log",
            "action_open_tasks",
            [this.state.selectedClients, onlyFailed]
        );
        this.actionService.doAction(action);
    }

    async _onExportLogs() {
        this.uiService.block();
        await download({
            url: "/cloud_base/export_logs",
            data: {
                search_name: this.state.searchString || "",
                selected_clients: JSON.stringify(this.state.selectedClients),
                log_levels: JSON.stringify(this.state.selectedLogLevels),
            },
        });
        this.uiService.unblock();
    }

    async _loadSyncLogs(logArgsDict = {}) {
        return await this.orm.call(
            componentModel,
            "action_prepare_logs_html",
            [
                logArgsDict,
                this.state.searchString,
                this.state.selectedClients,
                this.state.selectedLogLevels,
            ]
        );
    }

    _setRefreshInterval() {
        this._clearRefreshInterval();
        this.refreshInterval = setInterval(async () => {
            const baseHeight = this.logsMainContainer.offsetHeight + 20 + this.logsMoreBtn.offsetHeight;
            await this._onRefreshAllElements();
            this._scrollToTheBottom(baseHeight);
        }, 6000); // once in 6 seconds
    }

    _clearRefreshInterval() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = false;
        }
    }

    _scrollToTheBottom(baseHeight) {
        const scrollHeight = this.logsMainContainer.offsetHeight + 20 + this.logsMoreBtn.offsetHeight;
        if (baseHeight) {
            if (baseHeight - (this.logsWrapContainer.scrollTop + this.logsWrapContainer.offsetHeight) > 200) {
                return;
            }
        }
        this.logsWrapContainer.scrollTo({
            top: scrollHeight,
            behavior: "smooth",
        });
        this.previousHeight = scrollHeight;
    }
}

CloudLogs.template = "cloud_base.CloudLogs";

registry.category("actions").add("cloud.base.log", CloudLogs);