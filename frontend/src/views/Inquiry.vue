<template>
  <div class="inquiry-page">
    <div class="session-setup" v-if="!sessionId">
      <div class="card setup-card">
        <h2>{{ t('inquiry.startTitle') }}</h2>
        <p class="setup-desc">{{ t('inquiry.startDesc') }}</p>
        <div class="form-group">
          <label>{{ t('inquiry.age') }}</label>
          <input v-model="age" type="text" inputmode="numeric" :placeholder="t('inquiry.agePlaceholder')" />
        </div>
        <div class="form-group">
          <label>{{ t('inquiry.gender') }}</label>
          <select v-model="gender">
            <option value="">{{ t('inquiry.genderSelect') }}</option>
            <option value="男">{{ t('inquiry.male') }}</option>
            <option value="女">{{ t('inquiry.female') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ t('inquiry.birthYear') }}</label>
          <input v-model="birthYear" type="text" inputmode="numeric" :placeholder="t('inquiry.birthYearPlaceholder')" />
        </div>
        <div class="form-group">
          <label>{{ t('inquiry.region') }}</label>
          <input v-model="region" type="text" :placeholder="t('inquiry.regionPlaceholder')" />
        </div>
        <button class="btn btn-primary" @click="startSession" :disabled="loading">
          {{ loading ? t('inquiry.starting') : t('inquiry.startBtn') }}
        </button>
      </div>
    </div>

    <div class="chat-container" v-else>
      <div class="chat-header">
        <span class="round-badge">{{ t('inquiry.round', { round: currentRound }) }}</span>
        <span class="season-badge">{{ t('inquiry.season', { season }) }}</span>
      </div>

      <div class="chat-messages" ref="messagesContainer">
        <ChatBubble
          v-for="(msg, index) in messages"
          :key="index"
          :role="msg.role"
          :content="msg.content"
          :danger="msg.danger"
        />
        <div v-if="streaming" class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>

      <div class="danger-alert" v-if="dangerSignal">
        <p>🚨 {{ dangerSignal }}</p>
      </div>

      <div class="chat-input-area">
        <div class="input-row">
          <input
            ref="chatInputRef"
            v-model="userInput"
            type="text"
            :placeholder="t('inquiry.inputPlaceholder')"
            @keyup.enter="sendMessage"
          />
          <button
            class="btn btn-primary"
            @click="sendMessage"
            :disabled="!userInput.trim() || streaming"
          >
            {{ t('inquiry.sendBtn') }}
          </button>
        </div>
        <div class="action-row" v-if="currentRound >= 3">
          <button class="btn btn-outline" @click="startAnalysis" :disabled="analyzing">
            {{ analyzing ? t('inquiry.analyzing') : t('inquiry.analyzeBtn') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ChatBubble from '../components/ChatBubble.vue'
import { startSession as apiStartSession, sendMessageStream, analyzeSession } from '../api'

const router = useRouter()
const { t, locale } = useI18n()

const sessionId = ref('')
const age = ref('')
const gender = ref('')
const birthYear = ref('')
const region = ref('')
const season = ref('')
const currentRound = ref(0)
const messages = ref([])
const userInput = ref('')
const loading = ref(false)
const streaming = ref(false)
const analyzing = ref(false)
const dangerSignal = ref('')
const messagesContainer = ref(null)
const chatInputRef = ref(null)

onMounted(() => {
  setTimeout(() => {
    if (chatInputRef.value) {
      chatInputRef.value.focus()
    }
  }, 500)
})

async function startSession() {
  loading.value = true
  try {
    const data = await apiStartSession({
      age: age.value ? Number(age.value) : null,
      gender: gender.value,
      birth_year: birthYear.value ? Number(birthYear.value) : null,
      region: region.value,
      locale: locale.value,
    })
    sessionId.value = data.session_id
    season.value = data.season
    messages.value.push({ role: 'assistant', content: data.greeting })
    await nextTick()
    if (chatInputRef.value) chatInputRef.value.focus()
  } catch (err) {
    messages.value.push({ role: 'system', content: t('chat.createFailed', { msg: err.message }) })
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || streaming.value) return

  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  streaming.value = true

  const streamTimeout = setTimeout(() => {
    if (streaming.value) {
      streaming.value = false
      messages.value.push({ role: 'system', content: t('chat.timeout') })
    }
  }, 30000)

  await nextTick()
  scrollToBottom()

  try {
    const body = await sendMessageStream(sessionId.value, text)
    const reader = body.getReader()
    const decoder = new TextDecoder()
    let assistantMsg = { role: 'assistant', content: '' }
    messages.value.push(assistantMsg)

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          assistantMsg.content += line.slice(6)
        }
      }
      messages.value = [...messages.value]
      await nextTick()
      scrollToBottom()
    }

    currentRound.value += 1
  } catch (err) {
    messages.value.push({ role: 'system', content: t('chat.sendFailed', { msg: err.message }) })
  } finally {
    clearTimeout(streamTimeout)
    streaming.value = false
    await nextTick()
    if (chatInputRef.value) chatInputRef.value.focus()
  }
}

async function startAnalysis() {
  analyzing.value = true
  try {
    const result = await analyzeSession(sessionId.value)
    router.push({ name: 'Result', params: { sessionId: sessionId.value }, state: { result } })
  } catch (err) {
    messages.value.push({ role: 'system', content: t('chat.analyzeFailed', { msg: err.message }) })
  } finally {
    analyzing.value = false
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.inquiry-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.session-setup {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.setup-card {
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.setup-card h2 {
  margin-bottom: 8px;
  color: var(--primary);
}

.setup-desc {
  color: var(--text-secondary);
  margin-bottom: 20px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 16px;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  color: var(--text);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary);
}

.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  margin-bottom: 8px;
}

.round-badge,
.season-badge {
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 16px;
  background: var(--accent);
  color: var(--primary-dark);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.danger-alert {
  flex-shrink: 0;
  background: #f8d7da;
  color: #842029;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 8px;
}

.chat-input-area {
  flex-shrink: 0;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  background: var(--card-bg);
}

.input-row {
  display: flex;
  gap: 8px;
}

.input-row input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  color: var(--text);
}

.input-row input:focus {
  outline: none;
  border-color: var(--primary);
}

.action-row {
  margin-top: 8px;
  text-align: center;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
