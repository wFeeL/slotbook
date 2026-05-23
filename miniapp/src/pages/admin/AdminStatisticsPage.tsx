import { useState } from 'react';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Sheet } from '@/shared/ui/Sheet';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { useStatistics } from '@/entities/admin-statistics/api';
import { getAuthToken } from '@/shared/api/client';
import { api } from '@/shared/api/endpoints';
import { pushToast } from '@/shared/store/toast-store';
import type { StatisticsPeriodT } from '@/shared/api/types';
import { cn } from '@/shared/lib/cn';

const PERIODS: { value: StatisticsPeriodT; label: string }[] = [
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
  { value: '90d', label: '90 дней' },
  { value: '365d', label: 'Год' },
];

async function downloadAuthed(url: string, filename: string) {
  const token = getAuthToken();
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(objectUrl);
}

function BarRow({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-1/3 text-sm text-ink truncate">{label}</div>
      <div className="flex-1 bg-sand/40 rounded-full h-3 relative">
        <div className="bg-rose rounded-full h-3" style={{ width: `${pct}%` }} />
      </div>
      <div className="w-10 text-right text-sm text-sienna">{value}</div>
    </div>
  );
}

function Sparkline({ data }: { data: number[] }) {
  if (data.length === 0) return null;
  const max = Math.max(...data, 1);
  const W = 240;
  const H = 40;
  const step = W / Math.max(data.length - 1, 1);
  const points = data.map((v, i) => `${i * step},${H - (v / max) * H}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-10">
      <polyline points={points} fill="none" stroke="var(--color-rose)" strokeWidth={2} />
    </svg>
  );
}

export function AdminStatisticsPage() {
  const [period, setPeriod] = useState<StatisticsPeriodT>('30d');
  const [exportOpen, setExportOpen] = useState(false);
  const [format, setFormat] = useState<'csv' | 'xlsx'>('csv');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const q = useStatistics(period);
  const data = q.data;
  const max_services = Math.max(
    ...(data?.top_services ?? []).map((s) => s.completed_count),
    1,
  );
  const max_staff = Math.max(...(data?.top_staff ?? []).map((s) => s.completed_count), 1);

  async function doExport() {
    try {
      const url =
        format === 'csv'
          ? api.admin.exportCsvUrl({ from: from || undefined, to: to || undefined })
          : api.admin.exportXlsxUrl({ from: from || undefined, to: to || undefined });
      const ext = format;
      await downloadAuthed(url, `slotbook-bookings.${ext}`);
      pushToast('success', 'Загружено');
      setExportOpen(false);
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Статистика</h2>
        <Button size="md" variant="secondary" onClick={() => setExportOpen(true)}>
          Экспорт
        </Button>
      </header>

      <div className="flex gap-2 overflow-x-auto -mx-5 px-5">
        {PERIODS.map((p) => (
          <button
            key={p.value}
            type="button"
            onClick={() => setPeriod(p.value)}
            className={cn(
              'rounded-full px-3 py-1 text-sm font-semibold whitespace-nowrap',
              period === p.value
                ? 'bg-rose text-shell'
                : 'bg-shell border border-sand text-sienna',
            )}
          >
            {p.label}
          </button>
        ))}
      </div>

      {q.isLoading && <Skeleton height={300} />}
      {data && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase">Выручка</div>
              <div className="text-2xl text-ink font-display">{data.revenue} ₽</div>
            </Card>
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase">Всего записей</div>
              <div className="text-2xl text-ink font-display">{data.total_bookings}</div>
            </Card>
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase">Завершено</div>
              <div className="text-2xl text-ink font-display">{data.completed_count}</div>
            </Card>
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase">Не пришли</div>
              <div className="text-2xl text-ink font-display">{data.no_show_count}</div>
            </Card>
            <Card surface="shell" className="col-span-2">
              <div className="text-sienna text-xs uppercase">Доля отмен</div>
              <div className="text-2xl text-ink font-display">
                {(data.cancellation_rate * 100).toFixed(1)}%
              </div>
            </Card>
          </div>

          {data.daily_volume.length > 0 && (
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase mb-2">Записи по дням</div>
              <Sparkline data={data.daily_volume.map((d) => d.bookings_count)} />
            </Card>
          )}

          {data.top_services.length > 0 && (
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase mb-2">Топ услуг</div>
              <div className="flex flex-col gap-2">
                {data.top_services.map((s) => (
                  <BarRow
                    key={s.service_id}
                    label={s.service_title}
                    value={s.completed_count}
                    max={max_services}
                  />
                ))}
              </div>
            </Card>
          )}

          {data.top_staff.length > 0 && (
            <Card surface="shell">
              <div className="text-sienna text-xs uppercase mb-2">Топ сотрудников</div>
              <div className="flex flex-col gap-2">
                {data.top_staff.map((s) => (
                  <BarRow
                    key={s.staff_id}
                    label={s.staff_name}
                    value={s.completed_count}
                    max={max_staff}
                  />
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      <Sheet open={exportOpen} onClose={() => setExportOpen(false)} title="Экспорт записей">
        <div className="flex flex-col gap-3">
          <Select
            label="Формат"
            value={format}
            onChange={(e) => setFormat(e.target.value as 'csv' | 'xlsx')}
          >
            <option value="csv">CSV</option>
            <option value="xlsx">XLSX</option>
          </Select>
          <Input label="С" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          <Input label="По" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          <Button onClick={doExport}>Скачать</Button>
        </div>
      </Sheet>
    </div>
  );
}
