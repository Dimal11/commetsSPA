<template>
  <article class="comment">
    <div class="avatar">{{ initials }}</div>
    <div class="body">
      <div class="meta">
        <strong>{{ comment.author?.name || 'Anon' }}</strong>
        <span class="time">· {{ humanDate }}</span>
        <a v-if="comment.author?.email" class="hint" :href="`mailto:${comment.author.email}`">{{ comment.author.email }}</a>
      </div>

      <div class="text" v-html="safeHtml(comment.textHtml || '')"></div>

      <div v-if="images.length || docs.length" class="attachments">
        <img v-for="a in images" :key="a.id" :src="absUrl(a.url)" class="thumb" :alt="a.name || 'image'" @click="openLightbox(a)" />
        <a v-for="a in docs" :key="a.id" :href="absUrl(a.url)" target="_blank" rel="noopener" class="file-chip">{{ a.name || 'file.txt' }}</a>
      </div>

      <div class="actions">
        <button class="button gray" @click="replyOpen = !replyOpen">{{ replyOpen ? 'Отмена' : 'Ответить' }}</button>
        <button class="button ghost" @click="toggleReplies">
          {{ showReplies ? 'Скрыть ответы' : `Показать ответы (${comment.repliesCount || 0})` }}
        </button>
      </div>

      <div v-if="replyOpen" class="section">
        <CommentForm :parent-id="comment.id" captcha-mode="image" @created="onReplied" />
      </div>

      <ul v-if="showReplies" class="replies">
        <li v-for="r in replies" :key="r.id">
          <CommentItem :comment="r" @created="$emit('created')" />
        </li>
        <li v-if="repliesLoading" class="hint">Загрузка ответов…</li>
        <li v-if="repliesError" class="error">{{ repliesError }}</li>
      </ul>
    </div>

    <div v-if="lightbox" class="lightbox" @click.self="lightbox=null">
      <img :src="lightbox.url" />
      <button class="button" style="position:absolute;top:20px;right:20px" @click="lightbox=null">Закрыть</button>
    </div>
  </article>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuery } from '@vue/apollo-composable'
import { COMMENTS_QUERY } from '../graphql/operations'
import CommentForm from './CommentForm.vue'
import { absUrl } from '../paths'

const props = defineProps({ comment: { type: Object, required: true } })
const emit = defineEmits(['created'])

const replyOpen = ref(false)
const showReplies = ref(false)
const lightbox = ref(null)

const initials = computed(() => (props.comment.author?.name || '?').slice(0,2).toUpperCase())
const humanDate = computed(() => new Date(props.comment.createdAt).toLocaleString())

const attachments = computed(() => Array.isArray(props.comment.attachments) ? props.comment.attachments : [])
const images = computed(() => attachments.value.filter(a => a.isImage || /^image\//.test(a.contentType || '')))
const docs   = computed(() => attachments.value.filter(a => !a.isImage && !/^image\//.test(a.contentType || '')))

function openLightbox(a){ lightbox.value = a }

function safeHtml(raw){
  const div = document.createElement('div')
  div.innerHTML = raw ?? ''
  const ALLOWED = { A:new Set(['href','title']), CODE:new Set(), I:new Set(), STRONG:new Set() }
  const walk = (el)=>{
    [...el.children].forEach(ch => {
      const tag = ch.tagName
      if (!(tag in ALLOWED)){
        el.replaceChild(document.createTextNode(ch.textContent||''), ch)
      } else {
        ;[...ch.attributes].forEach(a => { const k=a.name.toLowerCase(); if (!ALLOWED[tag].has(k)) ch.removeAttribute(a.name) })
        walk(ch)
      }
    })
  }
  walk(div); return div.innerHTML
}

const { result: repliesRes, loading: repliesLoadingRaw, error: repliesErr, refetch: refetchReplies } = useQuery(
  COMMENTS_QUERY,
  () => ({
    page: 1,
    pageSize: 200,
    orderField: 'CREATED_AT',
    desc: false,
    parentId: props.comment.id
  }),
  { enabled: showReplies, fetchPolicy: 'cache-and-network' }
)

const replies = computed(() => repliesRes.value?.comments?.results ?? [])
const repliesLoading = computed(() => !!repliesLoadingRaw.value)
const repliesError = computed(() => repliesErr.value?.message || '')

function toggleReplies(){
  showReplies.value = !showReplies.value
  if (showReplies.value) refetchReplies()
}
function onReplied(){
  replyOpen.value = false
  showReplies.value = true
  refetchReplies()
  emit('created')
}
</script>
