"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  BarChart3,
  CloudSun,
  Compass,
  Droplets,
  History,
  LayoutDashboard,
  Lightbulb,
  LogOut,
  Map,
  Menu,
  Scale,
  Settings,
  Sparkles,
  Sprout,
  Wallet,
  Waves,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { auth } from "@/lib/api/client";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV: { group: string; items: NavItem[] }[] = [
  {
    group: "Home",
    items: [{ href: "/dashboard", label: "Farmer Dashboard", icon: LayoutDashboard }],
  },
  {
    group: "Choose a Crop",
    items: [
      { href: "/predict", label: "I Know My Crop", icon: Sprout },
      { href: "/help-me-choose", label: "Help Me Choose", icon: Compass },
    ],
  },
  {
    group: "My Farm",
    items: [
      { href: "/farms", label: "Farm & Location", icon: Map },
      { href: "/crops", label: "Crop Guides", icon: Sprout },
    ],
  },
  {
    group: "Water & Advice",
    items: [
      { href: "/irrigation", label: "Irrigation Scheduling", icon: Waves },
      { href: "/predictions", label: "Water Need History", icon: History },
      { href: "/weather", label: "Local Field Weather", icon: CloudSun },
      { href: "/advisory", label: "Farmer Advisory", icon: Lightbulb },
      { href: "/water-budget", label: "Water Budget", icon: Wallet },
    ],
  },
  {
    group: "Research & Profile",
    items: [
      { href: "/water-productivity", label: "Crop per Drop", icon: Scale },
      { href: "/analytics", label: "Research & Analytics", icon: BarChart3 },
      { href: "/settings", label: "Farmer Profile", icon: Settings },
    ],
  },
];

