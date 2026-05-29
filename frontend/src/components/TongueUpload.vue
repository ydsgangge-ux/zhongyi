<template>
  <div class="tongue-upload">
    <label class="upload-btn" :class="{ uploading }">
      <input type="file" accept="image/*" @change="handleFile" :disabled="uploading" hidden />
      <span v-if="!uploading">📷 舌象</span>
      <span v-else>上传中...</span>
    </label>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['upload'])
const uploading = ref(false)

async function handleFile(event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploading.value = true
  try {
    const base64 = await readFileAsBase64(file)
    emit('upload', base64)
  } catch (err) {
    console.error('读取图片失败', err)
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
</script>

<style scoped>
.upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  white-space: nowrap;
}

.upload-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.upload-btn.uploading {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
