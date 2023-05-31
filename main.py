import datetime
import logging
import re
from dataclasses import dataclass
from dateutil import parser
from datetime import time, date, datetime

log = logging.getLogger(__name__)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"))
log.addHandler(consoleHandler)
# LogLevel
log.setLevel(logging.DEBUG)

LEVEL_EXCEPTIONS = ["WARN", "FATAL", "TRACE", "ERROR"]

@dataclass
class ChargingPeriod:
    charge_point: str
    start: datetime
    stop: datetime = None

@dataclass
class DataPoint:
    target: str
    timestamp: datetime
    name: str
    value: str


def read_log_file(filename: str):
    log.debug(f"filename: {filename}")
    with open(filename, 'r', encoding='UTF-8') as file:
        rex = re.compile(
            r".*]:\s\[(?P<target>.*)]\s(?P<level>DEBUG|WARN|INFO|ERROR|FATAL)\s(?P<date>\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2})\s(?P<message>.*)")
        name_value_re = re.compile(r"(?P<name>.*):\s(?P<value>.*)")
        charging_periods = {}
        data_points = []
        while line := file.readline():
            result = rex.match(line)
            if result and result.group("level") not in LEVEL_EXCEPTIONS:
                # log.debug(result.groupdict())
                timestamp = parser.parse(result.group("date"))
                target = result.group("target").strip()

                if result.group("level") == "INFO" and result.group("message") == "start charging ->":
                    # start charging
                    if target not in charging_periods:
                        charging_periods[target] = []
                    charging_periods[target] += [ChargingPeriod(
                        charge_point=target,
                        start=timestamp
                    )]

                elif result.group("level") == "INFO" and result.group("message") == "stop charging <-":
                    # stop charging
                    if target in charging_periods:
                        for cp in charging_periods[target]:
                            if not cp.stop:
                                cp.stop = timestamp
                                break

                elif result.group("level") == "DEBUG":
                    # logging line to analyze
                    value_result = name_value_re.match(result.group("message"))
                    if value_result:
                        data_points += [DataPoint(
                            name=value_result.group("name"),
                            value=value_result.group("value"),
                            timestamp=timestamp,
                            target=target,
                        )]
                else:
                    # undefined / uninteresting line
                    log.debug(f"doing nothing: {result.group('message')}")
        log.debug(f"charging_periods: {charging_periods}")
        log.debug(f"data_points: {data_points}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    file = "evcc_20230525_20230529.log"
    read_log_file(file)
