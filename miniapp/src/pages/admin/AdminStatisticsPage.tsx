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
import { getWebApp } from '@/shared/telegram/webapp';
import { pushToast } from '@/shared/store/toast-store';
import type { StatisticsPeriodT } from '@/shared/api/types';
import { cn } from '@/shared/lib/cn';

const PERIODS: { value: StatisticsPeriodT; label: string }[] = [
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
  { value: '90d', label: '90 дней' },
  { value: '365d', label: 'Год' },
];

function absoluteUrl(pathOrUrl: string): string {
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  return `${window.location.origin}${pathOrUrl}`;
}

/**
 * Download an authenticated file. Strategy:
 *
 * 1. iOS / Android in Telegram → mint a 60-second download-scoped ticket
 *    server-side, then `Telegram.WebApp.openLink(absURL?ticket=<short-jwt>)`.
 *    The ticket has `purpose=export` and binds kind+params, so leaking the URL
 *    via Referer/logs cannot be replayed against any other endpoint and
 *    expires within seconds.
 * 2. Desktop / non-Telegram → fetch with Authorization header → blob → anchor.
 */
async function downloadAuthed(
  url: string,
  filename: string,
  kind: 'csv' | 'xlsx',
  params: { from?: string; to?: string; staff_id?: number },
): Promise<void> {
  const token = getAuthToken();
  const tg = getWebApp();
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
  const isAndroid = /Android/i.test(navigator.userAgent);

  if (tg && (isIOS || isAndroid) && typeof tg.openLink === 'function' && token) {
    const { ticket } = await api.admin.issueExportTicket({
      kind,
      date_from: params.from ?? null,
      date_to: params.to ?? null,
      staff_id: params.staff_id ?? null,
    });
    const sep = url.includes('?') ? '&' : '?';
    const fullUrl = `${absoluteUrl(url)}${sep}ticket=${encodeURIComponent(ticket)}`;
    tg.openLink(fullUrl);
    return;
  }

  // Desktop / non-Telegram fallback — blob + anchor click.
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) {
    throw new Error(`Не удалось скачать (HTTP ${res.status})`);
  }
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  anchorDownload(objectUrl, filename);
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}

