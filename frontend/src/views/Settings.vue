<template>
  <div class="settings-page">
    <h2>{{ t('settings.title') }}</h2>

    <div class="card">
      <h3>{{ t('settings.deepseekSection') }}</h3>
      <p class="section-hint" v-html="t('settings.deepseekHint')"></p>
      <div class="status-line">
        <span>{{ t('settings.statusLabel') }}</span>
        <span :class="status.deepseek ? 'status-ok' : 'status-err'">
          {{ status.deepseek ? t('settings.configured') : t('settings.notConfigured') }}
        </span>
      </div>
      <div class="form-group">
        <label>{{ t('settings.apiKey') }}</label>
        <input v-model="deepseek.api_key" type="password" placeholder="sk-..." />
      </div>
      <div class="form-group">
        <label>{{ t('settings.apiUrl') }}</label>
        <input v-model="deepseek.api_url" placeholder="https://api.deepseek.com/v1/chat/completions" />
      </div>
      <div class="form-group">
        <label>{{ t('settings.modelName') }}</label>
        <input v-model="deepseek.model" placeholder="deepseek-chat" />
      </div>
      <div class="form-row-2">
        <div class="form-group">
          <label>{{ t('settings.temperature') }}</label>
          <input v-model.number="deepseek.temperature" type="number" step="0.1" min="0" max="2" />
        </div>
        <div class="form-group">
          <label>{{ t('settings.maxTokens') }}</label>
          <input v-model.number="deepseek.max_tokens" type="number" min="100" max="8000" />
        </div>
      </div>
      <button class="btn btn-primary" @click="saveDeepSeek" :disabled="saving">
        {{ saving ? t('settings.saving') : t('settings.saveDeepSeek') }}
      </button>
    </div>

    <div class="card">
      <h3>{{ t('settings.claudeSection') }}</h3>
      <p class="section-hint" v-html="t('settings.claudeHint')"></p>
      <div class="status-line">
        <span>{{ t('settings.statusLabel') }}</span>
        <span :class="status.claude ? 'status-ok' : 'status-err'">
          {{ status.claude ? t('settings.configured') : t('settings.notConfiguredSingleMode') }}
        </span>
      </div>
      <div class="form-group">
        <label>{{ t('settings.apiKey') }}</label>
        <input v-model="claude.api_key" type="password" placeholder="sk-ant-..." />
      </div>
      <div class="form-group">
        <label>{{ t('settings.apiUrl') }}</label>
        <input v-model="claude.api_url" placeholder="https://api.anthropic.com/v1/messages" />
      </div>
      <div class="form-group">
        <label>{{ t('settings.modelName') }}</label>
        <input v-model="claude.model" placeholder="claude-sonnet-4-20250514" />
      </div>
      <div class="form-group">
        <label>{{ t('settings.maxTokens') }}</label>
        <input v-model.number="claude.max_tokens" type="number" min="100" max="8000" />
      </div>
      <button class="btn btn-primary" @click="saveClaude" :disabled="saving">
        {{ saving ? t('settings.saving') : t('settings.saveClaude') }}
      </button>
    </div>

    <div class="card">
      <h3>{{ t('settings.singleModelMode') }}</h3>
      <p class="section-hint">{{ t('settings.singleModelHint') }}</p>
      <div class="toggle-row">
        <label class="toggle-label">
          <input type="checkbox" v-model="singleModelMode" @change="saveSystem" />
          <span>{{ t('settings.enableSingleModel') }}</span>
        </label>
        <span class="toggle-status">{{ singleModelMode ? t('settings.enabled') : t('settings.disabled') }}</span>
      </div>
    </div>

    <div class="card" v-if="message" :class="messageType">
      <p>{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()
const api = axios.create({ baseURL: '/api', timeout: 10000 })

const deepseek = ref({
  api_key: '',
  api_url: 'https://api.deepseek.com/v1/chat/completions',
  model: 'deepseek-chat',
  temperature: 0.7,
  max_tokens: 500,
})

const claude = ref({
  api_key: '',
  api_url: 'https://api.anthropic.com/v1/messages',
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1500,
})

const singleModelMode = ref(false)
const status = ref({ deepseek: false, claude: false })
const saving = ref(false)
const message = ref('')
const messageType = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/settings')
    const config = res.data.config
    status.value = res.data.status
    if (config.deepseek) {
      deepseek.value = { ...deepseek.value, ...config.deepseek }
    }
    if (config.claude) {
      claude.value = { ...claude.value, ...config.claude }
    }
    if (config.system) {
      singleModelMode.value = config.system.single_model_mode || false
    }
  } catch (err) {
    console.error(t('settings.fetchFailed'), err)
  }
})

async function saveDeepSeek() {
  saving.value = true
  message.value = ''
  try {
    const res = await api.post('/settings/deepseek', deepseek.value)
    message.value = res.data.message
    messageType.value = 'success'
    status.value.deepseek = true
  } catch (err) {
    message.value = t('settings.saveFailed', { msg: err.response?.data?.detail || err.message })
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

async function saveClaude() {
  saving.value = true
  message.value = ''
  try {
    const res = await api.post('/settings/claude', claude.value)
    message.value = res.data.message
    messageType.value = 'success'
    status.value.claude = true
  } catch (err) {
    message.value = t('settings.saveFailed', { msg: err.response?.data?.detail || err.message })
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

async function saveSystem() {
  try {
    await api.post('/settings/system', { single_model_mode: singleModelMode.value })
    const res = await api.get('/settings/status')
    status.value = res.data
  } catch (err) {
    message.value = t('settings.saveFailed', { msg: err.response?.data?.detail || err.message })
    messageType.value = 'error'
  }
}
</script>

<style scoped>
.settings-page h2 {
  color: var(--primary);
  margin-bottom: 16px;
}

.settings-page h3 {
  color: var(--primary);
  margin-bottom: 4px;
}

.section-hint {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 12px;
}

.status-line {
  margin-bottom: 12px;
  font-size: 14px;
}

.status-ok {
  color: var(--success);
  font-weight: 600;
}

.status-err {
  color: var(--danger);
  font-weight: 600;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  color: var(--text);
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(45, 106, 79, 0.15);
}

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.toggle-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.toggle-status {
  font-size: 14px;
  font-weight: 500;
}

.success {
  background: #d1e7dd;
  color: #0f5132;
  border: 1px solid #badbcc;
}

.error {
  background: #f8d7da;
  color: #842029;
  border: 1px solid #f5c6cb;
}
</style>
