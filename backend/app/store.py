"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from typing import Any

from app.seed import SEED_ROWS

# 工区看板口径：平台固定三个工区；没有归属的记录统一落到「未分配工区」，
# 保证各工区数字加起来始终等于 overview() 的全平台总量。
WORK_AREAS = ["城东工区", "城西工区", "城南工区"]
UNASSIGNED_AREA = "未分配工区"

MODULE_LABELS = {
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

# 待办清单里每条记录用哪个字段做标题：取各模块的单号/编号列。
TITLE_FIELDS = {
    "section": "区段编码",
    "signal": "设备编号",
    "switch": "设备编号",
    "track": "设备编号",
    "interlock": "设备编号",
    "atp": "设备编号",
    "plan": "计划编号",
    "task": "任务编号",
    "fault": "故障编号",
    "dispose": "处置单号",
    "spare": "领用单号",
    "measure": "测试单号",
    "patrol": "巡视单号",
    "window": "天窗编号",
    "alarm": "报警编号",
    "verify": "验收单号",
    "shift": "交接编号",
    "assess": "评估编号",
}


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

    def section_overview(self) -> dict[str, object]:
        """工区分区看板：按工区归集今日新增、待处理、异常量，并列出各模块待办。

        与 overview() 共用同一份数据、同一套 pending/abnormal 口径，各工区数字
        相加必然等于全平台总量；没有工区归属的记录归入「未分配工区」。
        """
        areas: dict[str, dict[str, Any]] = {}

        def bucket(area: str) -> dict[str, Any]:
            return areas.setdefault(area, {"created": 0, "pending": 0, "abnormal": 0, "modules": {}})

        for name in self.module_names():
            for row in self.rows(name):
                area_name = str(row.get("work_area") or UNASSIGNED_AREA)
                area = bucket(area_name)
                area["created"] += 1
                module = area["modules"].setdefault(name, {"created": 0, "pending": 0, "abnormal": 0, "todos": []})
                module["created"] += 1
                if row.get("pending"):
                    area["pending"] += 1
                    module["pending"] += 1
                    module["todos"].append({
                        "id": row.get("id"),
                        "title": row.get(TITLE_FIELDS.get(name, "")) or f"记录{row.get('id')}",
                        "status": row.get("status") or "—",
                        "abnormal": bool(row.get("abnormal")),
                    })
                if row.get("abnormal"):
                    area["abnormal"] += 1
                    module["abnormal"] += 1

        # 固定工区排在前面（即使没有记录也占位），其余归属（如未分配）按名称追加。
        ordered_names = WORK_AREAS + sorted(name for name in areas if name not in WORK_AREAS)
        sections: list[dict[str, object]] = []
        for area_name in ordered_names:
            area = areas.get(area_name, {"created": 0, "pending": 0, "abnormal": 0, "modules": {}})
            modules = []
            for name in self.module_names():
                module = area["modules"].get(name, {"created": 0, "pending": 0, "abnormal": 0, "todos": []})
                module["todos"].sort(key=lambda todo: int(todo["id"] or 0))
                modules.append({
                    "name": name,
                    "label": MODULE_LABELS.get(name, name),
                    "created": module["created"],
                    "pending": module["pending"],
                    "abnormal": module["abnormal"],
                    "todos": module["todos"],
                })
            sections.append({
                "name": area_name,
                "created": area["created"],
                "pending": area["pending"],
                "abnormal": area["abnormal"],
                "modules": modules,
            })
        return {"sections": sections}


store = Store()
