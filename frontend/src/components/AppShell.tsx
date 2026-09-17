"use client";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

const navItems = [
  { name: "Dashboard", href: "/", icon: "▦" },
  { name: "Products", href: "/products", icon: "□" },
  { name: "Uploads", href: "/uploads", icon: "⇧" },
  { name: "Review Queue", href: "/review", icon: "✓" },
  { name: "Variants", href: "/variants", icon: "◇" },
  { name: "Amazon Mapping", href: "/mapping", icon: "↔" },
  { name: "Validation", href: "/validation", icon: "✓" },
  { name: "Schemas", href: "/schemas", icon: "▤" },
  { name: "Attributes", href: "/attributes", icon: "☷" },
  { name: "Submission History", href: "/submissions", icon: "◷" },
  { name: "Settings", href: "/settings", icon: "⚙" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [theme, setTheme] = useState("system");
  const [font, setFont] = useState(12);
  const pathname = usePathname();

  useEffect(() => {
    const t = localStorage.getItem("khagatara-theme") ?? "system";
    const f = Number(localStorage.getItem("khagatara-font-size") ?? 12);
    const c = localStorage.getItem("khagatara-sidebar") === "collapsed";
    setTheme(t);
    setFont(f);
    setCollapsed(c);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.setProperty("--ui-font-size", `${font}px`);
    localStorage.setItem("khagatara-theme", theme);
    localStorage.setItem("khagatara-font-size", String(font));
    localStorage.setItem("khagatara-sidebar", collapsed ? "collapsed" : "expanded");
  }, [theme, font, collapsed]);

  return (
    <div className={`shell ${collapsed ? "collapsed" : ""}`}>
      <aside>
        <div className="brand">{collapsed ? "K" : "KHAGATARA"}</div>
        <button className="icon" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">
          ☰
        </button>
        <nav>
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                className={isActive ? "active" : ""}
                href={item.href}
                key={item.name}
                title={item.name}
              >
                <span>{item.icon}</span>
                {!collapsed && item.name}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main>
        <header>
          <div className="crumb">
            Listing Automation <span>• Local workspace</span>
          </div>
          <div className="tools">
            <label>
              Theme{" "}
              <select value={theme} onChange={(e) => setTheme(e.target.value)}>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
            </label>
            <button className="font" onClick={() => setFont(Math.max(9, font - 1))} aria-label="Reduce font">
              A−
            </button>
            <select
              aria-label="Font size"
              value={font}
              onChange={(e) => setFont(Number(e.target.value))}
            >
              {Array.from({ length: 10 }, (_, i) => i + 9).map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
            <button className="font" onClick={() => setFont(Math.min(18, font + 1))} aria-label="Increase font">
              A+
            </button>
            <button className="avatar" aria-label="User menu">
              K
            </button>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}

