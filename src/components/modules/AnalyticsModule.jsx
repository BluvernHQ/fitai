import { BarChart3 } from "lucide-react";

export function AnalyticsModule() {
  return (
    <div className="page-shell page-shell-md text-white">
      <div className="rounded-3xl border border-white/8 bg-white/3 p-6 md:p-12 text-center">
        <BarChart3 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <h1 className="text-2xl font-bold mb-2">Analytics</h1>
        <p className="text-zinc-400 max-w-md mx-auto text-sm leading-relaxed">
          Enable this module from Admin → Modules when ready. Charts for FMS trends, block completion,
          and 1RM progression will plug in here.
        </p>
      </div>
    </div>
  );
}
