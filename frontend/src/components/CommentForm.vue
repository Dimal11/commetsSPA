<template>
  <form class="section" @submit.prevent="onSubmit">
    <div class="uploader">
      <div class="drop" @click="chooseFile">Добавить файл (JPG/PNG/GIF ≤320×240 или TXT ≤100KB)</div>
      <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/gif,text/plain" hidden @change="onFile" />
      <div v-if="fileInfo" class="preview">
        <img v-if="previewUrl" :src="previewUrl" />
        <span>{{ fileInfo }}</span>
        <button class="button gray" type="button" @click="clearFile">Удалить</button>
      </div>
    </div>
    <p class="hint" v-if="fileError">{{ fileError }}</p>

    <div class="section">
      <label>Имя *</label>
      <input class="input" v-model.trim="form.name" required placeholder="John42" />
    </div>
    <div class="section">
      <label>E-mail *</label>
      <input class="input" v-model.trim="form.email" type="email" required />
    </div>
    <div class="section">
      <label>Home page</label>
      <input class="input" v-model.trim="form.homePage" type="url" placeholder="https://example.com" />
    </div>

    <div class="section">
      <label>Сообщение *</label>
      <div class="toolbar">
        <button class="button gray" type="button" @click="wrap('[i]','[/i]')">i</button>
        <button class="button gray" type="button" @click="wrap('[strong]','[/strong]')">strong</button>
        <button class="button gray" type="button" @click="wrap('[code]','[/code]')">{ }</button>
        <button class="button gray" type="button" @click="insertLink">a</button>
        <div style="flex:1"></div>
        <button class="button gray" type="button" @click="preview = !preview">{{ preview ? 'Редактировать' : 'Предпросмотр' }}</button>
      </div>
      <textarea v-if="!preview" class="textarea" v-model="form.text" required></textarea>
      <div v-else class="section" v-html="previewHtml"></div>
      <p class="hint">Разрешены: &lt;a href title&gt;, &lt;code&gt;, &lt;i&gt;, &lt;strong&gt;</p>
    </div>

    <div class="section">
      <label>CAPTCHA *</label>
      <div class="uploader">
        <img :src="captchaSrc" @click="refreshCaptcha" class="captcha-img" />
        <input class="input" v-model.trim="form.captcha" placeholder="Код с картинки" required style="max-width:260px" />
      </div>
      <p class="hint">Кликните на капчу, чтобы обновить</p>
    </div>

    <div class="section" style="display:flex;gap:8px;justify-content:flex-end">
      <button class="button gray" type="button" @click="$emit('cancel')">Отмена</button>
      <button class="button" type="submit" :disabled="loading">{{ loading ? 'Отправка…' : 'Отправить' }}</button>
    </div>

    <p class="error" v-if="err">{{ err }}</p>
  </form>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMutation } from '@vue/apollo-composable'
import { CREATE_COMMENT_MUTATION } from '../graphql/operations'
import { uploadAttachmentREST } from '../api/upload'

const props = defineProps({
  parentId: { type: [String, Number, null], default: null },
  captchaMode: { type: String, default: 'image' },
  captchaImagePath: { type: String, default: '/api/captcha/' },
})
const emit = defineEmits(['created','cancel'])

const form = ref({ name:'', email:'', homePage:'', text:'', captcha:'' })
const preview = ref(false)
const err = ref('')
const loading = ref(false)
const fileInput = ref(null)
const file = ref(null)
const fileInfo = ref('')
const fileError = ref('')
const previewUrl = ref('')

const API = (window.__APP_CONFIG__?.API_BASE_URL ?? import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/,'')
const captchaSrc = ref('')
const captchaKey = ref(null)

function buildCaptchaUrl () {
  const path = (props.captchaImagePath?.startsWith('/') ? props.captchaImagePath : `/${props.captchaImagePath}`)
    .replace(/\/?$/, '/')
  return `${path}?_=${Date.now()}`
}

function loadCaptcha () {
  captchaSrc.value = buildCaptchaUrl()
}

function refreshCaptcha(){ loadCaptcha() }
onMounted(loadCaptcha)

const { mutate: mutateCreate } = useMutation(CREATE_COMMENT_MUTATION)

function chooseFile(){ fileInput.value?.click() }
function clearFile(){ file.value=null; fileInfo.value=''; fileError.value=''; previewUrl.value='' }

