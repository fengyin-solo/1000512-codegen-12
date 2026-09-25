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
          <h2>工区分区看板</h2>
          <p class="page-desc">按工区归集今日新增、待处理与异常量，点击工区查看其下各模块的待办清单。</p>
        </div>
      </header>
      <p v-if="areaState === 'loading'" class="board-placeholder">工区看板数据加载中…</p>
      <p v-else-if="areaState === 'error'" class="board-placeholder">
        工区看板数据暂时不可用，请确认后端服务已启动后刷新重试。
      </p>
      <p v-else-if="!areas.length" class="board-placeholder">暂无工区数据，请先在各业务模块登记记录。</p>
      <template v-else>
        <div class="area-row">
          <button
            v-for="area in areas"
            :key="area.name"
            type="button"
            class="area-card"
            :class="{ active: area.name === selectedArea }"
            @click="selectArea(area.name)"
          >
            <span class="area-name">{{ area.name }}</span>
            <span class="area-stats">今日新增 {{ area.created }} · 待处理 {{ area.pending }} · 异常 {{ area.abnormal }}</span>
          </button>
        </div>
        <div v-if="currentArea" class="area-detail">
          <h3 class="area-detail-title">{{ currentArea.name }} · 各模块待办清单</h3>
          <p v-if="!currentArea.pending" class="board-placeholder">该工区当前没有待办事项。</p>
          <div v-else class="module-grid">
            <article v-for="mod in currentArea.modules" :key="mod.name" class="module-card">
              <header class="module-card-head">
                <RouterLink :to="`/${mod.name}`" class="module-link">{{ mod.label }}</RouterLink>
                <span class="module-count">待处理 {{ mod.pending }}</span>
              </header>
              <ul v-if="mod.todos.length" class="todo-list">
                <li v-for="todo in mod.todos" :key="todo.id ?? todo.title">
                  <span class="todo-title">{{ todo.title }}</span>
                  <span class="todo-status">{{ todo.status }}</span>
                  <span v-if="todo.abnormal" class="todo-abnormal">异常</span>
                </li>
              </ul>
              <p v-else class="empty-state">暂无待办</p>
            </article>
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

type AreaTodo = { id: number | null; title: string; status: string; abnormal: boolean }
type AreaModule = {
  name: string
  label: string
  created: number
  pending: number
  abnormal: number
  todos: AreaTodo[]
}
type AreaSection = {
  name: string
  created: number
  pending: number
  abnormal: number
  modules: AreaModule[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

const AREA_STORAGE_KEY = 'dashboard.selectedWorkArea'

const areas = ref<AreaSection[]>([])
const areaState = ref<'loading' | 'ready' | 'error'>('loading')
const selectedArea = ref(localStorage.getItem(AREA_STORAGE_KEY) ?? '')

const currentArea = computed(() => areas.value.find((area) => area.name === selectedArea.value) ?? null)

function selectArea(name: string) {
  selectedArea.value = name
  localStorage.setItem(AREA_STORAGE_KEY, name)
}

async function loadAreas() {
  areaState.value = 'loading'
  try {
    const payload = await fetchJson<{ sections: AreaSection[] }>('/api/overview/sections')
    areas.value = payload.sections
    areaState.value = 'ready'
    if (!payload.sections.some((area) => area.name === selectedArea.value)) {
      selectArea(payload.sections[0]?.name ?? '')
    }
  } catch {
    areas.value = []
    areaState.value = 'error'
  }
}

onMounted(async () => {
  void loadAreas()
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
