import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript";

import { SyntaxHighlighter } from "@/components/ui/CodeBlock";

// Grammars only the analyzer needs live in its lazy chunk, so the landing page never loads them.
SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("typescript", typescript);
