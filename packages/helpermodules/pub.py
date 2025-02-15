"""Modul, das die publish-Verbindung zum Broker bereit stellt.
"""

import json
import logging
import os

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

log = logging.getLogger(__name__)


class PubSingleton:
    def __init__(self) -> None:
        self.client = mqtt.Client("openWB-python-bulkpublisher-" + str(os.getpid()))
        self.client.connect("localhost", 1886)
        self.client.loop_start()

    def pub(self, topic: str, payload, qos: int = 0, retain: bool = True) -> None:
        try:
            if payload == "":
                self.client.publish(topic, payload, qos=qos, retain=retain)
            else:
                self.client.publish(topic, payload=json.dumps(payload), qos=qos, retain=retain)
        except Exception:
            log.exception("Fehler im pub-Modul")


class Pub:
    instance = None

    def __init__(self) -> None:
        if not Pub.instance:
            Pub.instance = PubSingleton()

    def __getattr__(self, name):
        return getattr(self.instance, name)


def pub_single(topic, payload, hostname="localhost", no_json=False):
    """ published eine einzelne Nachricht an einen Host, der nicht der localhost ist.

        Parameter
    ---------
    topic : str
        Topic, an das gepusht werden soll
    payload : int, str, list, float
        Payload, der gepusht werden soll. Nicht als json, da ISSS kein json-Payload verwendet.
    hostname: str
        IP des Hosts
    no_json: bool
        Kompatibilität mit ISSS, die ramdisk verwenden.
    """
    try:
        if no_json:
            publish.single(topic, payload, hostname=hostname, retain=True)
        else:
            publish.single(topic, json.dumps(payload), hostname=hostname, retain=True)
    except Exception:
        log.exception(f"Fehler im pub-Modul. Host {hostname}")
