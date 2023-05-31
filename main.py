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


def write_charging_periods(workbook: xlsxwriter.Workbook, charging_periods=None, target: str = None):
    if charging_periods is None:
        charging_periods = {}
    for lp_name, cps in charging_periods.items():
        if not target or target == lp_name:
            worksheet = add_worksheet(workbook=workbook, worksheet_name=lp_name,
                                      header_list=[ExcelTableHeader(position=0, label="start", width=30),
                                                   ExcelTableHeader(position=1, label="stop", width=30)])
            format_table_date = workbook.add_format({"num_format": "dd.mm.yyyy hh:mm:ss",
                                                     "align": "left"})
            for idx, cp in enumerate(cps):
                worksheet.write_datetime(idx + 1, 0, cp.start, format_table_date)
                if cp.stop:
                    worksheet.write_datetime(idx + 1, 1, cp.stop, format_table_date)


def write_data_points(workbook: xlsxwriter.Workbook, data_points, name: str, value_unit: str, target: str = None):
    points_to_write = [dp for dp in data_points if dp.name == name and (
            target is None or dp.target == target)]
    worksheet = add_worksheet(workbook=workbook, worksheet_name=name[:30],
                              header_list=[ExcelTableHeader(position=0, label="timestamp", width=30),
                                           ExcelTableHeader(position=1, label="power", width=10)])
    format_table_date = workbook.add_format({"num_format": "dd.mm.yyyy hh:mm:ss",
                                             "align": "left"})
    for idx, dp in enumerate(points_to_write):
        worksheet.write_datetime(idx + 1, 0, dp.timestamp, format_table_date)
        worksheet.write_number(idx + 1, 1, int(dp.value.replace(value_unit, '')), format_table_cell)


def write_all_data_points(workbook: xlsxwriter.Workbook, data_points, names, value_unit: str, target: str = None):
    points_to_write = [dp for dp in data_points if dp.name in names and (
            target is None or dp.target == target)]

    points_by_time = {}
    last_ts = None
    for dp in points_to_write:
        if last_ts is None:
            last_ts = dp.timestamp

        if dp.timestamp not in points_by_time:
            points_by_time[dp.timestamp] = [dp]
            last_ts = dp.timestamp

        if last_ts == dp.timestamp and dp not in points_by_time[dp.timestamp]:
            points_by_time[dp.timestamp] += [dp]

    header_list = [ExcelTableHeader(position=0, label="timestamp", width=30)]
    for idx, n in enumerate(names):
        header_list += [ExcelTableHeader(position=idx + 1, label=n, width=10)]
    worksheet = add_worksheet(workbook=workbook, worksheet_name="all",
                              header_list=header_list)
    format_table_date = workbook.add_format({"num_format": "dd.mm.yyyy hh:mm:ss",
                                             "align": "left"})
    for key, dps in points_by_time.items():
        idx = list(points_by_time.keys()).index(key)
        worksheet.write_datetime(idx + 1, 0, key, format_table_date)
        for dp in dps:
            worksheet.write_number(idx + 1, names.index(dp.name) + 1, int(dp.value.replace(value_unit, '')), format_table_cell)


def main():
    # file = "evcc_20230525_20230529.log"
    file = "evcc_20230531.log"
    cp, dps = read_log_file(file)

    xlsx_file_name = 'evcc_log.xlsx'
    if os.path.isfile(xlsx_file_name):
        os.remove(xlsx_file_name)

    workbook = xlsxwriter.Workbook(xlsx_file_name)
    create_format(workbook)
    write_charging_periods(workbook=workbook, charging_periods=cp, target="lp-1")
    write_data_points(workbook=workbook, data_points=dps, name="charge power", value_unit="W", target="lp-1")
    write_data_points(workbook=workbook, data_points=dps, name="pv power", value_unit="W")
    write_data_points(workbook=workbook, data_points=dps, name="grid power", value_unit="W")
    write_data_points(workbook=workbook, data_points=dps, name="site power", value_unit="W")
    write_data_points(workbook=workbook, data_points=dps, name="battery power", value_unit="W")
    write_all_data_points(workbook=workbook, data_points=[dp for dp in dps if dp.target != "lp-2"],
                          names=["charge power", "pv power", "grid power", "site power", "battery power"],
                          value_unit="W")
    workbook.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
