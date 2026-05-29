<template>
  <div id="app-container">
    <header class="app-header">
      <router-link to="/" class="logo">
        <span class="logo-icon">🌿</span>
        <span class="logo-text">{{ t('app.title') }}</span>
      </router-link>
      <nav class="nav-links">
        <router-link to="/">{{ t('app.nav.inquiry') }}</router-link>
        <router-link to="/history">{{ t('app.nav.history') }}</router-link>
        <router-link to="/settings">{{ t('app.nav.settings') }}</router-link>
        <button class="lang-btn" @click="toggleLang" :title="t(`langSwitch.${locale === 'zh' ? 'en' : 'zh'}`)">
          {{ t(`langSwitch.${locale === 'zh' ? 'en' : 'zh'}`) }}
        </button>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>{{ t('app.footer') }}</p>
    </footer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { locale, t } = useI18n()

function toggleLang() {
  locale.value = locale.value === 'zh' ? 'en' : 'zh'
  localStorage.setItem('locale', locale.value)
}
</script>

<style scoped>
.lang-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.lang-btn:hover {
  color: var(--primary);
  border-color: var(--primary);
}
</style>
