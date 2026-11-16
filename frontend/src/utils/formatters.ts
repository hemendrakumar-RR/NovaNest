/**
 * Currency, Number and Metric Formatters
 */

export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) return "₹0";
  if (Math.abs(amount) >= 1_000_000_000) {
    return `₹${(amount / 1_000_000_000).toFixed(2)}B`;
  }
  if (Math.abs(amount) >= 10_000_000) {
    return `₹${(amount / 10_000_000).toFixed(2)} Cr`;
  }
  if (Math.abs(amount) >= 100_000) {
    return `₹${(amount / 100_000).toFixed(2)}L`;
  }
  if (Math.abs(amount) >= 1_000) {
    return `₹${(amount / 1_000).toFixed(1)}k`;
  }
  return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export function formatFullCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) return "₹0.00";
  return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatNumber(num: number | null | undefined): string {
  if (num === null || num === undefined || isNaN(num)) return "0";
  return num.toLocaleString('en-IN');
}

export function formatPercent(pct: number | null | undefined): string {
  if (pct === null || pct === undefined || isNaN(pct)) return "0.0%";
  return `${pct.toFixed(1)}%`;
}

/**
 * Indian Standard Time (IST - Asia/Kolkata) Formatters
 * Strict 12-hour AM/PM format
 */

export function formatTimeToIST(input: string | Date | number | null | undefined, includeSeconds = false): string {
  if (!input) return '';

  // 1. If Date object
  if (input instanceof Date) {
    if (isNaN(input.getTime())) return '';
    const timeStr = new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Kolkata',
      hour: 'numeric',
      minute: '2-digit',
      second: includeSeconds ? '2-digit' : undefined,
      hour12: true,
    }).format(input);
    return `${timeStr} IST`;
  }

  const str = String(input).trim();
  if (!str) return '';

  // 2. If timestamp contains explicit UTC Z, +, or ISO T
  if (str.includes('Z') || str.includes('+') || (str.includes('T') && str.length >= 19)) {
    const d = new Date(str);
    if (!isNaN(d.getTime())) {
      const timeStr = new Intl.DateTimeFormat('en-US', {
        timeZone: 'Asia/Kolkata',
        hour: 'numeric',
        minute: '2-digit',
        second: includeSeconds ? '2-digit' : undefined,
        hour12: true,
      }).format(d);
      return `${timeStr} IST`;
    }
  }

  // 3. If local timestamp without timezone offset (e.g. "2024-03-01 14:22:10" from orders data)
  // Preserves local operational hours without double-converting!
  const timeMatch = str.match(/(\d{4}-\d{2}-\d{2})?[ T]?(\d{1,2}):(\d{2})(:(\d{2}))?/);
  if (timeMatch) {
    let hour = parseInt(timeMatch[2], 10);
    const minute = timeMatch[3];
    const second = timeMatch[5];
    const ampm = hour >= 12 ? 'PM' : 'AM';
    hour = hour % 12;
    if (hour === 0) hour = 12;
    const secStr = includeSeconds && second ? `:${second}` : '';
    return `${hour}:${minute}${secStr} ${ampm} IST`;
  }

  // 4. Fallback Date parse
  const fallback = new Date(str);
  if (!isNaN(fallback.getTime())) {
    const timeStr = new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Kolkata',
      hour: 'numeric',
      minute: '2-digit',
      second: includeSeconds ? '2-digit' : undefined,
      hour12: true,
    }).format(fallback);
    return `${timeStr} IST`;
  }

  return str;
}

export function formatDateTimeToIST(input: string | Date | number | null | undefined): string {
  if (!input) return '';
  const timePart = formatTimeToIST(input);

  let datePart = '';
  if (input instanceof Date && !isNaN(input.getTime())) {
    datePart = new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    }).format(input);
  } else {
    const str = String(input).trim();
    const dateMatch = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (dateMatch) {
      const year = parseInt(dateMatch[1], 10);
      const monthIndex = parseInt(dateMatch[2], 10) - 1;
      const day = parseInt(dateMatch[3], 10);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      datePart = `${day} ${months[monthIndex]} ${year}`;
    } else {
      const d = new Date(str);
      if (!isNaN(d.getTime())) {
        datePart = new Intl.DateTimeFormat('en-IN', {
          timeZone: 'Asia/Kolkata',
          day: 'numeric',
          month: 'short',
          year: 'numeric'
        }).format(d);
      }
    }
  }

  return datePart ? `${datePart} • ${timePart}` : timePart;
}

