interface Segment {
  offset: number;
  text: string;
  isCode: boolean;
}

/** codegrade marks identifiers with backticks: "`var` is function-scoped". */
function toSegments(message: string): Segment[] {
  const segments: Segment[] = [];
  let offset = 0;
  message.split("`").forEach((text, position) => {
    if (text) segments.push({ offset, text, isCode: position % 2 === 1 });
    offset += text.length + 1;
  });
  return segments;
}

export function RichMessage({ text }: { text: string }) {
  return (
    <>
      {toSegments(text).map((segment) =>
        segment.isCode ? (
          <code
            key={segment.offset}
            className="rounded bg-white/10 px-1 py-0.5 font-mono text-[0.85em] text-gray-100"
          >
            {segment.text}
          </code>
        ) : (
          <span key={segment.offset}>{segment.text}</span>
        ),
      )}
    </>
  );
}
