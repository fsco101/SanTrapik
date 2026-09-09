import React from "react";

export interface QuickCorridorItem {
  code: string;
  name: string;
  origin: { name: string; lat: number; lng: number };
  destination: { name: string; lat: number; lng: number };
}

export const CORRIDORS: QuickCorridorItem[] = [
  {
    code: "EDSA",
    name: "QC → Makati",
    origin: { name: "Quezon City Circle", lat: 14.6515, lng: 121.0494 },
    destination: { name: "Ayala Triangle, Makati", lat: 14.5573, lng: 121.0234 }
  },
  {
    code: "C-5",
    name: "QC → BGC",
    origin: { name: "Katipunan, QC", lat: 14.6465, lng: 121.0755 },
    destination: { name: "Market Market, BGC", lat: 14.5450, lng: 121.0570 }
  },
  {
    code: "R-7",
    name: "Fairview → Manila",
    origin: { name: "Fairview Center, QC", lat: 14.7125, lng: 121.0780 },
    destination: { name: "UST, España, Manila", lat: 14.6095, lng: 120.9890 }
  },
  {
    code: "EDSA",
    name: "Caloocan → Pasay",
    origin: { name: "Monumento, Caloocan", lat: 14.6575, lng: 120.9998 },
    destination: { name: "MOA, Pasay", lat: 14.5330, lng: 120.9835 }
  }
];

interface QuickCorridorsProps {
  activeCorridorName: string | null;
  onSelect: (item: QuickCorridorItem) => void;
}

export const QuickCorridors: React.FC<QuickCorridorsProps> = ({ activeCorridorName, onSelect }) => {
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
      <span className="text-[10px] uppercase tracking-wider font-bold text-text-muted font-mono whitespace-nowrap pl-1">
        Quick:
      </span>
      {CORRIDORS.map((c) => {
        const isActive = activeCorridorName === c.name;
        return (
          <button
            key={c.name}
            onClick={() => onSelect(c)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono whitespace-nowrap transition border ${
              isActive
                ? "bg-indigo-950/60 border-ai-primary text-white shadow-ai-aura"
                : "bg-surface-card hover:bg-surface-elevated border-white/5 text-text-secondary hover:text-white"
            }`}
          >
            <span className="text-[10px] text-ai-cyan font-bold">[{c.code}]</span>
            <span>{c.name}</span>
          </button>
        );
      })}
    </div>
  );
};
