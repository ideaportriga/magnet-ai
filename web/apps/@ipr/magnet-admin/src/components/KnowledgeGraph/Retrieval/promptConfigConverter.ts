import { uid } from 'quasar'
import type { ConversionResult, PromptTemplate, PromptTemplateVariant, RetrievalConfig, RetrievalExample, ValidationError } from './models'

// ================================
// Constants
// ================================

export const PROMPT_SYSTEM_NAME = 'KG_AGENT_REACT_PROMPT'

export const SECTION_MARKERS = {
  PERSONA: { start: '<!-- PERSONA START -->', end: '<!-- PERSONA END -->' },
  GENERAL_INSTRUCTIONS: { start: '<!-- GENERAL INSTRUCTIONS START -->', end: '<!-- GENERAL INSTRUCTIONS END -->' },
  EXIT_INSTRUCTIONS: { start: '<!-- EXIT INSTRUCTIONS START -->', end: '<!-- EXIT INSTRUCTIONS END -->' },
  OUTPUT_INSTRUCTIONS: { start: '<!-- OUTPUT INSTRUCTIONS START -->', end: '<!-- OUTPUT INSTRUCTIONS END -->' },
  ADDITIONAL_OUTPUT_INSTRUCTIONS: {
    start: '<!-- ADDITIONAL OUTPUT INSTRUCTIONS START -->',
    end: '<!-- ADDITIONAL OUTPUT INSTRUCTIONS END -->',
  },
  EXAMPLES: { start: '<!-- EXAMPLES START -->', end: '<!-- EXAMPLES END -->' },
} as const

export const BASE_VARIANT_NAME = 'base_variant'

// ================================
// Helpers
// ================================

/**
 * Extract content between section markers
 */
function extractSection(text: string, sectionName: keyof typeof SECTION_MARKERS): string | null {
  const markers = SECTION_MARKERS[sectionName]
  const startIdx = text.indexOf(markers.start)

  if (startIdx === -1) {
    return null
  }

  const contentStart = startIdx + markers.start.length
  const endIdx = text.indexOf(markers.end, contentStart)

  if (endIdx === -1) {
    return null
  }

  return text.slice(contentStart, endIdx).trim()
}

/**
 * Wrap content with section markers
 */
function wrapSection(content: string, sectionName: keyof typeof SECTION_MARKERS): string {
  const markers = SECTION_MARKERS[sectionName]
  return `${markers.start}\n${content.trim()}\n${markers.end}`
}

/**
 * Parse examples section from prompt text
 */
