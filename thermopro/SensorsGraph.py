import traceback
from collections.abc import Sequence
from datetime import timedelta

import matplotlib

matplotlib.use('TkAgg')
import matplotlib.dates as m_dates
import mplcursors
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons

import thermopro
from thermopro import log


class SensorsGraph:
    df: pd.DataFrame | None = None

    def __init__(self):
        log.info('Starting ThermoProGraph')
        thermopro.sensors = None
        global df
        df = thermopro.load_sensors()

    def create_graph_sensors(self):
        try:
            thermopro.show_df(df, title='create_graph_sensors')

            fig, ax1 = plt.subplots()

            plt.xticks(rotation=45, ha='right', fontsize='9')
            plt.gcf().autofmt_xdate()
            plt.axhline(0, linewidth=0.5, color='black', zorder=-10)

            ax1.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax1.grid(axis='y', color='blue', linewidth=0.2)
            ax1.set_yticks(list(range(0, 101, 10)))
            ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
            ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
            ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
            ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            ax1.tick_params(axis='both', which='minor', labelsize='small')

            ax2 = ax1.twinx()
            ax2.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax2.grid(axis='y', linewidth=0.2, color='xkcd:scarlet')

            mi: float = 0.0
            ma: float = 0.0
            humidity_list: list[Line2D] = []
            temp_list: list[Line2D] = []
            for col in sorted(df.columns):
                name: str = col.rsplit('_', 1)[-1]
                pos: str = col.split('_')[0]
                if col != 'time':
                    if '_humidity_' in col and pd.isna(df[col].min()) == False:
                        line, = ax1.plot(df["time"], df[col], color='xkcd:royal blue', label=f'% {pos} {name}')
                        humidity_list.append(line)
                    if '_temp_' in col and pd.isna(df[col].min()) == False:
                        mi = min(df[col].min(), mi) if not pd.isna(df[col].min()) else mi
                        ma = max(df[col].max(), mi) if not pd.isna(df[col].max()) else ma
                        line, = ax2.plot(df["time"], df[col], color='xkcd:scarlet', label=f'°C {pos} {name}')
                        temp_list.append(line)

            for line in humidity_list:
                mplcursors.cursor(line, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                    f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
                ))
            for line in temp_list:
                mplcursors.cursor(line, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                    f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {round(float(sel[1][1]), 2)} {sel[0].get_label()}'
                ))

            def on_check_clicked(label):
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
            select.set_figure(temp_list[0].figure)
            select.figure.set_canvas(temp_list[0].figure.canvas)

            all_lines: list[Line2D] = [select] + temp_list + humidity_list
            lines_label: Sequence[str] = [str(line.get_label()) for line in all_lines]
            lines_colors: Sequence[str] = [line.get_color() for line in all_lines]
            lines_actives: Sequence[bool] = [line.get_visible() for line in all_lines]
            check: CheckButtons = CheckButtons(
                ax=ax1.inset_axes((0.0, 0.0, 0.14, 0.3), zorder=-10),
                labels=lines_label,
                actives=lines_actives,
                label_props={'color': lines_colors},
                frame_props={'edgecolor': lines_colors},
                check_props={'facecolor': lines_colors},
            )
            check.on_clicked(on_check_clicked)

            ax2.axis((
                df['time'][0] - timedelta(hours=1),
                df["time"][df["time"].size - 1] + timedelta(hours=1),
                mi - 1,
                ma + 1
            ))
            ax2.set_yticks(list(range(
                int(mi - 1),
                int(ma + 1),
                1)))

            plt.tight_layout()
            fig.subplots_adjust(
                left=0.055,
                bottom=0.105,
                right=0.952,
                top=0.948,
                wspace=0.198,
                hspace=0.202
            )
            fig.canvas.manager.set_window_title('ThermoPro Energy')
            mng = plt.get_current_fig_manager()
            mng.window.state('zoomed')
            plt.show()
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())


if __name__ == '__main__':
    print(matplotlib.get_backend())
    thermopro.set_up(__file__)
    thermoProGraph: SensorsGraph = SensorsGraph()
    thermoProGraph.create_graph_sensors()
