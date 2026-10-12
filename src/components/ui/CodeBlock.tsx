import type { CSSProperties, HTMLProps } from "react";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import SyntaxHighlighter from "react-syntax-highlighter/dist/esm/prism-light";
import nightOwl from "react-syntax-highlighter/dist/esm/styles/prism/night-owl";

import type { CodeLanguage } from "@/types/content";

// The light build ships without grammars. Registering only the ones the landing page renders
// keeps the highlighter ~1 MB smaller than the default all-languages import. The analyzer
// registers the rest in its own lazily loaded chunk.
SyntaxHighlighter.registerLanguage("jsx", jsx);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("bash", bash);

export { SyntaxHighlighter };

interface CodeBlockProps {
  code: string;
  language: CodeLanguage;
  style?: CSSProperties;
  showLineNumbers?: boolean;
  /** Per-line props (e.g. a highlight class); enables line wrapping when given. */
  getLineProps?: (lineNumber: number) => HTMLProps<HTMLElement>;
}

export function CodeBlock({
  code,
  language,
  style,
  showLineNumbers,
  getLineProps,
}: CodeBlockProps) {
  return (
    <SyntaxHighlighter
      language={language}
      style={nightOwl}
      customStyle={{ margin: 0, textAlign: "left", ...style }}
      codeTagProps={{
        style: { fontFamily: "inherit", fontSize: "inherit", whiteSpace: "inherit" },
      }}
      showLineNumbers={showLineNumbers ?? false}
      {...(getLineProps && { wrapLines: true, lineProps: getLineProps })}
    >
      {code}
    </SyntaxHighlighter>
  );
}
