// Extracted from ./model.js so Features.vue can import without creating
// a circular dependency (model.js imports Features.vue for controls.component).
export const featureOptions = [
  { label: 'JSON Mode', value: 'json_mode' },
  { label: 'Structured Outputs', value: 'json_schema' },
  { label: 'Tool Calling', value: 'tool_calling' },
  { label: 'Reasoning', value: 'reasoning' },
  { label: 'Diarization', value: 'diarization' },
]