const MOBILE_BOTTOM_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/predict", label: "Predict", icon: Droplets },
  { href: "/irrigation", label: "Irrigation", icon: Waves },
  { href: "/advisory", label: "Advisory", icon: Lightbulb },
  { href: "/crops", label: "Crops", icon: Sprout },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/dashboard") return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Main Navigation" className="space-y-5">
      {NAV.map(({ group, items }) => (
        <div key={group}>
          <p className="px-3 pb-1.5 text-[10px] font-black uppercase tracking-wider text-emerald-800/80">
            {group}
          </p>
          <ul className="space-y-1">
            {items.map(({ href, label, icon: Icon, badge }) => {
              const active = isActive(pathname, href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex min-h-10 items-center justify-between rounded-xl px-3 py-2 text-sm font-semibold transition-all",
                      active
                        ? "bg-primary text-white shadow-sm shadow-emerald-950/10"
                        : "text-emerald-950/70 hover:bg-emerald-100/60 hover:text-emerald-950",
                    )}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon className={cn("size-4 shrink-0", active ? "text-white" : "text-emerald-700")} />
                      <span className="truncate">{label}</span>
                    </div>
                    {badge && (
                      <span
                        className={cn(
                          "text-[10px] font-bold px-1.5 py-0.2 rounded-full",
                          active
                            ? "bg-white/20 text-white"
                            : "bg-emerald-100 text-emerald-800"
                        )}
                      >
                        {badge}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function SignOutButton({ className }: { className?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function signOut() {
    setBusy(true);
    try {
      await auth.logout();
    } finally {
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={signOut}
      loading={busy}
      loadingText="Signing out…"
      className={cn("w-full justify-start text-xs font-bold border border-emerald-200 text-emerald-900 bg-emerald-50 hover:bg-emerald-100", className)}
    >
      <LogOut className="size-3.5 mr-2 text-emerald-700" />
      Sign Out
    </Button>
  );
}

export function AppShell({
  children,
  farmerName,
}: {
  children: React.ReactNode;
  farmerName: string;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-dvh bg-background text-foreground flex flex-col pb-16 lg:pb-0">
      {/* Mobile Top Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-emerald-200 bg-white/95 backdrop-blur-md px-4 py-3 lg:hidden shadow-xs">
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            className="rounded-xl p-1.5 text-foreground hover:bg-emerald-100/70"
          >
            {menuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
            <span className="sr-only">
              {menuOpen ? "Close menu" : "Open menu"}
            </span>
          </button>
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="size-8 rounded-xl bg-gradient-to-tr from-primary to-teal-400 flex items-center justify-center text-white shadow-xs">
              <Droplets className="size-4" />
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-tight text-emerald-950">Jalachakra</span>
              <span className="text-[10px] text-emerald-800 ml-1 font-bold">ಜಲಚಕ್ರ</span>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-emerald-900 truncate max-w-[120px]">
            {farmerName.split(" ")[0]}
          </span>
          <div className="size-7 rounded-full bg-emerald-100 border border-emerald-300 text-primary font-bold text-xs flex items-center justify-center">
            {farmerName.charAt(0)}
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      {menuOpen && (
        <div
          id="mobile-nav"
          className="border-b border-emerald-200 bg-white px-4 py-4 lg:hidden max-h-[85vh] overflow-y-auto space-y-4 shadow-lg z-20"
        >
          {/* Primary CTA in Mobile Menu */}
          <Link
            href="/predict"
            onClick={() => setMenuOpen(false)}
            className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl bg-primary text-white text-sm font-bold shadow-md shadow-emerald-900/10 mb-3"
          >
            <Droplets className="size-4" />
            <span>Predict Water Need</span>
          </Link>

          <NavLinks onNavigate={() => setMenuOpen(false)} />
          <div className="pt-3 border-t border-emerald-100 space-y-2">
            <p className="text-xs text-muted-foreground">Logged in as {farmerName}</p>
            <SignOutButton />
          </div>
        </div>
      )}

      {/* Desktop App Layout */}
      <div className="mx-auto flex w-full max-w-7xl flex-1">
        {/* Desktop Sidebar */}
        <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-emerald-200 bg-white px-3.5 py-5 lg:flex shadow-xs">
          <Link href="/" className="mb-5 flex items-center gap-2.5 px-2 group">
            <div className="size-10 rounded-2xl bg-gradient-to-tr from-primary to-teal-400 flex items-center justify-center text-white shadow-md shadow-emerald-900/10 transition-transform group-hover:scale-105">
              <Droplets className="size-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-emerald-950">Jalachakra</span>
                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                  ಜಲಚಕ್ರ
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground leading-none mt-0.5">Farm · Water · Advisory</p>
            </div>
          </Link>

          {/* Primary CTA Button */}
          <div className="mb-5 px-1">
            <Link
              href="/predict"
              className="flex items-center justify-center gap-2 w-full py-2.5 px-3 rounded-xl bg-primary hover:bg-emerald-800 text-white text-xs font-bold shadow-md shadow-emerald-900/10 transition-all group"
            >
              <Droplets className="size-4 text-emerald-200 group-hover:scale-110 transition-transform" />
              <span>Predict Water Need</span>
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin">
            <NavLinks />
          </div>

          {/* User Profile & Sign Out footer in sidebar */}
          <div className="mt-4 space-y-2.5 border-t border-emerald-100 px-2 pt-4">
            <div className="flex items-center gap-2.5">
              <div className="size-8 rounded-full bg-emerald-100 border border-emerald-300 text-primary font-bold text-xs flex items-center justify-center">
                {farmerName.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-bold text-emerald-950">{farmerName}</p>
                <p className="text-[10px] text-emerald-700 font-semibold">Registered Farmer</p>
              </div>
            </div>
            <SignOutButton />
          </div>
        </aside>

        {/* Main Workspace Content */}
        <main id="main" className="flex-1 min-w-0 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
          {children}
        </main>
      </div>

      {/* Mobile Sticky Bottom Navigation Bar (Convenient thumb reach outdoors) */}
      <nav
        aria-label="Mobile Quick Navigation"
        className="fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur-md border-t border-emerald-200 px-2 py-1.5 flex items-center justify-around lg:hidden shadow-lg"
      >
        {MOBILE_BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center py-1 px-3 rounded-xl text-[10px] font-bold transition-colors min-w-[56px]",
                active
                  ? "text-primary"
                  : "text-muted-foreground hover:text-emerald-900"
              )}
            >
              <div
                className={cn(
                  "p-1 rounded-lg transition-all",
                  active ? "bg-emerald-100 text-primary" : "text-muted-foreground"
                )}
              >
                <Icon className="size-4" />
              </div>
              <span className="mt-0.5 leading-tight">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
