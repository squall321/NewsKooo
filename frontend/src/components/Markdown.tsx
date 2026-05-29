import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

/** Themed markdown renderer for report bodies (`body_md`). */
export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div
      className={cn(
        "max-w-none text-sm leading-relaxed text-foreground/90",
        "[&_h1]:mb-3 [&_h1]:mt-1 [&_h1]:text-2xl [&_h1]:font-semibold [&_h1]:tracking-tight",
        "[&_h2]:mb-2 [&_h2]:mt-6 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:tracking-tight",
        "[&_h3]:mb-2 [&_h3]:mt-4 [&_h3]:text-base [&_h3]:font-semibold",
        "[&_p]:my-3",
        "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-1",
        "[&_a]:text-primary [&_a]:underline [&_a]:underline-offset-2",
        "[&_strong]:font-semibold [&_strong]:text-foreground",
        "[&_blockquote]:my-3 [&_blockquote]:border-l-2 [&_blockquote]:border-primary/50 [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:text-muted-foreground",
        "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs",
        "[&_pre]:my-3 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-muted [&_pre]:p-3",
        "[&_table]:my-3 [&_table]:w-full [&_table]:border-collapse [&_table]:text-sm",
        "[&_th]:border [&_th]:border-border [&_th]:bg-muted/50 [&_th]:px-3 [&_th]:py-1.5 [&_th]:text-left [&_th]:font-medium",
        "[&_td]:border [&_td]:border-border [&_td]:px-3 [&_td]:py-1.5",
        "[&_hr]:my-5 [&_hr]:border-border",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
