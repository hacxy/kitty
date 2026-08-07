# AGENTS.md

- 在编写kitty配置之前, 永远先参考kitty的官方配置文档: <https://sw.kovidgoyal.net/kitty/conf/>
- 快捷键相关配置（映射、解除绑定、键盘模式等）参考:
  - <https://sw.kovidgoyal.net/kitty/conf/> 的 "Making your keyboard dance" 一节（含 unmap / discard_event / clear_all_shortcuts 等移除快捷键的方式）
  - <https://sw.kovidgoyal.net/kitty/actions/> （完整 action 列表，如 no_op / goto_tab / previous_tab / next_tab）
- 永远不要尝试查看 kitty 源码（Python/Cython 源码、GitHub 仓库源码等）来推断行为
- 如果官方配置文档无法满足用户需求，去 GitHub issue（<https://github.com/kovidgoyal/kitty/issues>）或其他论坛（如 Reddit、Stack Overflow）搜索/寻找解决方案，而不是去读源码
- 配置快捷键永远使用vim风格的快捷，如果用户只提出需求，没有给出具体快捷键映射，则主动向用户询问
