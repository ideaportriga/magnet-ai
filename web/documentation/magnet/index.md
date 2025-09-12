<script setup>
import { withBase } from 'vitepress'

if (typeof window !== 'undefined') {
  window.location.href = withBase('/docs/en/');
}
</script>

Redirecting to <a :href="withBase('/docs/en/')">/docs/en/</a>...