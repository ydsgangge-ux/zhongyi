<template>
  <div class="chat-bubble" :class="[role, { danger }]">
    <div class="bubble-avatar">
      <span v-if="role === 'assistant'">🧑‍⚕️</span>
      <span v-else-if="role === 'user'">👤</span>
      <span v-else>ℹ️</span>
    </div>
    <div class="bubble-content">
      <div class="bubble-role">{{ roleLabel }}</div>
      <div class="bubble-text" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
  danger: { type: Boolean, default: false },
})

const { t } = useI18n()

const roleLabel = computed(() => {
  if (props.role === 'assistant') return t('chat.assistant')
  if (props.role === 'user') return t('chat.user')
  return t('chat.system')
})

const renderedContent = computed(() => {
  try {
    return marked.parse(props.content || '')
  } catch {
    return props.content
  }
})
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 10px;
  max-width: 85%;
}

.chat-bubble.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-bubble.assistant {
  align-self: flex-start;
}

.chat-bubble.system {
  align-self: center;
  max-width: 90%;
}

.bubble-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.bubble-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-bubble.user .bubble-content {
  background: var(--primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-bubble.assistant .bubble-content {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.chat-bubble.system .bubble-content {
  background: #e8f4f8;
  color: #0c5460;
  font-size: 13px;
  text-align: center;
}

.chat-bubble.danger .bubble-content {
  background: #f8d7da;
  color: #842029;
  border-color: #f5c6cb;
}

.bubble-role {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.chat-bubble.user .bubble-role {
  color: rgba(255, 255, 255, 0.7);
  text-align: right;
}

.bubble-text :deep(p) {
  margin: 0;
}

.bubble-text :deep(ul),
.bubble-text :deep(ol) {
  padding-left: 18px;
  margin: 4px 0;
}
</style>
