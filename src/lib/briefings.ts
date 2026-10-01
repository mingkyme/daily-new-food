/** Read the product headings used by existing formats of the Markdown briefs. */
export function productHighlights(body = ''): string[] {
  return body.split('\n').flatMap((line) => {
    const match = line.match(/^###\s+(.+)$/) ?? line.match(/^(?:- |\d+\. )\*\*(.+?)\*\*\s*$/);
    if (!match || !match[1].includes(' — ')) return [];
    return [match[1].replace(/^\d+\.\s*/, '').replace(/\s*\([^)]*\)\s*$/, '').trim()];
  }).slice(0, 3);
}
