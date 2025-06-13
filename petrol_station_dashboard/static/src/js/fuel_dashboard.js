/** @odoo-module **/
console.log('*********************************************************888')
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");

export class FuelNozzleDashboard extends Component{
    setup() {
            super.setup(...arguments);
            this.orm = useService('orm');
            this.action = useService('action');
            this.actionService = useService("action");
            this.state = useState({
                data : [],
                employees :[],
                selected_employees_list :[],
                leads : [],
                selected_lead_list:[],
                opps : [],
                selected_opps_list:[],
                date_range: null,
                from_to : {},
            });
            this.load_data();
            onWillStart(this.onWillStart);
    }

    async onWillStart() {
        console.log('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        return this.load_data();
    }
    async load_data() {
        console.log('+++++++++++++++++++++++++++++++++++++++++++++++')
        var self = this;
        try{
            var data =await self.orm.call("petrol.station.pump", "fetch_data", [[]]);
            self.state.data = data['data']
            self.state.title = data['title']
            self.state.emp_data = data['emp_data']
        } catch (el) {
            window.location.href;
        }
    }

    async open_wizard(){
        console.log('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        var end_time = $(event.currentTarget).parents('form').find('#end_time').val()
        var end_reading = $(event.currentTarget).parents('form').find('#end_reading_1').val()
        var st_reading = $(event.currentTarget).attr("e_read")
        var en_type = $(event.currentTarget).attr("type")
        var start_km = $(event.currentTarget).attr('start_km')
        var fleet = $(event.currentTarget).attr('fleet')
        var petty_status = $(".open_wizard").attr('petty_status')
        var petty_cash_new = $(".open_wizard").attr('petty_cash_new')
        var id =$(event.target).attr("id")
        var emp_id =$(event.target).attr("emp_id")
        $(".pause_triger_function").attr('id', id);
        $(".pause_triger_function").attr('emp_id', emp_id);
        $("#start_reading").attr('value', $(event.target).attr("e_read"));
        $("#fuel_name").attr('value', $(event.target).attr("fuel_id"));
        $("#pump_sno").attr('value', $(event.target).attr("s_no"));
        if (en_type == "nozzle"){
            if (end_time == false && Number(end_reading) == 0.00){
                $("#id01").css("display", "block");
                if (petty_status == 'true'){
                    $("#petty_cash_amount").attr("readonly", "1");
                    $("#petty_cash_amount").attr("value",Number(petty_cash_new));
                }
                else{
                    $("#petty_cash_amount").attr("required", "1");
                    $("#petty_cash_amount").attr("value", false);
                }
                var val_fuel = await this.orm.call("petrol.station.pump", "get_fuel_list", [[], id]);
            }
            else if (end_time == false && Number(end_reading) >= 0.00){
                alert("Please Enter the End Time!");
            }
            else if (end_time != false && Number(end_reading) == 0.00){
                alert("Please Enter the End Reading!");
            }
            else if (end_time != false && Number(end_reading) <= Number(st_reading)){
                alert("End Reading must be greater than Start Reading");
            }
            else{
                $("#id01").css("display", "block");
                $("#petty_cash_amount").attr("readonly", "1");
                $("#petty_cash_amount").attr("value",Number(petty_cash_new));
                var val_fuel =await this.orm.call("petrol.station.pump", "get_fuel_list", [[], id]);
                this._onchange_end_time(id, end_time, end_reading)
                $("#end_reading").attr('value', end_reading);
                var final =end_reading - $('#start_reading').val()
                $("#cum_sale").attr('value', final.toFixed(3));
            }
        }
        if (en_type == "truck"){
            $("#id02").css("display", "block");
            $("#vehicle_name").attr('value', fleet);
            $("#start_km").attr('value', start_km);
        }
        return false;

    }

    async calculate_total_km() {
        var start = $('#start_km').val()
        var end = $('#end_km').val()
        if (Number(start) >= Number(end)){
            alert("Ending KM must be Greater than Staring KM!");
        }
        else{
            var final = end - start
            $("#total_km").attr('value', final);
        }
    }
    async cancelBtn() {
        $("#id01").css("display", "none");
    }
    end_reading(){
        var start = $('#start_reading').val()
        var end = $('#end_reading').val()
        var final = end - start
        $("#cum_sale").attr('value', final);
    }

    async pause_trigger_function(event) {
        var en_type = $(event.currentTarget).attr('aa')
        var self = this;
        var dict = {}
        var id = $(event.currentTarget).attr('id')
        console.log('+++++++++++++', en_type)
        if (en_type == 'nozzle'){
            if ($('#advance_amount').val() == false || $('#advance_amount').val() == 0.00){
                alert("Please Enter the Advance Amount!");
            }
            else{
                var petty_amount = $('#petty_cash_amount').val()
                dict['pump_sno'] = $('#pump_sno').val()
                dict['start_reading'] = $('#start_reading').val()
                dict['end_reading'] = $('#end_reading').val()
                dict['cum_sale'] = $('#cum_sale').val()
                dict['advance_amount'] = $('#advance_amount').val()
                var employee = $(".pause_triger_function").attr('emp_id')
                dict['id'] = id
                dict['emp_id'] = $('.pause_triger_function').attr('emp_id')
                if ($('.pause_triger_function').attr('sub_emp_id') == false){
                    dict['sub_id'] = false
                    dict['sub_emp_id'] = false
                }
                else{
                    dict['sub_id'] = $(".sub_employee option:selected").data('sub-id')
                    dict['sub_emp_id'] = $('.pause_triger_function').attr('sub_emp_id')
                }
                console.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^6', dict)
                await this.orm.call("petrol.station.pump.line", "create_record", [[], dict]);
                var petty_cash_amt = $('#petty_cash_amount').val()
                var petty_status = $(".open_wizard").attr('petty_status')
                if (petty_cash_amt > Number(0.00) && petty_status != 'true'){
                    await this.orm.call("petrol.station.pump", "create_journal_entry", [[], id, petty_cash_amt, employee]);
                    await this.orm.call("petrol.station.pump", "update_petty_cash", [[], id, petty_amount]);
                }
                if (($('#end_reading').val() != false) && Number($('#end_reading').val()) > Number($('#start_reading').val())){
                    this._onchange_close_statement(id)
                }
                $("#id01").css("display", "none");
                window.location.reload()
            }
        }
        if (en_type == 'truck'){
            var array = []
            var beta = {}
            var food = {}
            var maintenance = {}
            var loading = {}
            var rto = {}
            var commission = {}
            var amount = $('#total_amount').val()
            var start_km = $('#start_km').val()
            var end_km = $('#end_km').val()
            beta['beta'] = $('#beta_expense').val()
            food['food'] = $('#food_expense').val()
            maintenance['maintenance'] = $('#maintenance_service').val()
            loading['loading'] = $('#loading_expense').val()
            rto['rto'] = $('#rto_expense').val()
            commission['commission'] = $('#commission_expense').val()
            array.push(beta)
            array.push(food)
            array.push(maintenance)
            array.push(loading)
            array.push(rto)
            array.push(commission)
            if (Number(amount) <= 0.00){
                alert("Total amount must be greater than zero!");
            }
            if(Number(end_km) <= start_km){
                alert("End KM must be grater than Start KM!");
            }
            else{
                var val_fuel =await this.orm.call("petrol.station.pump", "rental_truck_invoice", [[], id, array, amount, start_km, end_km]);
                $("#id01").css("display", "none");
                window.location.reload()
            }
        }
    }
    async pump_data_function(event) {
        var self = this;
        var id =$(event.target).attr('id');
        var en_type = $(event.currentTarget).attr('type')
        event.stopPropagation();
        event.preventDefault();
        this.actionService.doAction({
            name: _t("Pump Line Datas"),
            type: 'ir.actions.act_window',
            res_model: 'petrol.station.pump.line',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['petrol_pump', '=', Number(id)],['quotation_create','=', false]],
            target: 'current'
        })
        if (en_type == 'tank'){
            this.actionService.doAction({
                name: _t('Bouch Details'),
                type: 'ir.actions.act_window',
                res_model: 'bouches.entry.details',
                context:{'default_bouche_id':Number(id)},
                target: 'current',
                views: [[false, 'form']],
            });
        }
    }
    async _onchange_end_time(id, end_time, end_reading) {
        await this.orm.call("petrol.station.pump", "update_end_time", [[], end_time, end_reading, id]);
    }

    async _onchange_close_statement(id) {
        await this.orm.call("petrol.station.pump", "update_close_statement", [[], id]);
    }

}
FuelNozzleDashboard.template = 'FuelNozzleDashboard'
registry.category("actions").add("pump_dashboard", FuelNozzleDashboard)
