import type { ReactNode } from "react";

interface Props {
  label: string;
  value: string | ReactNode;
}

export default function DetailField({ label, value }: Props) {
  return (
    <div className="space-y-1">
      <p className="text-sm text-muted-foreground">{label}</p>
      <div className="text-sm font-medium text-stone-800">{value}</div>
    </div>
  );
}