function onFile(e){
  fileError.value = ''
  fileInfo.value = ''
  previewUrl.value = ''
  const f = e.target.files?.[0]
  if (!f) { file.value = null; return }
  if (/^text\/plain/.test(f.type)){
    if (f.size > 100*1024){ fileError.value = 'TXT больше 100KB'; file.value = null; return }
    file.value = f; fileInfo.value = `${f.name} (${(f.size/1024).toFixed(1)} KB)`
  } else if (/^image\/(jpeg|png|gif)/.test(f.type)){
    const img = new Image()
    const url = URL.createObjectURL(f)
    img.onload = async () => {
      const w = img.naturalWidth, h = img.naturalHeight
      if (w<=320 && h<=240){
        file.value = f; previewUrl.value = url; fileInfo.value = f.name
      } else {
        const r = Math.min(320/w, 240/h), cw = Math.round(w*r), ch = Math.round(h*r)
        const canvas = document.createElement('canvas'); canvas.width=cw; canvas.height=ch
        const ctx = canvas.getContext('2d'); ctx.drawImage(img,0,0,cw,ch)
        const blob = await new Promise(res => canvas.toBlob(res, f.type==='image/png'?'image/png':'image/jpeg', .85))
        const ext = (blob.type==='image/png')?'.png':'.jpg'
        const nf = new File([blob], f.name.replace(/\.\w+$/i, ext), { type: blob.type })
        file.value = nf; fileInfo.value = nf.name; previewUrl.value = URL.createObjectURL(nf)
        URL.revokeObjectURL(url)
      }
    }
    img.onerror = () => { fileError.value = 'Не удалось прочитать изображение'; URL.revokeObjectURL(url) }
    img.src = url
  } else {
    fileError.value = 'Допустимы только изображения JPG/PNG/GIF или текстовый файл TXT'; file.value = null
  }
}

function wrap(open, close){
  const ta = document.querySelector('textarea')
  if (!ta) return
  const start = ta.selectionStart, end = ta.selectionEnd
  const val = form.value.text || ''
  form.value.text = val.slice(0,start) + open + val.slice(start,end) + close + val.slice(end)
}
function insertLink(){
  const url = prompt('Вставьте ссылку (http/https):', 'https://')
  if (!url) return
  const txt = prompt('Текст ссылки:', 'link')
  form.value.text += `[a href="${url}" title="${txt||''}"]${txt||url}[/a]`
}
function sanitizePreview(raw){
  let html = (raw||'')
    .replaceAll('[i]','<i>').replaceAll('[/i]','</i>')
    .replaceAll('[strong]','<strong>').replaceAll('[/strong]','</strong>')
    .replaceAll('[code]','<code>').replaceAll('[/code]','</code>')
    .replace(/\[a\s+href="([^"]+)"\s*(title="([^"]*)")?\]/g,'<a href="$1" title="$3">')
    .replaceAll('[/a]','</a>')
  const div = document.createElement('div'); div.innerHTML = html
  const ALLOWED = { A:new Set(['href','title']), CODE:new Set(), I:new Set(), STRONG:new Set() }
  const walk=(el)=>{ [...el.children].forEach(ch=>{ const tag=ch.tagName; if(!(tag in ALLOWED)){ el.replaceChild(document.createTextNode(ch.textContent||''),ch) } else { [...ch.attributes].forEach(a=>{ const k=a.name.toLowerCase(); if(!ALLOWED[tag].has(k)) ch.removeAttribute(a.name) }); walk(ch) } }) }
  walk(div); return div.innerHTML
}
const previewHtml = computed(() => sanitizePreview(form.value.text))

function validate(){
  const nameOk = /^[A-Za-z0-9]{2,}$/.test(form.value.name)
  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)
  const homeOk = !form.value.homePage || /^https?:\/\//i.test(form.value.homePage)
  if (!nameOk) return 'Имя: только латинские буквы и цифры (мин. 2)'
  if (!emailOk) return 'E-mail: некорректный формат'
  if (!homeOk) return 'Home page: нужен корректный URL (http/https)'
  if (!form.value.text?.trim()) return 'Сообщение пустое'
  if (!form.value.captcha?.trim()) return 'Введите CAPTCHA'
  return ''
}

async function onSubmit(){
  err.value = validate()
  if (err.value) return
  loading.value = true
  try {
    const { data } = await mutateCreate({
      input: {
        userName: form.value.name,
        email: form.value.email,
        homePage: form.value.homePage || null,
        text: form.value.text,
        captcha: form.value.captcha,
        captchaKey: captchaKey.value || null,
        parentId: props.parentId
      }
    })
    const created = data?.createComment
    if (!created?.id) throw new Error('Не удалось создать комментарий')
    if (file.value) {
      await uploadAttachmentREST(created.id, file.value)
    }
    emit('created')
    form.value = { name:'', email:'', homePage:'', text:'', captcha:'' }; clearFile(); preview.value=false
    refreshCaptcha()
  } catch (e) {
    console.error(e); err.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.uploader {
  display: flex;
  gap: 12px;
  align-items: center;
}

.captcha-img{
  height:64px;
  width:180px;
  border:1px solid var(--border);
  border-radius:6px;
  cursor:pointer;
  display:block;
}
</style>
