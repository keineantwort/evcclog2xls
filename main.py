import logging

from log import init_logger
import re
from dataclasses import dataclass
from dateutil import parser
from datetime import datetime

import xlsxwriter

from excel import *

log = init_logger(log_level=logging.DEBUG)

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
    with open(filename, 'r', encoding='UTF-8') as logfile:
        rex = re.compile(
            r".*]:\s\[(?P<target>.*)]\s(?P<level>DEBUG|WARN|INFO|ERROR|FATAL)\s(?P<date>\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2})\s(?P<message>.*)")
        name_value_re = re.compile(r"(?P<name>.*):\s(?P<value>.*)")
        charging_periods = {}
        data_points = []
        while line := logfile.readline():
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
        log.debug(f"charging_points: {len(charging_periods)}")
        log.debug(f"data_points: {len(data_points)}")
        return charging_periods, data_points


def write_charging_periods(workbook: xlsxwriter.Workbook, charging_periods=None):
    if charging_periods is None:
        charging_periods = {}
    for lp_name, cps in charging_periods.items():
        worksheet = add_worksheet(workbook=workbook, worksheet_name=lp_name,
                                  header_list=[ExcelTableHeader(position=0, label="start", width=30),
                                               ExcelTableHeader(position=1, label="stop", width=30)])
        for idx, cp in enumerate(cps):

            date_format = workbook.add_format({"num_format": "dd.mm.yyyy hh:mm:ss",
                                               "align": "left"})
            worksheet.write_datetime(idx + 1, 0, cp.start, date_format)
            if cp.stop:
                worksheet.write_datetime(idx + 1, 1, cp.stop, date_format)


def main():
    # file = "evcc_20230525_20230529.log"
    file = "evcc_20230531.log"
    cp, dp = read_log_file(file)

    xlsx_file_name = 'evcc_log.xlsx'
    if os.path.isfile(xlsx_file_name):
        os.remove(xlsx_file_name)

    workbook = xlsxwriter.Workbook(xlsx_file_name)
    create_format(workbook)
    write_charging_periods(workbook=workbook, charging_periods=cp)
    workbook.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
