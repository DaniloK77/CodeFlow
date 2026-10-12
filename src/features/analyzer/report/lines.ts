export { FILE_LEVEL_RULES, lineOf } from "@/lib/findings";

/** DOM id of one line in the code view, so a finding can scroll to it. */
export const lineAnchorId = (line: number) => `code-line-${line}`;

/** What the code view should flash. `nonce` changes on every click, even on the same line. */
export interface ActiveLine {
  line: number;
  nonce: number;
}