function anchorDownload(objectUrl: string, filename: string) {
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function BarRow({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-1/3 text-sm text-ink truncate">{label}</div>
      <div className="flex-1 bg-sand/40 rounded-full h-3 relative">
        <div className="bg-rose rounded-full h-3" style={{ width: `${pct}%` }} />
      </div>
      <div className="w-10 text-right text-sm text-sienna-deep">{value}</div>
    </div>
  );
}

interface DailyPoint {
  date: string; // YYYY-MM-DD
  count: number;
}

function fmtDayShort(iso: string): string {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
}

/**
 * Daily-volume line chart with Y/X axes.
 *
 * Layout (viewBox 320×140):
 *   - 28px left padding for Y-axis labels
 *   - 20px bottom padding for X-axis labels
 *   - 8px top padding
 *   - Right padding 4px
 */
function DailyChart({ data }: { data: DailyPoint[] }) {
  if (data.length === 0) return null;

  const W = 320;
  const H = 140;
  const PAD_L = 28;
  const PAD_R = 4;
  const PAD_T = 8;
  const PAD_B = 22;
  const plotW = W - PAD_L - PAD_R;
  const plotH = H - PAD_T - PAD_B;

  const max = Math.max(...data.map((d) => d.count), 1);
  // Nice round Y-axis ticks: 0, max/2, max
  const yTicks = [0, Math.ceil(max / 2), max];

  const step = plotW / Math.max(data.length - 1, 1);
  const xAt = (i: number) => PAD_L + i * step;
  const yAt = (v: number) => PAD_T + plotH - (v / max) * plotH;

  const linePoints = data.map((d, i) => `${xAt(i)},${yAt(d.count)}`).join(' ');
  const areaPath =
    `M${xAt(0)},${PAD_T + plotH} ` +
    data.map((d, i) => `L${xAt(i)},${yAt(d.count)}`).join(' ') +
    ` L${xAt(data.length - 1)},${PAD_T + plotH} Z`;

  // X-axis label: every Nth point so labels don't overlap
  const xLabelStep = Math.max(1, Math.ceil(data.length / 6));

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full h-36"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="График записей по дням"
    >
      {/* Y grid + labels */}
      {yTicks.map((t) => {
        const y = yAt(t);
        return (
          <g key={t}>
            <line
              x1={PAD_L}
              x2={W - PAD_R}
              y1={y}
              y2={y}
              stroke="var(--color-sand)"
              strokeWidth={1}
              strokeDasharray={t === 0 ? '' : '2 3'}
              opacity={0.7}
            />
            <text
              x={PAD_L - 6}
              y={y + 3}
              textAnchor="end"
              fontSize={10}
              fill="var(--color-sienna-deep)"
            >
              {t}
            </text>
          </g>
        );
      })}

      {/* Area fill + line */}
      <path d={areaPath} fill="var(--color-rose)" opacity={0.18} />
      <polyline
        points={linePoints}
        fill="none"
        stroke="var(--color-rose)"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Data points */}
      {data.map((d, i) => (
        <circle
          key={d.date}
          cx={xAt(i)}
          cy={yAt(d.count)}
          r={2.5}
          fill="var(--color-rose)"
        />
      ))}

      {/* X axis labels */}
      {data.map((d, i) =>
        i % xLabelStep === 0 || i === data.length - 1 ? (
          <text
            key={`x-${d.date}`}
            x={xAt(i)}
            y={H - 4}
            textAnchor="middle"
            fontSize={9}
            fill="var(--color-sienna-deep)"
          >
            {fmtDayShort(d.date)}
          </text>
        ) : null,
      )}

      {/* Axis title (Y) */}
      <text
        x={4}
        y={PAD_T + 2}
        textAnchor="start"
        fontSize={9}
        fill="var(--color-sienna-deep)"
      >
        записей
      </text>
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

  const [downloading, setDownloading] = useState(false);

  function resetDates() {
    setFrom('');
    setTo('');
  }

  async function doExport() {
    // Validate ordering — if both set, `to` must not be before `from`.
    if (from && to && from > to) {
      pushToast('error', 'Дата "По" должна быть не раньше "С"');
      return;
    }
    setDownloading(true);
    try {
      const url =
        format === 'csv'
          ? api.admin.exportCsvUrl({ from: from || undefined, to: to || undefined })
          : api.admin.exportXlsxUrl({ from: from || undefined, to: to || undefined });
      const ext = format;
      await downloadAuthed(url, `slotbook-bookings.${ext}`, format, {
        from: from || undefined,
        to: to || undefined,
      });
      pushToast('success', 'Загружено');
      setExportOpen(false);
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось скачать');
    } finally {
      setDownloading(false);
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

      <div className="flex gap-2 overflow-x-auto no-scrollbar -mx-5 px-5">
        {PERIODS.map((p) => (
          <button
            key={p.value}
            type="button"
            onClick={() => setPeriod(p.value)}
            className={cn(
              'rounded-full px-3 py-1 text-sm font-semibold whitespace-nowrap',
              period === p.value
                ? 'bg-rose text-shell'
                : 'bg-shell border border-sand text-sienna-deep',
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
              <div className="text-sienna-deep text-xs uppercase">Выручка</div>
              <div className="text-2xl text-ink font-display">{data.revenue} ₽</div>
            </Card>
            <Card surface="shell">
              <div className="text-sienna-deep text-xs uppercase">Всего записей</div>
              <div className="text-2xl text-ink font-display">{data.total_bookings}</div>
            </Card>
            <Card surface="shell">
              <div className="text-sienna-deep text-xs uppercase">Завершено</div>
              <div className="text-2xl text-ink font-display">{data.completed_count}</div>
            </Card>
            <Card surface="shell">
              <div className="text-sienna-deep text-xs uppercase">Не пришли</div>
              <div className="text-2xl text-ink font-display">{data.no_show_count}</div>
            </Card>
            <Card surface="shell" className="col-span-2">
              <div className="text-sienna-deep text-xs uppercase">Доля отмен</div>
              <div className="text-2xl text-ink font-display">
                {(data.cancellation_rate * 100).toFixed(1)}%
              </div>
            </Card>
          </div>

          {data.daily_volume.length > 0 && (
            <Card surface="shell">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sienna-deep text-xs uppercase">Записи по дням</div>
                <div className="text-ink text-sm font-semibold">
                  всего {data.daily_volume.reduce((sum, d) => sum + d.bookings_count, 0)}
                </div>
              </div>
              <DailyChart
                data={data.daily_volume.map((d) => ({
                  date: d.date,
                  count: d.bookings_count,
                }))}
              />
            </Card>
          )}

          {data.top_services.length > 0 && (
            <Card surface="shell">
              <div className="text-sienna-deep text-xs uppercase mb-2">Топ услуг</div>
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
              <div className="text-sienna-deep text-xs uppercase mb-2">Топ сотрудников</div>
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
          <div className="flex flex-col gap-1">
            <div className="flex items-end justify-between gap-2">
              <span className="text-sienna-deep text-sm font-semibold">Период</span>
              {(from || to) && (
                <button
                  type="button"
                  onClick={resetDates}
                  className="text-rose text-sm font-semibold"
                >
                  Сбросить
                </button>
              )}
            </div>
            <Input
              label="С"
              type="date"
              value={from}
              max={to || undefined}
              onChange={(e) => setFrom(e.target.value)}
            />
            <Input
              label="По"
              type="date"
              value={to}
              min={from || undefined}
              onChange={(e) => setTo(e.target.value)}
            />
            <p className="text-sienna-deep/60 text-xs">
              Оставьте пустым, чтобы выгрузить все записи.
            </p>
          </div>
          <div className="flex gap-2 pt-2">
            <Button onClick={doExport} disabled={downloading}>
              {downloading ? '...' : 'Скачать'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setExportOpen(false)}
              disabled={downloading}
            >
              Отмена
            </Button>
          </div>
        </div>
      </Sheet>
    </div>
  );
}
