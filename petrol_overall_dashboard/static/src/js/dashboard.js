/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { onMounted, Component, useRef } from "@odoo/owl";
import { onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { WebClient } from "@web/webclient/webclient";
const actionRegistry = registry.category("actions");


export class OverAllDashBoard extends Component{
    static template = 'OverAllDashBoardPage';
    static props = ["*"];
    setup() {
        // When the component is about to start, fetch data in tiles
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            dashboards_templates: ['OverAllDashBoard'],
        })

        onWillStart(async () => {
            var data = {}
            var GetData = await this.orm.call('sale.order', 'get_dashboard_all_data', [[],data])
            this.state.company_name = GetData['filters']['company_name']
            this.state.symbol = GetData['data']['symbol']
            this.state.datas = GetData['data']
            console.log("-----22222222222222222222",this.state)

        });
        onMounted(() => {
            var data = {}
            this.title = 'Dashboard'
            this.render_graphs(data);
        });
    }
    get_pro_image_url(id){
            return window.location.origin + '/web/image?model=product.template&field=image_1920&id='+id;
    }
    get_emp_image_url(id){
            return window.location.origin + '/web/image?model=hr.employee&field=image_1920&id='+id;
    }

    render_graphs(data){
        var self = this;
        self.price_line_chart(data)
//
    }

    apply_filter(){
        console.log("----------------77777")
    }

    price_line_chart(){
         var self = this
//         var ctx = self.$(".chart-canvas");


    }

}
registry.category("actions").add("overall_dashboard", OverAllDashBoard)

