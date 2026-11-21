<template>
  <div class="result-page">
    <div v-if="!result" class="card">
      <p>{{ loadError || t('inquiry.loadingResult') }}</p>
    </div>

    <div v-else>
      <div class="result-header card">
        <h2>{{ t('result.title') }}</h2>
        <div class="confidence-badge" :class="confidenceClass">
          {{ confidenceLabel }}
        </div>
      </div>

      <div v-if="tcm.emergency_warning" class="emergency-alert">
        🚨 {{ tcm.emergency_warning }}
      </div>

      <ResultCard :title="t('result.tcmAnalysis')" icon="中医">
        <div class="section">
          <h4>{{ t('result.syndromeDiagnosis') }}</h4>
          <p><strong>{{ t('result.primarySyndrome') }}</strong>{{ tcm.syndrome?.primary || '-' }}</p>
          <p v-if="tcm.syndrome?.secondary"><strong>{{ t('result.secondarySyndrome') }}</strong>{{ tcm.syndrome.secondary }}</p>
          <p><strong>{{ t('result.confidence') }}</strong>{{ Math.round((tcm.syndrome?.confidence || 0) * 100) }}%</p>
        </div>
        <div class="section">
          <h4>{{ t('result.eightPrinciples') }}</h4>
          <div class="bagang-grid">
            <div class="bagang-item">
              <span class="label">{{ t('result.yinYang') }}</span>
              <span class="value">{{ tcm.bagang?.yin_yang || '-' }}</span>
            </div>
            <div class="bagang-item">
              <span class="label">{{ t('result.biaoLi') }}</span>
              <span class="value">{{ tcm.bagang?.biao_li || '-' }}</span>
            </div>
            <div class="bagang-item">
              <span class="label">{{ t('result.hanRe') }}</span>
              <span class="value">{{ tcm.bagang?.han_re || '-' }}</span>
            </div>
            <div class="bagang-item">
              <span class="label">{{ t('result.xuShi') }}</span>
              <span class="value">{{ tcm.bagang?.xu_shi || '-' }}</span>
            </div>
          </div>
        </div>
        <div class="section">
          <h4>{{ t('result.organLocation') }}</h4>
          <p>{{ tcm.zangfu || '-' }}</p>
        </div>
        <div class="section" v-if="tcm.special_system">
          <h4>{{ t('result.specialSystem') }}</h4>
          <p>{{ tcm.special_system }}</p>
        </div>
        <div class="section">
          <h4>{{ t('result.etiology') }}</h4>
          <p>{{ tcm.etiology || '-' }}</p>
        </div>
        <div class="section">
          <h4>{{ t('result.treatmentPrinciple') }}</h4>
          <p>{{ tcm.treatment_principle || '-' }}</p>
        </div>
      </ResultCard>

      <ResultCard :title="t('result.prescription')" icon="方案">
        <div class="prescription-section">
          <div class="prescription-item" v-if="tcm.prescription?.diet_therapy">
            <span class="safety-badge badge-green">{{ t('result.dietTherapy') }}</span>
            <p>{{ tcm.prescription.diet_therapy }}</p>
          </div>
          <div class="prescription-item" v-if="tcm.prescription?.patent_medicine">
            <span class="safety-badge badge-yellow">{{ t('result.patentMedicine') }}</span>
            <p>{{ tcm.prescription.patent_medicine }}</p>
          </div>
          <div class="prescription-item" v-if="tcm.prescription?.decoction">
            <span class="safety-badge badge-yellow">{{ t('result.decoction') }}</span>
            <p>{{ tcm.prescription.decoction }}</p>
            <p class="warning-text">{{ t('result.decoctionWarning') }}</p>
          </div>
          <div class="prescription-item" v-if="tcm.prescription?.warning">
            <span class="safety-badge badge-red">{{ t('result.compatibilityWarning') }}</span>
            <p>{{ tcm.prescription.warning }}</p>
          </div>
        </div>
      </ResultCard>

      <ResultCard :title="t('result.lifestyle')" icon="调养">
        <div class="lifestyle-grid">
          <div class="lifestyle-item" v-if="tcm.lifestyle?.diet">
            <strong>{{ t('result.dietAdvice') }}</strong>
            <p>{{ tcm.lifestyle.diet }}</p>
          </div>
          <div class="lifestyle-item" v-if="tcm.lifestyle?.sleep">
            <strong>{{ t('result.sleepAdvice') }}</strong>
            <p>{{ tcm.lifestyle.sleep }}</p>
          </div>
          <div class="lifestyle-item" v-if="tcm.lifestyle?.emotion">
            <strong>{{ t('result.emotionAdvice') }}</strong>
            <p>{{ tcm.lifestyle.emotion }}</p>
          </div>
        </div>
      </ResultCard>

      <ResultCard :title="t('result.westernRef')" icon="西医">
        <div class="western-section">
          <div v-if="western.danger_signals?.length" class="danger-signals">
            <h4>{{ t('result.dangerSignals') }}</h4>
            <div v-for="(sig, i) in western.danger_signals" :key="i" class="danger-item">
              <span class="badge badge-red">{{ sig.urgency }}</span>
              <span>{{ sig.signal }} — {{ sig.action }}</span>
            </div>
          </div>
          <div v-if="western.possible_conditions?.length">
            <h4>{{ t('result.possibleConditions') }}</h4>
            <div v-for="(cond, i) in western.possible_conditions" :key="i" class="condition-item">
              <span class="badge" :class="cond.probability === 'high' ? 'badge-yellow' : 'badge-green'">{{ cond.probability }}</span>
              <strong>{{ cond.condition }}</strong>
              <p>{{ cond.description }}</p>
            </div>
          </div>
          <div v-if="western.recommended_tests?.length">
            <h4>{{ t('result.recommendedTests') }}</h4>
            <div v-for="(test, i) in western.recommended_tests" :key="i" class="test-item">
              <strong>{{ test.test }}</strong>
              <span>— {{ test.reason }}</span>
            </div>
          </div>
          <div v-if="western.doctor_visit" class="doctor-visit">
            <h4>{{ t('result.doctorAdvice') }}</h4>
            <p v-if="western.doctor_visit.needed">
              <span class="badge" :class="western.doctor_visit.urgency === 'immediate' ? 'badge-red' : 'badge-yellow'">
                {{ western.doctor_visit.urgency === 'immediate' ? t('result.urgencyImmediate') : western.doctor_visit.urgency === 'soon' ? t('result.urgencySoon') : t('result.urgencyRoutine') }}
              </span>
              {{ t('result.deptSuggestion', { dept: western.doctor_visit.department }) }}
            </p>
            <p v-else>{{ t('result.noUrgentNeed') }}</p>
          </div>
        </div>
      </ResultCard>

      <ResultCard v-if="messages.length" :title="t('result.inquiryProcess')" icon="问诊">
        <details class="dialogue-details">
          <summary>{{ t('result.inquiryProcess') }}（{{ messages.length }}）</summary>
          <div class="dialogue">
            <div v-for="(msg, i) in messages" :key="i" class="dialogue-line" :class="msg.role">
              <span class="dialogue-role">{{ msg.role === 'user' ? t('chat.user') : t('chat.assistant') }}</span>
              <p class="dialogue-text">{{ msg.content }}</p>
            </div>
          </div>
        </details>
      </ResultCard>

      <div class="disclaimer card">
        <p>{{ result.disclaimer }}</p>
      </div>

      <div class="actions">
        <button class="btn btn-primary" @click="$router.push('/')">{{ t('inquiry.newInquiry') }}</button>
        <button class="btn btn-outline" @click="$router.push('/history')">{{ t('inquiry.viewRecords') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ResultCard from '../components/ResultCard.vue'
import { getAnalysisResult } from '../api'

const route = useRoute()
const { t } = useI18n()

// 优先使用路由跳转时携带的结果；刷新或直接打开链接时回退到后端查询
const result = ref(history.state?.result || null)
const loadError = ref('')

onMounted(async () => {
  if (result.value) return
  try {
    result.value = await getAnalysisResult(route.params.sessionId)
  } catch (err) {
    loadError.value = t('chat.analyzeFailed', { msg: err.message })
  }
})

const tcm = computed(() => result.value?.tcm_analysis || {})
const western = computed(() => result.value?.western_reference || {})
const messages = computed(() => result.value?.messages || [])

const confidenceClass = computed(() => {
  const level = tcm.value.confidence_level
  if (level === 'green') return 'badge-green'
  if (level === 'yellow') return 'badge-yellow'
  return 'badge-red'
})

const confidenceLabel = computed(() => {
  const level = tcm.value.confidence_level
  if (level === 'green') return t('result.confidenceHigh')
  if (level === 'yellow') return t('result.confidenceMedium')
  return t('result.confidenceLow')
})
</script>

<style scoped>
.result-page {
  padding-bottom: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header h2 {
  color: var(--primary);
}

.confidence-badge {
  font-size: 14px;
  padding: 4px 14px;
  border-radius: 16px;
}

.emergency-alert {
  margin-top: 12px;
  background: #f8d7da;
  border: 1px solid #f1aeb5;
  color: #842029;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.section {
  margin-bottom: 16px;
}

.section h4 {
  color: var(--primary);
  margin-bottom: 6px;
  font-size: 15px;
}

.bagang-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.bagang-item {
  text-align: center;
  padding: 8px;
  background: var(--bg);
  border-radius: 8px;
}

.bagang-item .label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.bagang-item .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
}

.prescription-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prescription-item {
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
}

.safety-badge {
  display: inline-block;
  margin-bottom: 6px;
}

.warning-text {
  color: var(--danger);
  font-size: 13px;
  margin-top: 4px;
}

.lifestyle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.lifestyle-item {
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
}

.lifestyle-item strong {
  display: block;
  margin-bottom: 4px;
  color: var(--primary);
}

.western-section h4 {
  color: var(--primary);
  margin: 12px 0 6px;
  font-size: 15px;
}

.danger-item,
.condition-item,
.test-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.condition-item p {
  width: 100%;
  font-size: 13px;
  color: var(--text-secondary);
  padding-left: 0;
}

.doctor-visit {
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  margin-top: 8px;
}

.disclaimer {
  background: #fff3cd;
  border: 1px solid #ffc107;
  text-align: center;
  font-size: 13px;
  color: #856404;
}

.dialogue-details summary {
  cursor: pointer;
  color: var(--primary);
  font-size: 14px;
  font-weight: 500;
}

.dialogue {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow-y: auto;
}

.dialogue-line {
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--bg);
}

.dialogue-line.user {
  background: var(--accent);
}

.dialogue-role {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.dialogue-text {
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}
</style>
