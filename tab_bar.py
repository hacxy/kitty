import datetime
import json
import subprocess
from collections import defaultdict

from kitty.boss import get_boss
from kitty.fast_data_types import Screen, add_timer, remove_timer
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    Formatter,
    TabBarData,
    as_rgb,
    draw_attributed_string,
    draw_tab_with_powerline,
)

timer_id = None


def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    global timer_id

    # 启动定时刷新（仅一次）：每 2 秒重绘 tab bar，保证右侧时间/电池实时更新
    if timer_id is None:
        timer_id = add_timer(_redraw_tab_bar, 2.0, True)

    draw_tab_with_powerline(
        draw_data, screen, tab, before, max_title_length, index, is_last, extra_data
    )
    if is_last:
        draw_right_status(draw_data, screen)
    return screen.cursor.x


def _cleanup_timer() -> None:
    # 脚本重载时清理旧 timer，避免泄漏
    global timer_id
    if timer_id is not None:
        try:
            remove_timer(timer_id)
        except Exception as e:
            # timer 可能已被 kitty 自动移除，忽略即可
            print(f'kitty tab bar: timer cleanup skipped: {e}')
        timer_id = None


# 重载时清理（kitty 重新加载 tab_bar.py 时执行）
_cleanup_timer()


def draw_right_status(draw_data: DrawData, screen: Screen) -> None:
    # The tabs may have left some formats enabled. Disable them now.
    draw_attributed_string(Formatter.reset, screen)
    cells = create_cells()
    # Drop cells that wont fit
    while True:
        if not cells:
            return
        padding = screen.columns - screen.cursor.x - sum(len(c) + 3 for c in cells)
        if padding >= 0:
            break
        cells = cells[1:]

    if padding:
        screen.draw(" " * padding)

    tab_bg = as_rgb(int(draw_data.inactive_bg))
    tab_fg = as_rgb(int(draw_data.inactive_fg))
    default_bg = as_rgb(int(draw_data.default_bg))
    for cell in cells:
        # Draw the separator
        if cell == cells[0]:
            screen.cursor.fg = tab_bg
            screen.draw("")
        else:
            screen.cursor.fg = default_bg
            screen.cursor.bg = tab_bg
            screen.draw("")
        screen.cursor.fg = tab_fg
        screen.cursor.bg = tab_bg
        screen.draw(f" {cell} ")


def create_cells() -> list[str]:
    now = datetime.datetime.now()
    # 只显示时间
    return [
        now.strftime("%H:%M"),
    ]

def get_laptop_battery_status():
    try:
        output = subprocess.getoutput("acpi -b")
        if not output:
            return ""
        parts = output.split(", ")
        if len(parts) >= 2:
            percentage = parts[1].strip()
            return f" {percentage}"
    except Exception:
        pass
    return ""




def _redraw_tab_bar(timer_id):
    for tm in get_boss().all_tab_managers:
        tm.mark_tab_bar_dirty()
