#!/usr/bin/env python3
import logging
import pathlib
import time
from pathlib import Path
from typing import Dict, List, Union

from helpermodules import compatibility
from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_soc import AbstractSoc
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.tesla import api

log = logging.getLogger("soc."+__name__)


def get_default_config() -> Dict:
    return {
        "name": "Tesla",
        "type": "tesla",
        "id": 0,
        "configuration": {
                "tesla_ev_num": 0
        }
    }


class TeslaConfiguration:
    def __init__(self, id: int, tesla_ev_num: int):
        self.id = id
        self.tesla_ev_num = tesla_ev_num

    @staticmethod
    def from_dict(device_config: dict):
        try:
            values = [device_config["id"], device_config["configuration"]["tesla_ev_num"]]
        except KeyError as e:
            raise Exception(
                'Illegal configuration <{}>: Expected object with properties: device_config["id"], '.format(
                    device_config) +
                'device_config["configuration"]["tesla_ev_num"]'
            ) from e
        return TeslaConfiguration(*values)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, TeslaConfiguration]):
        self.config = device_config \
            if isinstance(device_config, TeslaConfiguration) \
            else TeslaConfiguration.from_dict(device_config)
        self.value_store = store.get_car_value_store(self.config.id)
        self.component_info = ComponentInfo(self.config.id, "Tesla", "vehicle")
        self.token_file = self.get_token_file(self.config.id) if not compatibility.is_ramdisk_in_use() else ""

    def get_token_file(self, id: int) -> str:
        token_file = str(pathlib.Path(__file__).resolve().parents[0]) + "/tokens.ev" + str(id)
        if not Path(token_file).is_file():
            raise FaultState.error("Kein Token in "+token_file+" gefunden.")
        return token_file

    def update(self, charge_state: bool = False) -> None:
        with SingleComponentUpdateContext(self.component_info):
            if charge_state is False:
                self.__wake_up_car()
            soc, range = api.request_soc_range(vehicle=self.config.tesla_ev_num, token_file=self.token_file)
            self.value_store.set(CarState(soc, range))

    def __wake_up_car(self):
        log.debug("Tesla"+str(self.config.id)+": Waking up car.")
        counter = 0
        state = "offline"
        while counter <= 12:
            state = api.post_wake_up_command(vehicle=self.config.tesla_ev_num, token_file=self.token_file)
            if state == "online":
                break
            counter = counter+1
            time.sleep(5)
            log.debug("Tesla "+str(self.config.id)+": Loop: "+str(counter)+", State: "+str(state))
        log.info("Tesla "+str(self.config.id)+": Status nach Aufwecken: "+str(state))
        if state != "online":
            raise FaultState.error("EV"+str(self.config.id)+" konnte nicht geweckt werden.")


def read_legacy(id: int,
                token_file: str,
                tesla_ev_num: int,
                charge_state: bool):

    log.debug('SoC-Module tesla num: ' + str(id))
    log.debug('SoC-Module tesla token_file: ' + str(token_file))
    log.debug('SoC-Module tesla tesla_ev_num: ' + str(tesla_ev_num))
    log.debug('SoC-Module tesla charge_state: ' + str(charge_state))

    config = TeslaConfiguration(id, tesla_ev_num)
    soc = Soc(config)
    soc.token_file = token_file
    soc.update(charge_state)


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)
