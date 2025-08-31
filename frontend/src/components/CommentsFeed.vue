<template>
  <section class="container card">
    <header class="header">
      <h2>Комментарии</h2>
      <div class="toolbar">
        <button class="button" @click="showCreate = true">Написать сообщение</button>
        <button class="button gray" @click="doRefetch">Обновить</button>
        <span class="badge">Всего: {{ total }}</span>
      </div>
    </header>

    <section class="section toolbar">
      <span class="badge">Сортировка:</span>
      <button class="badge" :class="{active: sort.field==='CREATED_AT'}" @click="setSort('CREATED_AT')">
        Дата <small>({{ sort.desc ? '↓' : '↑' }})</small>
      </button>
      <button class="badge" :class="{active: sort.field==='USER_NAME'}" @click="setSort('USER_NAME')">
        User Name <small>({{ sort.desc ? 'Z→A' : 'A→Z' }})</small>
      </button>
      <button class="badge" :class="{active: sort.field==='EMAIL'}" @click="setSort('EMAIL')">
        E-mail <small>({{ sort.desc ? 'Z→A' : 'A→Z' }})</small>
      </button>

      <div style="flex:1"></div>

      <input class="input" v-model.trim="filters.q" placeholder="Имя/E-mail содержит…" @keyup.enter="doRefetch" style="max-width:280px" />
      <button class="button gray" @click="doRefetch">Применить</button>
      <button class="button gray" @click="resetFilters">Сброс</button>
    </section>

    <section v-if="errText" class="section">
      <p class="error">{{ errText }}</p>
    </section>

    <section class="section" v-if="loadingTop">
      Загружаем…
    </section>

    <section class="section" v-else>
      <ul class="list">
        <li v-for="node in filtered" :key="node.id">
          <CommentItem :comment="node" @created="doRefetch" />
        </li>
      </ul>
    </section>

    <footer v-if="pages>1" class="section toolbar" style="justify-content:center">
      <button class="button gray" :disabled="page===1" @click="goto(page-1)">← Назад</button>
      <span class="badge">Стр. {{ page }} / {{ pages }}</span>
      <button class="button gray" :disabled="page===pages" @click="goto(page+1)">Вперёд →</button>
    </footer>

    <Modal v-if="showCreate" @close="showCreate=false">
      <template #title>Новое сообщение</template>
      <CommentForm :parent-id="null" captcha-mode="image" @created="onCreatedAndClose" />
    </Modal>
  </section>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuery } from '@vue/apollo-composable'
import { COMMENTS_QUERY } from '../graphql/operations'
import CommentItem from './CommentItem.vue'
import CommentForm from './CommentForm.vue'
import Modal from './Modal.vue'

const pageSize = 25
const page = ref(1)
const sort = reactive({ field: 'CREATED_AT', desc: true }) // LIFO
const filters = reactive({ q: '' })
const showCreate = ref(false)

const { result, loading: loadingTop, error: gqlErr, refetch } = useQuery(
  COMMENTS_QUERY,
  () => ({
    page: page.value,
    pageSize,
    orderField: sort.field,
    desc: sort.desc,
    parentId: null
  }),
  { fetchPolicy: 'cache-and-network' }
)

const total = computed(() => result.value?.comments?.count ?? 0)
const items = computed(() => result.value?.comments?.results ?? [])

const filtered = computed(() => {
  const q = (filters.q || '').toLowerCase()
  if (!q) return items.value
  return items.value.filter(it => {
    const name = (it.author?.name || '').toLowerCase()
    const email = (it.author?.email || '').toLowerCase()
    return name.includes(q) || email.includes(q)
  })
})

const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function doRefetch(){
  refetch()
}

function goto(p){
  page.value = Math.min(Math.max(1,p), pages.value)
  refetch()
}

function setSort(field){
  if (sort.field === field) {
    sort.desc = !sort.desc
  } else {
    sort.field = field
    sort.desc = (field === 'CREATED_AT')
  }
  page.value = 1
  refetch()
}

function resetFilters(){
  filters.q = ''
  refetch()
}

function onCreatedAndClose(){
  showCreate.value = false
  refetch()
}

const errText = computed(() => gqlErr.value?.message || '')
</script>
