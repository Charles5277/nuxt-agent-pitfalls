<script setup lang="ts">
const { data: viaUseFetch } = await useFetch('/api/echo', { key: 'uf' })
const { data: viaDollar } = await useAsyncData('df', () => $fetch('/api/echo'))
</script>
<template><pre id="out">{{ JSON.stringify({ useFetch: viaUseFetch, dollarFetch: viaDollar }) }}</pre></template>
