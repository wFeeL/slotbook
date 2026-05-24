interface ContactLinksProps {
  username?: string | null;
  phone?: string | null;
  telegramId?: number | null;
}

/**
 * Renders quick-contact links for a client.
 *
 * Strategy (best → worst handle):
 *   1. @username — `tg://resolve?domain=...` deep-link opens that user's profile
 *      directly in the Telegram app on iOS/Android/Desktop.
 *   2. phone — `tel:` link triggers the dialer.
 *   3. telegram_id — last-resort plaintext (no link; numeric IDs aren't routable).
 */
export function ContactLinks({ username, phone, telegramId }: ContactLinksProps) {
  if (!username && !phone && !telegramId) {
    return <span className="text-sienna-deep text-sm">Контактов нет</span>;
  }
  return (
    <div className="flex flex-col gap-1">
      {username && (
        <a
          href={`tg://resolve?domain=${username}`}
          className="text-rose text-sm font-semibold"
        >
          ✈ Telegram @{username}
        </a>
      )}
      {phone && (
        <a href={`tel:${phone}`} className="text-rose text-sm font-semibold">
          📞 {phone}
        </a>
      )}
      {telegramId && !username && (
        <span className="text-sienna-deep text-xs">TG ID: {telegramId}</span>
      )}
    </div>
  );
}
