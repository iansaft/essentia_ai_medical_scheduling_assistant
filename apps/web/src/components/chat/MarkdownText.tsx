import type { ReactNode } from "react";
import Markdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";

type MarkdownTextProps = {
  content: string;
  className?: string;
};

function MarkdownLink({
  href,
  children,
}: {
  href?: string;
  children?: ReactNode;
}) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

export function MarkdownText({ content, className }: MarkdownTextProps) {
  return (
    <div className={className}>
      <Markdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={{ a: MarkdownLink }}
      >
        {content}
      </Markdown>
    </div>
  );
}
