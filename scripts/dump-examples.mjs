// Prints the assignment examples as JSON, so Python tooling can use the same source of truth.
// Run with: node --experimental-strip-types scripts/dump-examples.mjs
const { ASSIGNMENT_EXAMPLES } = await import("../src/content/examples.ts");
process.stdout.write(JSON.stringify(ASSIGNMENT_EXAMPLES));
