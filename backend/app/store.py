"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from typing import Any

from app.seed import SEED_ROWS

# 工区清单：示例数据没有真实的工区字段，未标注的记录按确定规则轮流落位，
# 保证每条记录只归属于一个工区，各工区合计与全平台汇总严格一致。
WORK_AREAS = ["信号一工区", "信号二工区", "信号三工区"]

MODULE_TITLES = {
    "section": "线路区段",
    "signal": "信号机",
    "switch": "转辙机",
    "track": "轨道电路",
    "interlock": "联锁设备",
    "atp": "列车防护",
    "plan": "检修计划",
    "task": "检修任务",
    "fault": "故障登记",
    "dispose": "故障处置",
    "spare": "器材领用",
    "measure": "电气测试",
    "patrol": "巡视检查",
    "window": "天窗作业",
    "alarm": "监测报警",
    "verify": "验收确认",
    "shift": "值班交接",
    "assess": "状态评估",
}

# 不属于业务字段的键：生成待办清单标题时跳过这些键，取第一个业务字段的值。
META_KEYS = {"id", "status", "pending", "abnormal", "work_area"}


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self) -> dict[str, object]:
        modules: list[dict[str, object]] = []
        for name in self.module_names():
            rows = self.rows(name)
            modules.append({
                "name": name,
                "created": len(rows),
                "pending": sum(1 for row in rows if row.get("pending")),
                "abnormal": sum(1 for row in rows if row.get("abnormal")),
            })
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}

    def row_area(self, module_index: int, row_index: int, row: dict[str, Any]) -> str:
        """确定一条记录归属的工区：记录自带 work_area 时以记录为准，
        否则按模块序号与记录序号轮流落位，规则固定，多次请求结果一致。"""
        explicit = str(row.get("work_area") or "").strip()
        if explicit:
            return explicit
        return WORK_AREAS[(module_index + row_index) % len(WORK_AREAS)]

    def todo_label(self, row: dict[str, Any]) -> str:
        """待办清单的展示标题：取第一个业务字段（通常是编号），与各模块列表首列一致。"""
        for key, value in row.items():
            if key not in META_KEYS and value not in (None, ""):
                return str(value)
        return f"记录#{row.get('id', '?')}"

    def section_overview(self) -> dict[str, object]:
        """工区分区看板：把全部记录按工区重新归集今日新增、待处理、异常量，
        并给出每个工区下各模块的待办清单。统计口径与 overview() 完全相同，
        每条记录只进一个工区，因此各工区合计恒等于全平台汇总。"""
        modules = self.module_names()
        # 先按 工区 -> 模块 归集，再统一展开，保证每个工区都列出全部模块。
        grid: dict[str, dict[str, dict[str, Any]]] = {}
        for module_index, module in enumerate(modules):
            for row_index, row in enumerate(self.rows(module)):
                area_name = self.row_area(module_index, row_index, row)
                bucket = grid.setdefault(area_name, {}).setdefault(
                    module, {"created": 0, "pending": 0, "abnormal": 0, "todos": []}
                )
                bucket["created"] += 1
                if row.get("pending"):
                    bucket["pending"] += 1
                    bucket["todos"].append({
                        "id": row.get("id"),
                        "label": self.todo_label(row),
                        "status": str(row.get("status") or ""),
                        "abnormal": bool(row.get("abnormal")),
                    })
                if row.get("abnormal"):
                    bucket["abnormal"] += 1
        area_names = list(WORK_AREAS) + sorted(name for name in grid if name not in WORK_AREAS)
        areas: list[dict[str, object]] = []
        for area_name in area_names:
            by_module = grid.get(area_name, {})
            module_entries: list[dict[str, object]] = []
            for module in modules:
                bucket = by_module.get(module) or {"created": 0, "pending": 0, "abnormal": 0, "todos": []}
                module_entries.append({
                    "module": module,
                    "name": MODULE_TITLES.get(module, module),
                    "created": bucket["created"],
                    "pending": bucket["pending"],
                    "abnormal": bucket["abnormal"],
                    "todos": bucket["todos"],
                })
            areas.append({
                "name": area_name,
                "created": sum(int(item["created"]) for item in module_entries),
                "pending": sum(int(item["pending"]) for item in module_entries),
                "abnormal": sum(int(item["abnormal"]) for item in module_entries),
                "modules": module_entries,
            })
        return {"areas": areas}


store = Store()
