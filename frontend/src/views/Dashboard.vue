<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>

    <section class="area-board">
      <header class="page-head">
        <div>
          <h3 class="area-board-title">工区分区看板</h3>
          <p class="page-desc">按工区重新排列今日新增、待处理与异常量，点击工区查看它下面各模块的待办清单。</p>
        </div>
      </header>
      <p v-if="boardMessage" class="board-placeholder">{{ boardMessage }}</p>
      <template v-else>
        <table class="data-table area-table">
          <thead>
            <tr><th>工区</th><th>今日新增</th><th>待处理</th><th>异常量</th><th>待办清单</th></tr>
          </thead>
          <tbody>
            <tr
              v-for="area in areas"
              :key="area.name"
              class="area-row"
              :class="{ 'area-active': area.name === selectedArea }"
              @click="selectArea(area.name)"
            >
              <td>{{ area.name }}</td>
              <td>{{ area.created }}</td>
              <td>{{ area.pending }}</td>
              <td>{{ area.abnormal }}</td>
              <td>
                <button class="link" type="button" @click.stop="selectArea(area.name)">
                  {{ area.name === selectedArea ? '当前工区' : '查看清单' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="currentArea" class="area-detail">
          <h4 class="area-detail-title">{{ currentArea.name }} · 各模块待办清单</h4>
          <div class="area-modules">
            <section v-for="mod in currentArea.modules" :key="mod.module" class="area-module">
              <header class="area-module-head">
                <RouterLink class="area-module-title" :to="`/${mod.module}`">{{ mod.name }}</RouterLink>
                <span class="area-module-stats">新增 {{ mod.created }} · 待办 {{ mod.pending }} · 异常 {{ mod.abnormal }}</span>
              </header>
              <ul v-if="mod.todos.length" class="todo-list">
                <li v-for="todo in mod.todos" :key="todo.id">
                  <span class="todo-label">{{ todo.label }}</span>
                  <span class="todo-status">{{ todo.status || '待处理' }}</span>
                  <span v-if="todo.abnormal" class="todo-tag">异常</span>
                </li>
              </ul>
              <p v-else class="todo-empty">该工区在此模块暂无待办</p>
            </section>
          </div>
        </div>
      </template>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

type AreaTodo = { id: number; label: string; status: string; abnormal: boolean }
type AreaModule = { module: string; name: string; created: number; pending: number; abnormal: number; todos: AreaTodo[] }
type AreaSummary = { name: string; created: number; pending: number; abnormal: number; modules: AreaModule[] }

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

// 看板上选中的工区写进 localStorage：切去别的页面再回来、刷新浏览器都还在。
const AREA_STORAGE_KEY = 'dashboard.selectedArea'
const areas = ref<AreaSummary[]>([])
const selectedArea = ref('')
const boardMessage = ref('工区看板数据加载中…')

const currentArea = computed(() => areas.value.find((area) => area.name === selectedArea.value) ?? null)

function readStoredArea(): string {
  try {
    return localStorage.getItem(AREA_STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

function selectArea(name: string) {
  selectedArea.value = name
  try {
    localStorage.setItem(AREA_STORAGE_KEY, name)
  } catch {
    // 隐私模式等场景写不进去时，仅本次会话内记住选择
  }
}

async function loadAreaBoard() {
  try {
    const payload = await fetchJson<{ areas: AreaSummary[] }>('/api/overview/sections')
    areas.value = payload.areas ?? []
    if (!areas.value.length) {
      boardMessage.value = '后端还没有任何工区数据，可先在各业务模块登记记录后再来查看'
      return
    }
    boardMessage.value = ''
    const stored = readStoredArea()
    const fallback = areas.value[0].name
    const target = areas.value.some((area) => area.name === stored) ? stored : fallback
    selectArea(target)
  } catch {
    // 取不到数据时给出占位说明，不把看板显示成全零
    areas.value = []
    boardMessage.value = '工区看板数据暂时取不到，请确认后端服务已启动后刷新重试'
  }
}

onMounted(async () => {
  void loadAreaBoard()
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "线路区段", "created": 0, "pending": 0, "abnormal": 0}, {"name": "信号机", "created": 0, "pending": 0, "abnormal": 0}, {"name": "转辙机", "created": 0, "pending": 0, "abnormal": 0}, {"name": "轨道电路", "created": 0, "pending": 0, "abnormal": 0}, {"name": "联锁设备", "created": 0, "pending": 0, "abnormal": 0}, {"name": "列车防护", "created": 0, "pending": 0, "abnormal": 0}, {"name": "检修计划", "created": 0, "pending": 0, "abnormal": 0}, {"name": "检修任务", "created": 0, "pending": 0, "abnormal": 0}, {"name": "故障登记", "created": 0, "pending": 0, "abnormal": 0}, {"name": "故障处置", "created": 0, "pending": 0, "abnormal": 0}, {"name": "器材领用", "created": 0, "pending": 0, "abnormal": 0}, {"name": "电气测试", "created": 0, "pending": 0, "abnormal": 0}, {"name": "巡视检查", "created": 0, "pending": 0, "abnormal": 0}, {"name": "天窗作业", "created": 0, "pending": 0, "abnormal": 0}, {"name": "监测报警", "created": 0, "pending": 0, "abnormal": 0}, {"name": "验收确认", "created": 0, "pending": 0, "abnormal": 0}, {"name": "值班交接", "created": 0, "pending": 0, "abnormal": 0}, {"name": "状态评估", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
