/** Only same-origin relative paths are accepted as post-login destinations. */
export function safeNextPath(next: string | null) {
  return next && next.startsWith('/') && !next.startsWith('//') && !next.startsWith('/\\') ? next : '/'
}
