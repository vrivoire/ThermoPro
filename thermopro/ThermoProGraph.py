# start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import ctypes
import math
import sys
import traceback
from collections.abc import Sequence
from datetime import timedelta
from typing import Any

import matplotlib.dates as m_dates
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
from matplotlib.container import BarContainer
from matplotlib.dates import date2num, num2date
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons, Slider, Button

import thermopro
from constants import MIN_HPA, MAX_HPA, DAYS
from thermopro import log, show_df
from thermopro.ThermoProScan import ThermoProScan


class ThermoProGraph:
    df: pd.DataFrame

    def __init__(self):
        log.info('Starting ThermoProGraph')
        global df
        df = ThermoProScan.load_json()
        for col in ['kwh_hydro_quebec', 'ext_temp', 'int_temp', 'open_temp']:
            df[col] = df[col].astype('Float64')
            df[col] = df[col].ffill().fillna(0.0)
        for col in ['ext_humidity', 'open_humidity', 'open_pressure', 'ext_humidex', 'open_feels_like']:
            df[col] = df[col].astype('Int64')
            df[col] = df[col].ffill().fillna(0)
        show_df(df)

    # https://stackoverflow.com/questions/7908636/how-to-add-hovering-annotations-to-a-plot
    def create_graph_temperature(self) -> None:
        try:
            log.info('create_graph_temperature')
            show_df(df)
            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()

            ax1.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax1.grid(axis='y', color='blue', linewidth=0.2)
            ax1.set_yticks(list(range(0, 101, 10)))

            ext_humidity, = ax1.plot(df["time"], df["ext_humidity"], color='xkcd:royal blue', label='Ext. %')
            int_humidity, = ax1.plot(df["time"], df["int_humidity"], color='xkcd:blue', label='Int.. %')
            open_humidity, = ax1.plot(df["time"], df["open_humidity"], color='xkcd:sky blue', label='Open %')
            open_pressure, = ax1.plot(df["time"], (df["open_pressure"] - MIN_HPA) / ((MAX_HPA - MIN_HPA) / 100), color='xkcd:black', label='hPa')

            ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
            ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
            ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
            ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            ax1.tick_params(axis='both', which='minor', labelsize='small')
            plt.xticks(rotation=45, ha='right', fontsize='9')
            plt.gcf().autofmt_xdate()

            ext_humidex, = ax2.plot(df["time"], df["ext_humidex"], color='xkcd:pink', label='Humidex')
            open_feels_like, = ax2.plot(df["time"], df["open_feels_like"], color='xkcd:rose pink', label='Feels like °C')
            ext_temp, = ax2.plot(df["time"], df["ext_temp"], color='xkcd:scarlet', label='Ext. °C')
            int_temp, = ax2.plot(df["time"], df["int_temp"], color='xkcd:red', label='Int. °C')
            open_temp, = ax2.plot(df["time"], df["open_temp"], color='xkcd:brick red', label='Open °C')

            ax2.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax2.grid(axis='y', linewidth=0.2, color='xkcd:scarlet')
            ax2.set_yticks(list(range(int(df['ext_temp'].min(numeric_only=True) - 0.5),
                                      int(max(df['ext_temp'].max(numeric_only=True) + 0.5,
                                              df['ext_humidex'].max(numeric_only=True) + 0.5,
                                              df['int_temp'].max(numeric_only=True) + 0.5,
                                              df['open_temp'].max(numeric_only=True) + 0.5,
                                              df['open_feels_like'].max(numeric_only=True) + 0.5
                                              )))))

            mean_ext_temp, = ax2.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['ext_temp'].mean(), color='xkcd:deep red', alpha=0.3, label='Mean ext °C')
            mean_int_temp, = ax2.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['int_temp'].mean(), color='xkcd:deep rose', alpha=0.3, label='Mean int °C')
            mean_ext_humidity, = ax1.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['ext_humidity'].mean(), color='xkcd:deep blue', alpha=0.3, label='Mean %')
            # https://mplcursors.readthedocs.io/en/stable/index.html
            mplcursors.cursor(open_pressure, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {int(float(sel[1][1]) * float((MAX_HPA - MIN_HPA) / 100.0) + MIN_HPA)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(mean_ext_temp, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(mean_int_temp, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(mean_ext_humidity, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
            ))
            plt.axhline(0, linewidth=0.5, color='black', zorder=-10)

            window = (
                df['time'][0] - timedelta(hours=1),
                df["time"][df["time"].size - 1] + timedelta(hours=1),
                df['ext_temp'].min(numeric_only=True) - 1,
                max(df['ext_temp'].max(numeric_only=True) + 0.5,
                    df['ext_humidex'].max(numeric_only=True) + 0.5,
                    df['int_temp'].max(numeric_only=True) + 0.5,
                    df['open_temp'].max(numeric_only=True) + 0.5,
                    df['open_feels_like'].max(numeric_only=True) + 0.5
                    ))
            plt.axis(window)

            try:
                plt.title(
                    f"Date: {df['time'][len(df['time']) - 1].strftime('%Y/%m/%d %H:%M')}, Int: {df['int_temp'][len(df['int_temp']) - 1]}°C, Ext.: {df['ext_temp'][len(df['ext_temp']) - 1]}°C, " \
                    + f"{int(df['ext_humidity'][len(df['ext_humidity']) - 1])}%, Humidex: {(df['ext_humidex'][len(df['ext_humidex']) - 1])}, " \
                    + f"Open: {df['open_temp'][len(df['open_temp']) - 1]}°C, Open: {int(df['open_humidity'][len(df['open_humidity']) - 1])}%, Open Humidex: {int(df['open_feels_like'][len(df['open_feels_like']) - 1])}, " \
                    + f'Pressure: {int(df['open_pressure'][len(df['open_pressure']) - 1])} hPa, Rolling x̄: {int(DAYS)} days', fontsize=10)
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())

            plt.tight_layout()
            fig.subplots_adjust(
                left=0.055,
                bottom=0.105,
                right=0.952,
                top=0.948,
                wspace=0.198,
                hspace=0.202
            )

            def on_clicked(label):
                line: Line2D | None = None
                for line in all_lines:
                    if line.get_label() == label:
                        break
                line.set_visible(not line.get_visible())
                line.figure.canvas.draw_idle()

                check.eventson = False
                if label == 'All/None':
                    for i in range(len(all_lines)):
                        line2 = all_lines[i]
                        line2.set_visible(line.get_visible())
                        line2.figure.canvas.draw_idle()
                        check.set_active(i, line.get_visible())
                check.eventson = True

            select: Line2D = Line2D([1], [1], label='All/None', color='black')
            select.set_figure(ext_temp.figure)
            select.figure.set_canvas(ext_temp.figure.canvas)

            all_lines: list[Line2D] = [select, open_pressure, int_temp, ext_temp, open_feels_like, open_temp, int_humidity, ext_humidity, open_humidity, ext_humidex, open_feels_like]
            lines_label: Sequence[str] = [str(line.get_label()) for line in all_lines]
            lines_colors: Sequence[str] = [line.get_color() for line in all_lines]
            lines_actives: Sequence[bool] = [line.get_visible() for line in all_lines]
            check = CheckButtons(
                ax=ax1.inset_axes((0.0, 0.0, 0.1, 0.3), zorder=-10),
                labels=lines_label,
                actives=lines_actives,
                label_props={'color': lines_colors},
                frame_props={'edgecolor': lines_colors},
                check_props={'facecolor': lines_colors},
            )
            check.on_clicked(on_clicked)

            def on_changed(val):
                slider_position.valtext.set_text(num2date(val).date())
                df2: pd.DataFrame = df.set_index(['time'])
                df2 = df2[num2date(val - DAYS).date():num2date(val + DAYS).date()]
                window = (
                    val - DAYS,
                    val + 0.1,
                    0,
                    100
                )
                ax1.axis(window)
                ax1.set_yticks(list(range(0, 101, 10)))
                ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m/%d'))
                ax1.xaxis.set_major_locator(m_dates.DayLocator(interval=1))

                window2 = (
                    val - DAYS,
                    val + 0.1,
                    df2['ext_temp'].min(numeric_only=True) - 1,
                    max(
                        df2['ext_temp'].max(numeric_only=True) + 0.5,
                        df2['ext_humidex'].max(numeric_only=True) + 0.5,
                        df2['int_temp'].max(numeric_only=True) + 0.5,
                        df2['open_temp'].max(numeric_only=True) + 0.5,
                        df2['open_feels_like'].max(numeric_only=True) + 0.5
                    ) + 1
                )
                ax2.axis(window2)
                ax2.set_yticks(list(range(int(df2['ext_temp'].min(numeric_only=True) - 1.1),
                                          int(max(
                                              df2['ext_temp'].max(numeric_only=True) + 0.5,
                                              df2['ext_humidex'].max(numeric_only=True) + 0.5,
                                              df2['int_temp'].max(numeric_only=True) + 0.5,
                                              df2['open_temp'].max(numeric_only=True) + 0.5,
                                              df2['open_feels_like'].max(numeric_only=True) + 0.5
                                          ) + 1.1), 1)))

                fig.canvas.draw_idle()

            def reset(event) -> None:
                slider_position.reset()
                ax1.axis((
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    0,
                    100
                ))
                ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
                ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
                ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
                ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))

                ax2.axis((
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    df['ext_temp'].min(numeric_only=True) - 1,
                    max(
                        df['ext_temp'].max(numeric_only=True) + 0.5,
                        df['ext_humidex'].max(numeric_only=True) + 0.5,
                        df['int_temp'].max(numeric_only=True) + 0.5,
                        df['open_temp'].max(numeric_only=True) + 0.5,
                        df['open_feels_like'].max(numeric_only=True) + 0.5
                    ) + 1
                ))
                ax2.set_yticks(list(range(int(df['ext_temp'].min(numeric_only=True) - 1.1),
                                          int(max(
                                              df['ext_temp'].max(numeric_only=True) + 0.5,
                                              df['ext_humidex'].max(numeric_only=True) + 0.5,
                                              df['int_temp'].max(numeric_only=True) + 0.5,
                                              df['open_temp'].max(numeric_only=True) + 0.5,
                                              df['open_feels_like'].max(numeric_only=True) + 0.5
                                          ) + 1.1), 1)))
                fig.canvas.draw_idle()

            slider_position = Slider(
                plt.axes(
                    (0.08, 0.01, 0.73, 0.03),
                    facecolor='White'
                ),
                'Date',
                date2num(df["time"][0]),
                date2num(df['time'][len(df['time']) - 1]),
                valstep=1,
                color='w',
                initcolor='none',
            )
            slider_position.valtext.set_text(df["time"][0].date())
            slider_position.on_changed(on_changed)
            button = Button(fig.add_axes((0.9, 0.01, 0.055, 0.03)), 'Reset', hovercolor='0.975')
            button.on_clicked(reset)
            slider_position.set_val(date2num(df['time'][len(df['time']) - 1]))

            fig.canvas.manager.set_window_title('ThermoPro Temperature')
            mng = plt.get_current_fig_manager()
            mng.window.state('zoomed')
            plt.show()

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            ctypes.windll.user32.MessageBoxW(0, f'{ex}', "ThermoProGraph Error", 16)

    # https://stackoverflow.com/questions/7908636/how-to-add-hovering-annotations-to-a-plot
    # https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2F4b4dsqrkc8251.png%3Fwidth%3D478%26format%3Dpng%26auto%3Dwebp%26s%3Df23f16925ebaae75f60c43756dd9f7214dbffa3b
    def create_graph_energy(self) -> None:
        try:
            log.info('create_graph_energy')
            global df

            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()

            ax1.set_ylabel('KWh', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax1.grid(axis='y', color='gray', linewidth=0.2)
            ax1.set_yticks(list(range(0, math.ceil(df['kwh_hydro_quebec'].max(numeric_only=True)))), minor=True)
            kwh_hydro_quebec, = ax1.plot(df["time"], (df["kwh_hydro_quebec"]), color='xkcd:grey', label='Hydro KWh')
            kwh_neviweb, = ax1.plot(df["time"], (df["kwh_neviweb"]), color='xkcd:gray', label='Nevi KWh')

            ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
            ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
            ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
            ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            ax1.tick_params(axis='both', which='minor', labelsize='small')
            plt.xticks(rotation=45, ha='right', fontsize='9')
            plt.gcf().autofmt_xdate()

            ext_temp, = ax2.plot(df["time"], df["ext_temp"], color='xkcd:scarlet', label='Ext. °C')
            int_temp, = ax2.plot(df["time"], df["int_temp"], color='xkcd:red', label='Int. °C')
            open_temp, = ax2.plot(df["time"], df["open_temp"], color='xkcd:brick red', label='Open °C')

            ax2.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax2.grid(axis='y', linewidth=0.2, color='xkcd:scarlet')

            mean_ext_temp, = ax2.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['ext_temp'].mean(), color='xkcd:deep red', alpha=0.3, label='Mean ext °C')
            mean_int_temp, = ax2.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['int_temp'].mean(), color='xkcd:deep rose', alpha=0.3, label='Mean int °C')
            mean_kwh_hydro_quebec, = ax1.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['kwh_hydro_quebec'].mean(), color='xkcd:medium grey', alpha=0.3, label='Mean Hydo KWh')
            mean_kwh_kwh_neviweb, = ax1.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['kwh_neviweb'].mean(), color='xkcd:medium gray', alpha=0.3, label='Mean Nevi KWh')

            plt.axhline(0, linewidth=0.5, color='black', zorder=-10)

            try:
                plt.title(
                    f"Date: {df['time'][len(df['time']) - 1].strftime('%Y/%m/%d %H:%M')}, Int: {df['int_temp'][len(df['int_temp']) - 1]}°C, Ext.: {df['ext_temp'][len(df['ext_temp']) - 1]}°C, " \
                    + f"Open: {df['open_temp'][len(df['open_temp']) - 1]}°C, Hydro: {df['kwh_hydro_quebec'][df['kwh_hydro_quebec'].last_valid_index()]}KWh, Nevi: {df['kwh_neviweb'][df['kwh_neviweb'].last_valid_index()]}KWh" \
                    + f', Rolling x̄: {int(DAYS)} days', fontsize=10)
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())

            plt.tight_layout()
            fig.subplots_adjust(
                left=0.055,
                bottom=0.105,
                right=0.952,
                top=0.948,
                wspace=0.198,
                hspace=0.202
            )

            def on_clicked(label):
                line: Line2D | None = None
                for line in all_lines:
                    if line.get_label() == label:
                        break
                line.set_visible(not line.get_visible())
                line.figure.canvas.draw_idle()

                check.eventson = False
                if label == 'All/None':
                    for i in range(len(all_lines)):
                        line2 = all_lines[i]
                        line2.set_visible(line.get_visible())
                        line2.figure.canvas.draw_idle()
                        check.set_active(i, line.get_visible())
                check.eventson = True

            select: Line2D = Line2D([1], [1], label='All/None', color='black')
            select.set_figure(ext_temp.figure)
            select.figure.set_canvas(ext_temp.figure.canvas)

            all_lines: list[Line2D | BarContainer] = [select, kwh_hydro_quebec, kwh_neviweb, int_temp, ext_temp, open_temp]
            lines_colors: list[Any] = []
            lines_actives: list[bool] = []
            for line in all_lines:
                if type(line) == BarContainer:
                    lines_colors.append(line[0].get_facecolor())
                    lines_actives.append(line[0].get_visible())
                else:
                    lines_colors.append(line.get_color())
                    lines_actives.append(line.get_visible())
            lines_label: list[str] = [str(line.get_label()) for line in all_lines]
            check = CheckButtons(
                ax=ax1.inset_axes((0.0, 0.0, 0.1, 0.3), zorder=-10),
                labels=lines_label,
                actives=lines_actives,
                label_props={'color': lines_colors},
                frame_props={'edgecolor': lines_colors},
                check_props={'facecolor': lines_colors},
            )
            check.on_clicked(on_clicked)

            def on_changed(val):
                log.info(f'on_changed({num2date(val)}) -> from: {num2date(val - DAYS).date()}, to: {num2date(val + 1).date()}')
                slider_position.valtext.set_text(num2date(val).date())
                df2: pd.DataFrame = df.set_index(['time'])
                df2 = df2[num2date(val - DAYS).date():num2date(val + 1).date()].ffill()
                show_df(df2)

                if len(df2) > 0:
                    window = (
                        val - DAYS,
                        val + 0.1,
                        0,
                        math.ceil(max(df2['kwh_hydro_quebec']) * 10 if len(df2['kwh_hydro_quebec']) > 0 else 0.0) / 10
                    )
                    ax1.axis(window)
                    ax1.set_yticks(
                        list(
                            range(0,
                                  math.ceil(max(df2['kwh_hydro_quebec']) if len(df2['kwh_hydro_quebec']) > 0 else 0.0)
                                  )
                        ), minor=True)
                    ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m/%d'))
                    ax1.xaxis.set_major_locator(m_dates.DayLocator(interval=1))

                    window2 = (
                        val - DAYS,
                        val + 0.1,
                        min(
                            df2['ext_temp'].min(numeric_only=True, skipna=True),
                            df2['int_temp'].min(numeric_only=True, skipna=True),
                            df2['open_temp'].min(numeric_only=True, skipna=True)
                        ) - 2.0,
                        max(
                            df2['ext_temp'].max(numeric_only=True, skipna=True),
                            df2['int_temp'].max(numeric_only=True, skipna=True),
                            df2['open_temp'].max(numeric_only=True, skipna=True),
                        ) + 2.0
                    )
                    ax2.axis(window2)
                    ax2.set_yticks(list(range(
                        int(min(
                            df2['ext_temp'].min(numeric_only=True, skipna=True),
                            df2['int_temp'].min(numeric_only=True, skipna=True),
                            df2['open_temp'].min(numeric_only=True, skipna=True)
                        ) - 2),
                        int(max(
                            df2['ext_temp'].max(numeric_only=True, skipna=True),
                            df2['int_temp'].max(numeric_only=True, skipna=True),
                            df2['open_temp'].max(numeric_only=True, skipna=True),
                        ) + 2),
                        1)),
                        minor=True)

                    fig.canvas.draw_idle()

            def reset(val) -> None:
                log.info(f'reset({val}) -> from: {df['time'][0] - timedelta(hours=1)}, to: {df["time"][df["time"].size - 1] + timedelta(hours=1)}')
                slider_position.reset()
                show_df(df)
                ax1.axis((
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    0,
                    math.ceil(df['kwh_hydro_quebec'].max(numeric_only=True, skipna=True))
                ))
                ax1.set_yticks(
                    list(
                        range(0, math.ceil(df['kwh_hydro_quebec'].max(numeric_only=True, skipna=True)))),
                    minor=True)
                ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
                ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
                ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
                ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))

                window = (
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    min(
                        df['ext_temp'].min(numeric_only=True, skipna=True),
                        df['int_temp'].min(numeric_only=True, skipna=True),
                        df['open_temp'].min(numeric_only=True, skipna=True)
                    ) - 2.0,
                    max(
                        df['ext_temp'].max(numeric_only=True, skipna=True),
                        df['int_temp'].max(numeric_only=True, skipna=True),
                        df['open_temp'].max(numeric_only=True, skipna=True),
                    ) + 2.0
                )
                ax2.axis(window)
                ax2.set_yticks(list(range(
                    int(min(
                        df['ext_temp'].min(numeric_only=True, skipna=True),
                        df['int_temp'].min(numeric_only=True, skipna=True),
                        df['open_temp'].min(numeric_only=True, skipna=True)
                    ) - 2),
                    int(max(
                        df['ext_temp'].max(numeric_only=True, skipna=True),
                        df['int_temp'].max(numeric_only=True, skipna=True),
                        df['open_temp'].max(numeric_only=True, skipna=True),
                    ) + 2),
                    1)),
                    minor=True)
                fig.canvas.draw_idle()

            slider_position = Slider(
                plt.axes(
                    (0.08, 0.01, 0.73, 0.03),
                    facecolor='White'
                ),
                'Date',
                date2num(df["time"][0]),
                date2num(df['time'][len(df['time']) - 1]),
                valstep=1,
                color='w',
                initcolor='none',
            )
            slider_position.valtext.set_text(df["time"][0].date())
            slider_position.on_changed(on_changed)
            button = Button(fig.add_axes((0.9, 0.01, 0.055, 0.03)), 'Reset', hovercolor='0.975')
            button.on_clicked(reset)
            slider_position.set_val(date2num(df['time'][len(df['time']) - 1]))

            mplcursors.cursor(mean_ext_temp, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(mean_int_temp, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(kwh_hydro_quebec, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}: {round(float(sel[1][1]), 3)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(mean_kwh_hydro_quebec, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}: {round(float(sel[1][1]), 3)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(mean_kwh_kwh_neviweb, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}: {round(float(sel[1][1]), 3)} {sel[0].get_label()}'
            ))

            fig.canvas.manager.set_window_title('ThermoPro Energy')
            mng = plt.get_current_fig_manager()
            mng.window.state('zoomed')
            plt.show()

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            ctypes.windll.user32.MessageBoxW(0, f'{ex}', "ThermoProGraph Error", 16)


if __name__ == '__main__':
    thermopro.set_up(__file__)
    thermoProGraph: ThermoProGraph = ThermoProGraph()
    thermoProGraph.create_graph_temperature()
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        log.info(f"The command line argument is: {arg}")
        if arg == 'temperature':
            thermoProGraph.create_graph_temperature()
        elif arg == 'energy':
            thermoProGraph.create_graph_energy()
        else:
            log.error(f'The argument "{arg}" is invalid')
    else:
        log.info("No command line arguments provided.")
        thermoProGraph.create_graph_temperature()

    log.info('exit')
    sys.exit()
