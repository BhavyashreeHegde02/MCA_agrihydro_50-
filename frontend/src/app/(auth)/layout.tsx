import Link from "next/link";
import { Droplets, Sprout } from "lucide-react";

export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground selection:bg-emerald-200 selection:text-emerald-900">
      {/* Top Bar with Brand Link */}
      <header className="border-b border-emerald-200/80 bg-white/80 backdrop-blur-md px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="size-9 rounded-xl bg-gradient-to-tr from-primary to-teal-500 flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105">
              <Droplets className="size-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-emerald-950">
                  JALACHAKRA
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                  ಜಲಚಕ್ರ
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground leading-none">Farm · Water · Advisory</p>
            </div>
          </Link>

          <Link
            href="/"
            className="text-xs font-semibold text-emerald-900 hover:text-primary transition-colors flex items-center gap-1"
          >
            &larr; Back to Overview
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <main id="main" className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-10">
        <div className="w-full max-w-5xl">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-emerald-200/80 bg-white/80 py-4 px-4 text-center text-xs text-muted-foreground">
        <p>
          Jalachakra Agricultural Decision Support · FAO-56 Penman-Monteith crop water estimates are advisory to assist farmer field observation.
        </p>
      </footer>
    </div>
  );
}
