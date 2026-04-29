import Link from "next/link";
import { ArrowLeft } from "lucide-react";

interface Props {
  href: string;
  label: string;
}

export default function BackLink({ href, label }: Props) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
    >
      <ArrowLeft className="h-4 w-4" />
      {label}
    </Link>
  );
}