function parseExamplesSection(examplesText: string): RetrievalExample[] {
  const examples: RetrievalExample[] = []
  // Format:
  // ### Example: Title
  // **User:** user message
  // **Agent:** agent response
  const blocks = examplesText.split(/(?=###\s*Example:)/g).filter((b) => b.trim())

  for (const block of blocks) {
    const titleMatch = block.match(/###\s*Example:\s*(.+?)(?=\n)/)
    const userMatch = block.match(/\*\*User:\*\*\s*([\s\S]*?)(?=\*\*Agent:\*\*)/i)
    const agentMatch = block.match(/\*\*Agent:\*\*\s*([\s\S]*?)$/i)

    if (titleMatch && userMatch && agentMatch) {
      examples.push({
        id: uid(),
        title: titleMatch[1].trim(),
        input: userMatch[1].trim(),
        output: agentMatch[1].trim(),
      })
    }
  }

  return examples
}

/**
 * Format examples as prompt text
 */
function formatExamplesSection(examples: RetrievalExample[]): string {
  if (examples.length === 0) {
    return ''
  }

  const lines: string[] = []
  for (const example of examples) {
    lines.push(`### Example: ${example.title || `Example ${example.id}`}`)
    lines.push(`**User:** ${example.input}`)
    lines.push(`**Agent:** ${example.output}`)
    lines.push('')
  }

  return lines.join('\n').trim()
}

// ================================
// Conversion: Config -> Prompt
// ================================

/**
 * Convert UI configuration to prompt template text
 */
export function configToPrompt(config: RetrievalConfig): ConversionResult<string> {
  const errors: ValidationError[] = []
  const warnings: string[] = []

  try {
    const sections: string[] = []

    // PERSONA section
    if (config.promptSections.persona?.trim()) {
      sections.push(wrapSection(config.promptSections.persona, 'PERSONA'))
    } else {
      warnings.push('Persona section is empty')
    }

    // INSTRUCTIONS section
    if (config.promptSections.instructions?.trim()) {
      sections.push(wrapSection(config.promptSections.instructions, 'GENERAL_INSTRUCTIONS'))
    } else {
      warnings.push('Instructions section is empty')
    }

    // EXIT INSTRUCTIONS section
    sections.push(wrapSection('{exitInstructions}', 'EXIT_INSTRUCTIONS'))

    // OUTPUT INSTRUCTIONS section
    sections.push(wrapSection('{outputInstructions}', 'OUTPUT_INSTRUCTIONS'))

    // ADDITIONAL OUTPUT INSTRUCTIONS section
    if (config.promptSections.additionalOutputInstructions?.trim()) {
      sections.push(wrapSection(config.promptSections.additionalOutputInstructions, 'ADDITIONAL_OUTPUT_INSTRUCTIONS'))
    } else {
      // Optional section, so no warning needed if empty, or we can push warning if desired
      // warnings.push('Additional output instructions section is empty')
    }

    // EXAMPLES section
    sections.push(wrapSection('{exampleList}', 'EXAMPLES'))

    const promptText = sections.join('\n\n')

    return {
      success: errors.length === 0,
      data: promptText,
      errors,
      warnings,
    }
  } catch (error) {
    return {
      success: false,
      errors: [
        {
          type: 'parse_error',
          message: 'Failed to convert configuration to prompt',
          details: error instanceof Error ? error.message : String(error),
        },
      ],
      warnings,
    }
  }
}

// ================================
// Conversion: Prompt -> Config
// ================================

/**
 * Convert prompt template text to UI configuration
 */
export function promptToConfig(promptText: string, existingConfig?: Partial<RetrievalConfig>): ConversionResult<RetrievalConfig> {
  const errors: ValidationError[] = []
  const warnings: string[] = []

  try {
    // Extract sections
    const persona = extractSection(promptText, 'PERSONA')
    const instructions = extractSection(promptText, 'GENERAL_INSTRUCTIONS')
    const exitInstructions = extractSection(promptText, 'EXIT_INSTRUCTIONS')
    const outputInstructions = extractSection(promptText, 'OUTPUT_INSTRUCTIONS')
    const additionalOutputInstructions = extractSection(promptText, 'ADDITIONAL_OUTPUT_INSTRUCTIONS')
    const examplesSection = extractSection(promptText, 'EXAMPLES')

    // Validate required sections
    if (persona === null) {
      errors.push({
        type: 'missing_section',
        message: 'Section is missing',
        section: 'PERSONA',
        details: 'The prompt must include following section:\n<!-- PERSONA START -->\n...\n<!-- PERSONA END -->',
      })
    }

    if (instructions === null) {
      errors.push({
        type: 'missing_section',
        message: 'Section is missing',
        section: 'GENERAL_INSTRUCTIONS',
        details: 'The prompt must include following section:\n<!-- GENERAL INSTRUCTIONS START -->\n...\n<!-- GENERAL INSTRUCTIONS END -->',
      })
    }

    if (exitInstructions === null) {
      errors.push({
        type: 'missing_section',
        message: 'Section is missing',
        section: 'EXIT_INSTRUCTIONS',
        details: 'The prompt must include following section:\n<!-- EXIT INSTRUCTIONS START -->\n...\n<!-- EXIT INSTRUCTIONS END -->',
      })
    } else if (!exitInstructions.includes('{exitInstructions}')) {
      errors.push({
        type: 'missing_section',
        message: 'Variable {exitInstructions} is missing',
        details: 'The EXIT INSTRUCTIONS section must include the\n{exitInstructions} variable.',
      })
    }

    if (outputInstructions === null) {
      errors.push({
        type: 'missing_section',
        message: 'Section is missing',
        section: 'OUTPUT_INSTRUCTIONS',
        details: 'The prompt must include following section:\n<!-- OUTPUT INSTRUCTIONS START -->\n...\n<!-- OUTPUT INSTRUCTIONS END -->',
      })
    } else if (!outputInstructions.includes('{outputInstructions}')) {
      errors.push({
        type: 'missing_section',
        message: 'Variable {outputInstructions} is missing',
        details: 'The OUTPUT INSTRUCTIONS section must include the\n{outputInstructions} variable.',
      })
    }

    if (examplesSection === null) {
      errors.push({
        type: 'missing_section',
        message: 'Section is missing',
        section: 'EXAMPLES',
        details: 'The prompt must include following section:\n<!-- EXAMPLES START -->\n...\n<!-- EXAMPLES END -->',
      })
    } else if (!examplesSection.includes('{exampleList}')) {
      errors.push({
        type: 'missing_section',
        message: 'Variable {exampleList} is missing',
        details: 'The EXAMPLES section must include the\n{exampleList} variable.',
      })
    }

    // Parse examples if present (legacy support or if manual edits added them)
    // For new format, examples are stored in graph settings, so this will likely be empty or just {exampleList}
    let examples: RetrievalExample[] = []
    if (examplesSection && !examplesSection.includes('{exampleList}')) {
      examples = parseExamplesSection(examplesSection)
    }

    const config: RetrievalConfig = {
      promptSections: {
        persona: persona || '',
        instructions: instructions || '',
        additionalOutputInstructions: additionalOutputInstructions || '',
      },
      temperature: existingConfig?.temperature ?? 0.7,
      topP: existingConfig?.topP ?? 0.9,
      model: existingConfig?.model,
      examples,
      enabledTools: existingConfig?.enabledTools || [],
    }

    if (errors.length > 0) {
      return {
        success: false,
        data: config,
        errors,
        warnings,
      }
    }

    return {
      success: true,
      data: config,
      errors: [],
      warnings,
    }
  } catch (error) {
    return {
      success: false,
      errors: [
        {
          type: 'parse_error',
          message: 'Failed to parse prompt template',
          details: error instanceof Error ? error.message : String(error),
        },
      ],
      warnings,
    }
  }
}

// ================================
// Variant Helpers
// ================================

/**
 * Create a variant name for a specific graph
 */
export function createGraphVariantName(graphId: string): string {
  return `graph_${graphId.replace(/-/g, '_')}`
}

/**
 * Find a variant by name in the template
 */
export function findVariant(template: PromptTemplate, variantName: string): PromptTemplateVariant | undefined {
  return template.variants.find((v) => v.variant === variantName)
}

/**
 * Create a new variant from config
 */
export function createVariantFromConfig(
  variantName: string,
  config: RetrievalConfig,
  baseVariant?: PromptTemplateVariant,
  displayName?: string,
  description?: string
): ConversionResult<PromptTemplateVariant> {
  const promptResult = configToPrompt(config)

  if (!promptResult.success || !promptResult.data) {
    return {
      success: false,
      errors: promptResult.errors,
      warnings: promptResult.warnings,
    }
  }

  const variant: PromptTemplateVariant = {
    variant: variantName,
    text: promptResult.data,
    temperature: config.temperature,
    topP: config.topP,
    system_name_for_model: config.model || baseVariant?.system_name_for_model,
    retrieve: baseVariant?.retrieve,
    description: description || `Configuration for variant ${variantName}`,
    ...(displayName ? { display_name: displayName } : baseVariant?.display_name ? { display_name: baseVariant.display_name } : {}),
  }

  return {
    success: true,
    data: variant,
    errors: [],
    warnings: promptResult.warnings,
  }
}

/**
 * Validate that a prompt template has the required structure
 */
export function validatePromptStructure(promptText: string): ConversionResult<boolean> {
  const errors: ValidationError[] = []
  const warnings: string[] = []

  // Check for section markers
  const requiredSections: (keyof typeof SECTION_MARKERS)[] = [
    'PERSONA',
    'GENERAL_INSTRUCTIONS',
    'EXIT_INSTRUCTIONS',
    'OUTPUT_INSTRUCTIONS',
    'EXAMPLES',
  ]

  for (const section of requiredSections) {
    const markers = SECTION_MARKERS[section]
    const hasStart = promptText.includes(markers.start)
    const hasEnd = promptText.includes(markers.end)

    if (!hasStart) {
      errors.push({
        type: 'missing_section',
        message: `Missing ${section} section start`,
        section,
        details: `Expected marker: ${markers.start}`,
      })
    }

    if (!hasEnd) {
      errors.push({
        type: 'missing_section',
        message: `Missing ${section} section end`,
        section,
        details: `Expected marker: ${markers.end}`,
      })
    }
  }

  const exitInstructions = extractSection(promptText, 'EXIT_INSTRUCTIONS')
  if (exitInstructions && !exitInstructions.includes('{exitInstructions}')) {
    errors.push({
      type: 'missing_section',
      message: 'Variable {exitInstructions} is missing',
      details: 'The EXIT INSTRUCTIONS section must include the {exitInstructions} variable.',
    })
  }

  const outputInstructions = extractSection(promptText, 'OUTPUT_INSTRUCTIONS')
  if (outputInstructions && !outputInstructions.includes('{outputInstructions}')) {
    errors.push({
      type: 'missing_section',
      message: 'Variable {outputInstructions} is missing',
      details: 'The OUTPUT INSTRUCTIONS section must include the {outputInstructions} variable.',
    })
  }

  const examplesSection = extractSection(promptText, 'EXAMPLES')
  if (examplesSection && !examplesSection.includes('{exampleList}')) {
    errors.push({
      type: 'missing_section',
      message: 'Variable {exampleList} is missing',
      details: 'The EXAMPLES section must include the {exampleList} variable.',
    })
  }

  return {
    success: errors.length === 0,
    data: errors.length === 0,
    errors,
    warnings,
  }
}

// ================================
// Error Message Helpers
// ================================

/**
 * Get user-friendly error message with guidance
 */
export function getErrorGuidance(error: ValidationError): string {
  switch (error.type) {
    case 'missing_section':
      const markers =
        error.section && SECTION_MARKERS[error.section as keyof typeof SECTION_MARKERS]
          ? SECTION_MARKERS[error.section as keyof typeof SECTION_MARKERS]
          : { start: '<!-- SECTION START -->', end: '<!-- SECTION END -->' }

      return `
**${error.message}**

Your prompt template must include the following section:

\`\`\`
${markers.start}
Your content here...
${markers.end}
\`\`\`

${error.details || ''}
      `.trim()

    case 'invalid_section':
      return `
**${error.message}**

${error.details || ''}

Make sure all sections have matching start markers.
      `.trim()

    case 'parse_error':
      return `
**${error.message}**

${error.details || 'An unexpected error occurred while parsing the prompt.'}

Please check the prompt format and try again.
      `.trim()

    case 'not_found':
      return `
**${error.message}**

${error.details || 'The requested resource could not be found.'}
      `.trim()

    case 'incompatible':
      return `
**${error.message}**

${error.details || 'The prompt format is not compatible with the current configuration.'}

Please ensure your prompt follows the required structure with section markers.
      `.trim()

    default:
      return error.message
  }
}
