<template>
  <div class="history-page">
    <h2>{{ t('history.title') }}</h2>
    <div v-if="records.length === 0" class="card empty-state">
      <p>{{ t('history.empty') }}</p>
      <button class="btn btn-primary" @click="$router.push('/')">{{ t('history.startInquiry') }}</button>
    </div>
    <div v-else>
      <div v-for="record in records" :key="record.id" class="card record-card">
        <div class="record-header">
          <span class="record-id">#{{ record.id }}</span>
          <span class="record-date">{{ record.created_at }}</span>
        </div>
        <div class="record-body">
          <p class="record-notes" v-if="record.notes">{{ record.notes }}</p>
          <p class="record-session">{{ t('history.sessionId') }}{{ record.session_id }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getHealthRecords } from '../api'

const { t } = useI18n()
const records = ref([])

onMounted(async () => {
  try {
    records.value = await getHealthRecords()
  } catch (err) {
    console.error(t('history.fetchFailed'), err)
  }
})
</script>

<style scoped>
.history-page h2 {
  color: var(--primary);
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.record-card {
  transition: transform 0.2s;
}

.record-card:hover {
  transform: translateY(-2px);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-id {
  font-weight: 600;
  color: var(--primary);
}

.record-date {
  font-size: 13px;
  color: var(--text-secondary);
}

.record-notes {
  font-size: 14px;
  margin-bottom: 4px;
}

.record-session {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
