/** @odoo-module **/

import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component } = owl;


export class RuleParent extends Component {
    /*
    * Getter for selectorFieldName: field name for the fields selector
    */
    get selectorFieldName() {
        return this.props.value || "";
    }
    /*
    * Gettter for selectorIsDebugMode (always true)
    */
    get selectorIsDebugMode() {
        return true;
    }
    /*
    * Get res_model name from the 'model' field
    */
    getResModel(props) {
        let resModel = "";
        if (props.record.fieldNames.includes("model")) {
            resModel = props.record.data["model"];
        };
        return resModel;
    }
    /*
    * Filter method of fields selector, the idea is to show only m2o fields
    */
    getFieldsFilter(field) {
        return field.type == "many2one";
    }
    /*
    * Get the value from the fields selector
    */
    update(chain) {
        return this.props.update(chain);
    }
};

RuleParent.supportedTypes = ["char"];
RuleParent.template = "cloud_base.RuleParent";
RuleParent.components = { ModelFieldSelector };
RuleParent.props = {...standardFieldProps };
registry.category("fields").add("parentRuleMany2one", RuleParent);