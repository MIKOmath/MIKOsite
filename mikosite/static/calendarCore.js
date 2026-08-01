/* Pure calendar logic: dates, Polish text, colours and grid layout. No DOM access. */

const DEFAULT_GROUP_COLOR = '#074A59';
const WEEKS_IN_GRID = 6;
const DAYS_IN_GRID = WEEKS_IN_GRID * 7;
const MILLISECONDS_PER_DAY = 86400000;

const monthFormatter = new Intl.DateTimeFormat('pl', { month: 'long', year: 'numeric' });
const dayFormatter = new Intl.DateTimeFormat('pl', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
const shortDayFormatter = new Intl.DateTimeFormat('pl', { day: 'numeric', month: 'long' });

function startOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addDays(date, days) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

function addMonths(date, months) {
    return new Date(date.getFullYear(), date.getMonth() + months, 1);
}

function isoDate(date) {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${date.getFullYear()}-${month}-${day}`;
}

function parseLocalDate(value) {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, month - 1, day);
}

function monthKey(date) {
    return `${date.getFullYear()}-${date.getMonth() + 1}`;
}

function firstVisibleMonday(viewDate) {
    const first = startOfMonth(viewDate);
    return addDays(first, -((first.getDay() + 6) % 7));
}

function lastVisibleDay(viewDate) {
    return addDays(firstVisibleMonday(viewDate), DAYS_IN_GRID - 1);
}

function daysBetween(startDate, date) {
    return Math.round((date - startDate) / MILLISECONDS_PER_DAY);
}

function isSameDay(a, b) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function capitalizeFirst(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}

function polishPlural(count, one, few, many) {
    if (count === 1) {
        return one;
    }
    const lastDigit = count % 10;
    const lastTwoDigits = count % 100;
    if (lastDigit >= 2 && lastDigit <= 4 && (lastTwoDigits < 12 || lastTwoDigits > 14)) {
        return few;
    }
    return many;
}

function formatMonthTitle(date) {
    return capitalizeFirst(monthFormatter.format(date));
}

function formatDayTitle(date) {
    return capitalizeFirst(dayFormatter.format(date));
}

function describeDay(date, eventCount) {
    if (!eventCount) {
        return `${shortDayFormatter.format(date)}, brak wydarzeń`;
    }
    const noun = polishPlural(eventCount, 'wydarzenie', 'wydarzenia', 'wydarzeń');
    return `${shortDayFormatter.format(date)}, ${eventCount} ${noun}`;
}

function normalizeColor(color) {
    return /^#[0-9a-fA-F]{6}$/.test(color || '') ? color : DEFAULT_GROUP_COLOR;
}

function colorChannels(color) {
    const hex = normalizeColor(color).slice(1);
    return [hex.slice(0, 2), hex.slice(2, 4), hex.slice(4, 6)].map(pair => parseInt(pair, 16));
}

function contrastingInk(color) {
    const [red, green, blue] = colorChannels(color).map(channel => {
        const ratio = channel / 255;
        return ratio <= 0.03928 ? ratio / 12.92 : Math.pow((ratio + 0.055) / 1.055, 2.4);
    });
    const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
    return luminance > 0.45 ? '#06313E' : '#ffffff';
}

function groupKeyOf(seminar) {
    return seminar.group ? String(seminar.group.id) : null;
}

function groupColorOf(seminar) {
    return normalizeColor(seminar.group && seminar.group.color);
}

function emptyCalendarPayload() {
    return { seminars: [], registration_events: [], olympiad_stages: [] };
}

/**
 * Groups drawn anywhere on the grid, including the days it borrows from the
 * neighbouring months — a seminar on screen with no chip could not be filtered.
 */
function collectVisibleGroups(payload) {
    const groups = new Map();
    (payload.seminars || []).forEach(seminar => {
        if (!seminar.group) {
            return;
        }
        const existing = groups.get(groupKeyOf(seminar));
        if (existing) {
            existing.count += 1;
            return;
        }
        groups.set(groupKeyOf(seminar), {
            key: groupKeyOf(seminar),
            name: seminar.group.name,
            label: seminar.group.short_label,
            color: groupColorOf(seminar),
            count: 1,
        });
    });

    return [...groups.values()].sort((a, b) => a.label.localeCompare(b.label, 'pl'));
}

function toGridBand(item, kind, gridStartDate, gridEndDate) {
    const itemStart = parseLocalDate(item.date_begin);
    const itemEnd = parseLocalDate(item.date_end);
    return {
        ...item,
        kind,
        startIndex: Math.max(daysBetween(gridStartDate, itemStart), 0),
        endIndex: Math.min(daysBetween(gridStartDate, itemEnd), DAYS_IN_GRID - 1),
        continuesBefore: itemStart < gridStartDate,
        continuesAfter: itemEnd > gridEndDate,
    };
}

function assignLanes(bands) {
    const lanes = [];
    bands.forEach(band => {
        let lane = lanes.findIndex(placed => placed.every(
            other => other.endIndex < band.startIndex || other.startIndex > band.endIndex,
        ));
        if (lane === -1) {
            lanes.push([]);
            lane = lanes.length - 1;
        }
        lanes[lane].push(band);
        band.lane = lane;
    });
    return lanes.length;
}

/** Registration events take the top lanes; olympiad stages sit in a block below them. */
function layOutBands(payload, gridStartDate, gridEndDate) {
    const prepare = (items, kind) => items
        .map(item => toGridBand(item, kind, gridStartDate, gridEndDate))
        .filter(band => band.endIndex >= band.startIndex)
        .sort((a, b) => a.startIndex - b.startIndex || b.endIndex - a.endIndex);

    const events = prepare(payload.registration_events || [], 'event');
    const olympiads = prepare(payload.olympiad_stages || [], 'olympiad');
    const eventLaneCount = assignLanes(events);
    const olympiadLaneCount = assignLanes(olympiads);
    olympiads.forEach(band => { band.lane += eventLaneCount; });

    return { bands: [...events, ...olympiads], laneCount: eventLaneCount + olympiadLaneCount };
}

function bandsCoveringEachDay(bands, gridStartDate) {
    const byDay = new Map();
    bands.forEach(band => {
        for (let index = band.startIndex; index <= band.endIndex; index += 1) {
            const key = isoDate(addDays(gridStartDate, index));
            if (!byDay.has(key)) {
                byDay.set(key, []);
            }
            byDay.get(key).push(band);
        }
    });
    return byDay;
}

function segmentBandForWeek(band, weekIndex) {
    const weekStart = weekIndex * 7;
    const weekEnd = weekStart + 6;
    if (band.endIndex < weekStart || band.startIndex > weekEnd) {
        return null;
    }
    const from = Math.max(band.startIndex, weekStart);
    const to = Math.min(band.endIndex, weekEnd);
    return {
        firstColumn: from - weekStart + 1,
        lastColumn: to - weekStart + 2,
        clippedStart: band.startIndex < weekStart || (band.continuesBefore && from === band.startIndex),
        clippedEnd: band.endIndex > weekEnd || (band.continuesAfter && to === band.endIndex),
    };
}
