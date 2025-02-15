import logging
import RPi.GPIO as GPIO
import time

from helpermodules.pub import Pub

log = logging.getLogger(__name__)


def read():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        button1_state = GPIO.input(8)
        button2_state = GPIO.input(9)

        time.sleep(10.2)

        if not button1_state:
            Pub().pub("openWB/set/general/ripple_control_receiver/r1_active", True)
            time.sleep(0.2)
        else:
            Pub().pub("openWB/set/general/ripple_control_receiver/r1_active", False)
            time.sleep(0.2)
        if not button2_state:
            Pub().pub("openWB/set/general/ripple_control_receiver/r2_active", True)
            time.sleep(0.2)
        else:
            Pub().pub("openWB/set/general/ripple_control_receiver/r2_active", False)
            time.sleep(0.2)
    except Exception:
        GPIO.cleanup()
        log.exception()
