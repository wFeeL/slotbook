// miniapp/src/features/admin-staff/WorkingHoursEditor.tsx
import { useEffect, useState } from 'react';
import { Toggle } from '@/shared/ui/Toggle';
import { Button } from '@/shared/ui/Button';
import { cn } from '@/shared/lib/cn';
import type { WorkingHoursEntry } from '@/shared/api/types';

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

function normalizeTime(t: string): string {
  // HH:MM:SS → HH:MM for input value
  return t.length >= 5 ? t.slice(0, 5) : t;
}

interface WorkingHoursEditorProps {
  initial: WorkingHoursEntry[];
  onSave(entries: WorkingHoursEntry[]): void;
  saving: boolean;
}

export function WorkingHoursEditor({ initial, onSave, saving }: WorkingHoursEditorProps) {
  const [rows, setRows] = useState<WorkingHoursEntry[]>(() => buildRows(initial));

  useEffect(() => {
    setRows(buildRows(initial));
  }, [initial]);

  function update(index: number, patch: Partial<WorkingHoursEntry>) {
    setRows((rs) => rs.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  function handleSave() {
    const out = rows
      .filter((r) => r.is_active)
      .map((r) => ({
        ...r,
        start_time: r.start_time.length === 5 ? `${r.start_time}:00` : r.start_time,
        end_time: r.end_time.length === 5 ? `${r.end_time}:00` : r.end_time,
      }));
    onSave(out);
  }

  return (
    <div className="flex flex-col gap-3">
      {rows.map((row, i) => (
        <div
          key={row.weekday}
          className={cn(
            'flex items-center gap-3 rounded-2xl bg-shell p-3 border border-sand',
            !row.is_active && 'opacity-50',
          )}
        >
          <div className="w-8 text-sienna text-sm font-semibold">{WEEKDAYS[row.weekday]}</div>
          <Toggle checked={row.is_active} onChange={(v) => update(i, { is_active: v })} />
          <input
            type="time"
            value={normalizeTime(row.start_time)}
            onChange={(e) => update(i, { start_time: e.target.value })}
            disabled={!row.is_active}
            className="flex-1 rounded-xl border border-sand bg-cream px-2 py-1.5 text-ink text-sm"
          />
          <span className="text-sienna">–</span>
          <input
            type="time"
            value={normalizeTime(row.end_time)}
            onChange={(e) => update(i, { end_time: e.target.value })}
            disabled={!row.is_active}
            className="flex-1 rounded-xl border border-sand bg-cream px-2 py-1.5 text-ink text-sm"
          />
        </div>
      ))}
      <Button onClick={handleSave} disabled={saving}>
        {saving ? '...' : 'Сохранить'}
      </Button>
    </div>
  );
}

function buildRows(initial: WorkingHoursEntry[]): WorkingHoursEntry[] {
  const byWeekday = new Map(initial.map((e) => [e.weekday, e]));
  return WEEKDAYS.map((_, wd) => {
    const existing = byWeekday.get(wd);
    if (existing) {
      return {
        weekday: wd,
        start_time: normalizeTime(existing.start_time),
        end_time: normalizeTime(existing.end_time),
        is_active: existing.is_active,
      };
    }
    return { weekday: wd, start_time: '10:00', end_time: '18:00', is_active: false };
  });
}
