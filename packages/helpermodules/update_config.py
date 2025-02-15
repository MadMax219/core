import glob
import json
import logging
import re
import time
from typing import List
import paho.mqtt.client as mqtt

from helpermodules.pub import Pub
from helpermodules import measurement_log
from control import chargepoint
from control import ev

log = logging.getLogger(__name__)


class UpdateConfig:
    valid_topic = ["^openWB/bat/config/configured$",
                   "^openWB/bat/set/charging_power_left$",
                   "^openWB/bat/set/switch_on_soc_reached$",
                   "^openWB/bat/get/soc$",
                   "^openWB/bat/get/power$",
                   "^openWB/bat/get/imported$",
                   "^openWB/bat/get/exported$",
                   "^openWB/bat/get/daily_exported$",
                   "^openWB/bat/get/daily_imported$",
                   "^openWB/bat/[0-9]+/get/soc$",
                   "^openWB/bat/[0-9]+/get/power$",
                   "^openWB/bat/[0-9]+/get/imported$",
                   "^openWB/bat/[0-9]+/get/exported$",
                   "^openWB/bat/[0-9]+/get/daily_exported$",
                   "^openWB/bat/[0-9]+/get/daily_imported$",
                   "^openWB/bat/[0-9]+/get/fault_state$",
                   "^openWB/bat/[0-9]+/get/fault_str$",

                   "^openWB/chargepoint/get/power$",
                   "^openWB/chargepoint/get/exported$",
                   "^openWB/chargepoint/get/imported$",
                   "^openWB/chargepoint/get/daily_exported$",
                   "^openWB/chargepoint/get/daily_imported$",
                   "^openWB/chargepoint/template/0$",
                   "^openWB/chargepoint/template/0/autolock/0$",
                   "^openWB/chargepoint/[0-9]+/config$",
                   "^openWB/chargepoint/[0-9]+/get/charge_state$",
                   "^openWB/chargepoint/[0-9]+/get/currents$",
                   "^openWB/chargepoint/[0-9]+/get/fault_state$",
                   "^openWB/chargepoint/[0-9]+/get/fault_str$",
                   "^openWB/chargepoint/[0-9]+/get/plug_state$",
                   "^openWB/chargepoint/[0-9]+/get/phases_in_use$",
                   "^openWB/chargepoint/[0-9]+/get/exported$",
                   "^openWB/chargepoint/[0-9]+/get/imported$",
                   "^openWB/chargepoint/[0-9]+/get/daily_exported$",
                   "^openWB/chargepoint/[0-9]+/get/daily_imported$",
                   "^openWB/chargepoint/[0-9]+/get/power$",
                   "^openWB/chargepoint/[0-9]+/get/voltages$",
                   "^openWB/chargepoint/[0-9]+/get/state_str$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/soc_config$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/soc$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/info$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/config$",
                   "^openWB/chargepoint/[0-9]+/get/rfid$",
                   "^openWB/chargepoint/[0-9]+/get/rfid_timestamp$",
                   "^openWB/chargepoint/[0-9]+/set/charging_ev$",
                   "^openWB/chargepoint/[0-9]+/set/current$",
                   "^openWB/chargepoint/[0-9]+/set/energy_to_charge$",
                   "^openWB/chargepoint/[0-9]+/set/manual_lock$",
                   "^openWB/chargepoint/[0-9]+/set/plug_time$",
                   "^openWB/chargepoint/[0-9]+/set/rfid$",
                   "^openWB/chargepoint/[0-9]+/set/change_ev_permitted$",
                   "^openWB/chargepoint/[0-9]+/set/log/imported_since_mode_switch$",
                   "^openWB/chargepoint/[0-9]+/set/log/imported_since_plugged$",
                   "^openWB/chargepoint/[0-9]+/set/log/chargemode_log_entry$",
                   "^openWB/chargepoint/[0-9]+/set/log/imported_at_mode_switch$",
                   "^openWB/chargepoint/[0-9]+/set/log/imported_at_plugtime$",
                   "^openWB/chargepoint/[0-9]+/set/log/range_charged$",
                   "^openWB/chargepoint/[0-9]+/set/log/timestamp_start_charging$",
                   "^openWB/chargepoint/[0-9]+/set/log/time_charged$",
                   "^openWB/chargepoint/[0-9]+/set/phases_to_use$",
                   "^openWB/chargepoint/[0-9]+/set/charging_ev_prev$",

                   "^openWB/command/max_id/autolock_plan$",
                   "^openWB/command/max_id/charge_template$",
                   "^openWB/command/max_id/charge_template_scheduled_plan$",
                   "^openWB/command/max_id/charge_template_time_charging_plan$",
                   "^openWB/command/max_id/chargepoint_template$",
                   "^openWB/command/max_id/device$",
                   "^openWB/command/max_id/ev_template$",
                   "^openWB/command/max_id/hierarchy$",
                   "^openWB/command/max_id/mqtt_bridge$",
                   "^openWB/command/max_id/vehicle$",
                   "^openWB/command/[A-Za-z0-9_]+/error$",
                   "^openWB/command/todo$",

                   "^openWB/counter/get/hierarchy$",
                   "^openWB/counter/set/invalid_home_consumption$",
                   "^openWB/counter/set/home_consumption$",
                   "^openWB/counter/set/daily_yield_home_consumption$",
                   "^openWB/counter/[0-9]+/get/voltages$",
                   "^openWB/counter/[0-9]+/get/power$",
                   "^openWB/counter/[0-9]+/get/currents$",
                   "^openWB/counter/[0-9]+/get/powers$",
                   "^openWB/counter/[0-9]+/get/power_factors$",
                   "^openWB/counter/[0-9]+/get/fault_state$",
                   "^openWB/counter/[0-9]+/get/fault_str$",
                   "^openWB/counter/[0-9]+/get/frequency$",
                   "^openWB/counter/[0-9]+/get/daily_exported$",
                   "^openWB/counter/[0-9]+/get/daily_imported$",
                   "^openWB/counter/[0-9]+/get/imported$",
                   "^openWB/counter/[0-9]+/get/exported$",
                   "^openWB/counter/[0-9]+/set/consumption_left$",
                   "^openWB/counter/[0-9]+/set/state_str$",
                   "^openWB/counter/[0-9]+/config/max_currents$",
                   "^openWB/counter/[0-9]+/config/max_total_power$",

                   "^openWB/general/extern$",
                   "^openWB/general/extern_display_mode$",
                   "^openWB/general/control_interval$",
                   "^openWB/general/external_buttons_hw$",
                   "^openWB/general/grid_protection_configured$",
                   "^openWB/general/grid_protection_active$",
                   "^openWB/general/mqtt_bridge$",
                   "^openWB/general/grid_protection_timestamp$",
                   "^openWB/general/grid_protection_random_stop$",
                   "^openWB/general/price_kwh$",
                   "^openWB/general/range_unit$",
                   "^openWB/general/notifications/selected$",
                   "^openWB/general/notifications/configuration$",
                   "^openWB/general/notifications/start_charging$",
                   "^openWB/general/notifications/stop_charging$",
                   "^openWB/general/notifications/plug$",
                   "^openWB/general/notifications/smart_home$",
                   "^openWB/general/ripple_control_receiver/configured$",
                   "^openWB/general/ripple_control_receiver/r1_active$",
                   "^openWB/general/ripple_control_receiver/r2_active$",
                   "^openWB/general/chargemode_config/individual_mode$",
                   "^openWB/general/chargemode_config/unbalanced_load_limit$",
                   "^openWB/general/chargemode_config/unbalanced_load$",
                   "^openWB/general/chargemode_config/pv_charging/feed_in_yield$",
                   "^openWB/general/chargemode_config/pv_charging/switch_on_threshold$",
                   "^openWB/general/chargemode_config/pv_charging/switch_on_delay$",
                   "^openWB/general/chargemode_config/pv_charging/switch_off_threshold$",
                   "^openWB/general/chargemode_config/pv_charging/switch_off_delay$",
                   "^openWB/general/chargemode_config/pv_charging/phase_switch_delay$",
                   "^openWB/general/chargemode_config/pv_charging/control_range$",
                   "^openWB/general/chargemode_config/pv_charging/phases_to_use$",
                   "^openWB/general/chargemode_config/pv_charging/bat_prio$",
                   "^openWB/general/chargemode_config/pv_charging/switch_on_soc$",
                   "^openWB/general/chargemode_config/pv_charging/switch_off_soc$",
                   "^openWB/general/chargemode_config/pv_charging/rundown_soc$",
                   "^openWB/general/chargemode_config/pv_charging/rundown_power$",
                   "^openWB/general/chargemode_config/pv_charging/charging_power_reserve$",
                   "^openWB/general/chargemode_config/scheduled_charging/phases_to_use$",
                   "^openWB/general/chargemode_config/instant_charging/phases_to_use$",
                   "^openWB/general/chargemode_config/standby/phases_to_use$",
                   "^openWB/general/chargemode_config/stop/phases_to_use$",
                   "^openWB/general/chargemode_config/time_charging/phases_to_use$",

                   "^openWB/graph/config/duration$",
                   "^openWB/graph/alllivevaluesJson",
                   "^openWB/graph/lastlivevaluesJson$",

                   "^openWB/set/log/request",
                   "^openWB/set/log/data",

                   "^openWB/optional/load_sharing/active$",
                   "^openWB/optional/load_sharing/max_current$",
                   "^openWB/optional/et/active$",
                   "^openWB/optional/et/get/price_list$",
                   "^openWB/optional/et/get/price$",
                   "^openWB/optional/et/get/source$",
                   "^openWB/optional/et/config/max_price$",
                   "^openWB/optional/et/config/provider$",
                   "^openWB/optional/int_display/active$",
                   "^openWB/optional/int_display/on_if_plugged_in$",
                   "^openWB/optional/int_display/pin_active$",
                   "^openWB/optional/int_display/pin_code$",
                   "^openWB/optional/int_display/standby$",
                   "^openWB/optional/int_display/theme$",
                   "^openWB/optional/led/active$",
                   "^openWB/optional/rfid/active$",

                   "^openWB/pv/config/configured$",
                   "^openWB/pv/set/overhang_power_left$",
                   "^openWB/pv/set/reserved_evu_overhang$",
                   "^openWB/pv/set/released_evu_overhang$",
                   "^openWB/pv/set/available_power$",
                   "^openWB/pv/get/exported$",
                   "^openWB/pv/get/power$",
                   "^openWB/pv/get/daily_exported$",
                   "^openWB/pv/get/monthly_exported$",
                   "^openWB/pv/get/yearly_exported$",
                   "^openWB/pv/[0-9]+/config/max_ac_out$",
                   "^openWB/pv/[0-9]+/get/exported$",
                   "^openWB/pv/[0-9]+/get/power$",
                   "^openWB/pv/[0-9]+/get/currents$",
                   "^openWB/pv/[0-9]+/get/energy$",
                   "^openWB/pv/[0-9]+/get/daily_exported$",
                   "^openWB/pv/[0-9]+/get/monthly_exported$",
                   "^openWB/pv/[0-9]+/get/yearly_exported$",
                   "^openWB/pv/[0-9]+/get/fault_state$",
                   "^openWB/pv/[0-9]+/get/fault_str$",

                   "^openWB/vehicle/template/ev_template/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+",
                   "^openWB/vehicle/[0-9]+/charge_template$",
                   "^openWB/vehicle/[0-9]+/ev_template$",
                   "^openWB/vehicle/[0-9]+/name$",
                   "^openWB/vehicle/[0-9]+/soc_module/config$",
                   "^openWB/vehicle/[0-9]+/tag_id$",
                   "^openWB/vehicle/[0-9]+/get/fault_state$",
                   "^openWB/vehicle/[0-9]+/get/fault_str$",
                   "^openWB/vehicle/[0-9]+/get/range$",
                   "^openWB/vehicle/[0-9]+/get/soc$",
                   "^openWB/vehicle/[0-9]+/get/soc_timestamp$",
                   "^openWB/vehicle/[0-9]+/match_ev/selected$",
                   "^openWB/vehicle/[0-9]+/match_ev/tag_id$",
                   "^openWB/vehicle/[0-9]+/control_parameter/submode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/chargemode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/current_plan$",
                   "^openWB/vehicle/[0-9]+/control_parameter/imported_at_plan_start$",
                   "^openWB/vehicle/[0-9]+/control_parameter/prio$",
                   "^openWB/vehicle/[0-9]+/control_parameter/required_current$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_auto_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_perform_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/used_amount_instant_charging$",
                   "^openWB/vehicle/[0-9]+/control_parameter/phases$",
                   "^openWB/vehicle/[0-9]+/set/ev_template$",

                   "^openWB/system/boot_done$",
                   "^openWB/system/dataprotection_acknowledged$",
                   "^openWB/system/debug_level$",
                   "^openWB/system/lastlivevaluesJson$",
                   "^openWB/system/ip_address$",
                   "^openWB/system/version$",
                   "^openWB/system/release_train$",
                   "^openWB/system/update_in_progress$",
                   "^openWB/system/device/[0-9]+/config$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/config$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/timestamp_present$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/power_present$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_imported$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_exported$",
                   "^openWB/system/device/module_update_completed$",
                   "^openWB/system/configurable/soc_modules$",
                   "^openWB/system/configurable/devices_components$",
                   "^openWB/system/configurable/chargepoints$",
                   "^openWB/system/mqtt/bridge/[0-9]+$"
                   ]
    default_topic = (
        ("openWB/chargepoint/template/0", chargepoint.get_chargepoint_template_default()),
        ("openWB/counter/get/hierarchy", []),
        ("openWB/vehicle/0/name", ev.get_vehicle_default()["name"]),
        ("openWB/vehicle/0/charge_template", ev.get_vehicle_default()["charge_template"]),
        ("openWB/vehicle/0/soc_module/config", {"type": None, "configuration": {}}),
        ("openWB/vehicle/0/ev_template", ev.get_vehicle_default()["ev_template"]),
        ("openWB/vehicle/0/tag_id", ev.get_vehicle_default()["tag_id"]),
        ("openWB/vehicle/0/get/soc", ev.get_vehicle_default()["get/soc"]),
        ("openWB/vehicle/template/ev_template/0", ev.get_ev_template_default()),
        ("openWB/vehicle/template/charge_template/0", ev.get_charge_template_default()),
        ("openWB/general/chargemode_config/instant_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/pv_charging/bat_prio", 1),
        ("openWB/general/chargemode_config/pv_charging/switch_on_soc", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_off_soc", 40),
        ("openWB/general/chargemode_config/pv_charging/rundown_power", 1000),
        ("openWB/general/chargemode_config/pv_charging/rundown_soc", 50),
        ("openWB/general/chargemode_config/pv_charging/charging_power_reserve", 200),
        ("openWB/general/chargemode_config/pv_charging/control_range", [0, 230]),
        ("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 5),
        ("openWB/general/chargemode_config/pv_charging/switch_off_delay", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_on_delay", 30),
        ("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 1500),
        ("openWB/general/chargemode_config/pv_charging/feed_in_yield", 15000),
        ("openWB/general/chargemode_config/pv_charging/phase_switch_delay", 7),
        ("openWB/general/chargemode_config/pv_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/scheduled_charging/phases_to_use", 0),
        ("openWB/general/chargemode_config/standby/phases_to_use", 1),
        ("openWB/general/chargemode_config/stop/phases_to_use", 1),
        ("openWB/general/chargemode_config/time_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/individual_mode", True),
        ("openWB/general/chargemode_config/unbalanced_load", False),
        ("openWB/general/chargemode_config/unbalanced_load_limit", 18),
        ("openWB/general/control_interval", 10),
        ("openWB/general/extern", False),
        ("openWB/general/extern_display_mode", "local"),
        ("openWB/general/external_buttons_hw", False),
        ("openWB/general/grid_protection_configured", True),
        ("openWB/general/notifications/selected", "none"),
        ("openWB/general/notifications/plug", False),
        ("openWB/general/notifications/start_charging", False),
        ("openWB/general/notifications/stop_charging", False),
        ("openWB/general/notifications/smart_home", False),
        ("openWB/general/notifications/configuration", {}),
        ("openWB/general/price_kwh", 0.3),
        ("openWB/general/range_unit", "km"),
        ("openWB/general/ripple_control_receiver/configured", False),
        ("openWB/graph/config/duration", 120),
        ("openWB/optional/et/active", False),
        ("openWB/optional/et/config/max_price", 0),
        ("openWB/optional/et/config/provider", {}),
        ("openWB/optional/int_display/active", False),
        ("openWB/optional/int_display/on_if_plugged_in", True),
        ("openWB/optional/int_display/pin_active", False),
        ("openWB/optional/int_display/pin_code", "0000"),
        ("openWB/optional/int_display/standby", 60),
        ("openWB/optional/int_display/theme", "cards"),
        ("openWB/optional/led/active", False),
        ("openWB/optional/load_sharing/active", False),
        ("openWB/optional/load_sharing/max_current", 16),
        ("openWB/optional/rfid/active", False),
        ("openWB/system/dataprotection_acknowledged", False),
        ("openWB/system/debug_level", 30),
        ("openWB/system/device/module_update_completed", True),
        ("openWB/system/ip_address", "unknown"),
        ("openWB/system/release_train", "master"))

    def __init__(self) -> None:
        self.all_received_topics = {}

    def update(self):
        log.debug("Broker-Konfiguration aktualisieren")
        mqtt_broker_ip = "localhost"
        client = mqtt.Client("openWB-updateconfig-" + self.getserial())
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(mqtt_broker_ip, 1886)
        client.loop_start()
        time.sleep(2)
        client.loop_stop()

        try:
            self.__remove_outdated_topics()
            self.__pub_missing_defaults()
            self.__update_version()
            self.__solve_breaking_changes()
        except Exception:
            log.exception("Fehler beim Prüfen des Brokers.")

    def getserial(self):
        """ Extract serial from cpuinfo file
        """
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    return line[10:26]
            return "0000000000000000"

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/#", 2)

    def on_message(self, client, userdata, msg):
        self.all_received_topics.update({msg.topic: msg.payload})

    def __remove_outdated_topics(self):
        # ungültige Topics entfernen
        # aufpassen mit dynamischen Zweigen! z.B. vehicle/x/...
        for topic in self.all_received_topics.keys():
            for valid_topic in self.valid_topic:
                if re.search(valid_topic, topic) is not None:
                    break
            else:
                Pub().pub(topic, "")
                log.debug("Ungültiges Topic zum Startzeitpunkt: "+str(topic))

    def __pub_missing_defaults(self):
        # zwingend erforderliche Standardwerte setzen
        for topic in self.default_topic:
            if topic[0] not in self.all_received_topics.keys():
                log.debug("Setzte Topic '%s' auf Standardwert '%s'" % (topic[0], str(topic[1])))
                Pub().pub(topic[0].replace("openWB/", "openWB/set/"), topic[1])

    def __update_version(self):
        with open("/var/www/html/openWB/web/version", "r") as f:
            version = f.read().splitlines()[0]
        Pub().pub("openWB/set/system/version", version)

    def __solve_breaking_changes(self):
        # prevent_switch_stop auf zwei Einstellungen prevent_phase_switch und prevent_charge_stop aufteilen
        for topic, payload in self.all_received_topics.items():
            if "openWB/vehicle/template/ev_template/" in topic:
                payload = json.loads(str(payload.decode("utf-8")))
                if "prevent_switch_stop" in payload:
                    combined_setting = payload["prevent_switch_stop"]
                    payload.pop("prevent_switch_stop")
                    payload.update({"prevent_charge_stop": combined_setting, "prevent_phase_switch": combined_setting})
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)

        # zu konfiguriertem Wechselrichter die maximale Ausgangsleistung hinzufügen
        for topic, payload in self.all_received_topics.items():
            regex = re.search("(openWB/pv/[0-9]+)/get/fault_state", topic)
            if regex is not None:
                module = regex.group(1)
                if f"{module}/config/max_ac_out" not in self.all_received_topics.keys():
                    Pub().pub(
                        f'{module.replace("openWB/", "openWB/set/")}/config/max_ac_out', 0)

        # Summen in Tages- und Monatslog hinzufügen
        files = glob.glob("/var/www/html/openWB/data/daily_log/*")
        files.extend(glob.glob("/var/www/html/openWB/data/monthly_log/*"))
        for file in files:
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    if isinstance(content, List):
                        try:
                            new_content = {"entries": content, "totals": measurement_log.get_totals(content)}
                            json.dump(new_content, jsonFile)
                            log.debug(f"Format des Logfiles {file} aktualisiert.")
                        except Exception:
                            log.exception(f"Logfile {file} entspricht nicht dem Dateiformat von Alpha 3.")
                except json.decoder.JSONDecodeError:
                    log.exception(
                        f"Logfile {file} konnte nicht konvertiert werden, da es keine gültigen json-Daten enthält.")
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    for e in content["entries"]:
                        for module in e["pv"]:
                            if e["pv"][module].get("imported"):
                                e["pv"][module]["exported"] = e["pv"][module]["imported"]
                    for entry in content["totals"]["pv"]:
                        if content["totals"]["pv"][entry].get("imported"):
                            content["totals"]["pv"][entry]["exported"] = content["totals"]["pv"][entry]["imported"]
                    json.dump(content, jsonFile)
                except Exception:
                    log.exception(f"Logfile {file} konnte nicht konvertiert werden.")

        # prevent_switch_stop auf zwei Einstellungen prevent_phase_switch und prevent_charge_stop aufteilen
        for topic, payload in self.all_received_topics.items():
            if re.search("^openWB/system/device/[0-9]+/config$", topic) is not None:
                payload = json.loads(str(payload.decode("utf-8")))
                if payload["type"] == "http":
                    index = re.search('(?!/)([0-9]*)(?=/|$)', topic).group()
                    for topic, payload in self.all_received_topics.items():
                        if re.search(f"^openWB/system/device/{index}/component/[0-9]+/config$", topic) is not None:
                            payload = json.loads(str(payload.decode("utf-8")))
                            if payload["type"] == "inverter" and "counter_path" in payload["configuration"]:
                                updated_payload = payload
                                updated_payload["configuration"]["exported_path"] = payload[
                                    "configuration"]["counter_path"]
                                updated_payload["configuration"].pop("counter_path")
                                Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
                elif payload["type"] == "json":
                    index = re.search('(?!/)([0-9]*)(?=/|$)', topic).group()
                    for topic, payload in self.all_received_topics.items():
                        if re.search(f"^openWB/system/device/{index}/component/[0-9]+/config$", topic) is not None:
                            payload = json.loads(str(payload.decode("utf-8")))
                            if payload["type"] == "inverter" and "jq_counter" in payload["configuration"]:
                                updated_payload = payload
                                updated_payload["configuration"]["jq_exported"] = payload["configuration"]["jq_counter"]
                                updated_payload["configuration"].pop("jq_counter")
                                Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
