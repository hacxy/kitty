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
from kitty.utils import color_as_int

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
    cells = create_cells()  # list of (text, fg, bg)；fg=0 表示用默认色
    # Drop cells that wont fit
    while True:
        if not cells:
            return
        total_len = sum(len(c[0]) + 3 for c in cells)
        padding = screen.columns - screen.cursor.x - total_len
        if padding >= 0:
            break
        cells = cells[1:]

    if padding:
        screen.draw(" " * padding)

    # 右侧状态整体使用激活 tab 颜色（active_bg/active_fg）
    tab_bg = as_rgb(int(draw_data.active_bg))
    tab_fg = as_rgb(int(draw_data.active_fg))
    default_bg = as_rgb(int(draw_data.default_bg))
    prev_bg = default_bg
    for i, cell in enumerate(cells):
        text, fg, bg = cell
        if fg == 0 and bg == 0:
            fg, bg = tab_fg, tab_bg  # 默认色
        # 镜像左侧 tab：左侧 tab 用 (右半圆/右凸) 让 tab 向右凸；右侧 cell 镜像用 (左半圆/左凸) 让 cell 向左凸
        # 每个 cell 左侧画 ：fg=当前cell色(凸出部分)，bg=右侧邻cell色（起始 cell 右侧是终端背景）
        if i == 0:
            screen.cursor.fg = bg           # 凸出=当前 cell 色（VIM 蓝），朝左（内容区）
            screen.cursor.bg = default_bg   # 右侧露终端背景
        else:
            screen.cursor.fg = bg           # 凸出=当前 cell 色（时间紫）
            screen.cursor.bg = prev_bg      # 右侧邻 cell 色
        screen.draw("")
        # 内容
        screen.cursor.fg = fg
        screen.cursor.bg = bg
        screen.draw(f" {text} ")
        prev_bg = bg


def get_vim_mode_status() -> tuple[str, int, int] | None:
    """返回 (文本, 前景色, 背景色)，均为 as_rgb 编码值；进入 split 模式显示 VIM，否则 None（隐藏）"""
    try:
        mode = get_boss().mappings.current_keyboard_mode_name
        if mode == 'split':
            return ("VIM", as_rgb(color_as_int(0x1E1E2E)), as_rgb(color_as_int(0x89B4FA)))  # 深字 + Mocha 蓝底
    except Exception:
        pass
    return None


def create_cells() -> list[tuple[str, int, int]]:
    now = datetime.datetime.now()
    cells: list[tuple[str, int, int]] = []
    # vim 模式指示：显示在时间左边，进入 split 模式显示，退出隐藏
    vim_mode = get_vim_mode_status()
    if vim_mode:
        cells.append(vim_mode)
    # 时间：fg=0/bg=0 哨兵值，由 draw_right_status 替换为默认 tab 色
    cells.append((now.strftime("%H:%M"), 0, 0))
    return cells

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
