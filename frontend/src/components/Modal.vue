<template>
  <div class="modal" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-head">
        <strong><slot name="title" /></strong>
        <button class="button gray" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['close'])
</script>
