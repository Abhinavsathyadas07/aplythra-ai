export function ComingSoon({ title, phase, children }: { title: string; phase: string; children: string }) {
  return (
    <section>
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <div className="mt-6 rounded-xl border border-dashed border-border bg-card p-6">
        <p className="text-sm font-medium text-accent">Planned for {phase}</p>
        <p className="mt-2 text-sm text-muted">{children}</p>
      </div>
    </section>
  );
}
