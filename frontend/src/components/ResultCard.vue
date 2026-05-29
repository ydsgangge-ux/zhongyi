<template>
  <div class="result-card card">
    <div class="card-title">
      <span class="card-icon">{{ icon }}</span>
      <h3>{{ title }}</h3>
    </div>
    <div class="card-body">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  icon: { type: String, default: '' },
})
</script>

<style scoped>
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.card-icon {
  font-size: 20px;
}

.card-title h3 {
  font-size: 16px;
  color: var(--primary);
  font-weight: 600;
}
</style>
