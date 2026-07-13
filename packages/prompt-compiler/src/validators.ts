// SPDX-License-Identifier: MIT

export function validatePrompt(prompt: string, maxLength: number): string[] {
  const warnings: string[] = [];

  if (prompt.length === 0) {
    warnings.push('Prompt is empty');
  }

  if (prompt.length > maxLength) {
    warnings.push(`Prompt too long: ${prompt.length} > ${maxLength}`);
  }

  // Check for unclosed variable placeholders
  const unclosed = prompt.match(/\{\{[^}]*$/g);
  if (unclosed) {
    warnings.push(`Unclosed template variables: ${unclosed.length}`);
  }

  return warnings;
}

export function sanitizePrompt(prompt: string): string {
  return prompt
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '') // strip control chars
    .replace(/\s+/g, ' ')                             // collapse whitespace
    .replace(/\.+/g, '.')                             // collapse dots
    .replace(/,+/g, ',')                              // collapse commas
    .trim();
}
