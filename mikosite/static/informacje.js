/* Calendar page controller: month loading, grid rendering, filters and the day dialog. */

const CALENDAR_ENDPOINT = '/api/calendar/';
const SEMINAR_ENDPOINT = '/api/seminars/';
const MAX_CHIP_ROWS_WIDE = 3;
const MAX_CHIP_ROWS_COMPACT = 4;
const MAX_CACHED_MONTHS = 24;
const PREFETCH_DEADLINE_MS = 1000;

const monthTitle = document.getElementById('currentMonth');
const weeksElement = document.getElementById('calendarWeeks');
const prevMonthButton = document.getElementById('prevMonth');
const nextMonthButton = document.getElementById('nextMonth');
const showCurrentMonthButton = document.getElementById('showCurrentMonth');
const filtersElement = document.getElementById('calendarFilters');
const groupFiltersElement = document.getElementById('groupFilters');
const clearFiltersButton = document.getElementById('clearFilters');
const progressElement = document.getElementById('calendarProgress');
const errorElement = document.getElementById('calendarError');
const retryButton = document.getElementById('calendarRetry');
const eventPopup = document.getElementById('eventPopup');
const popupEyebrow = document.getElementById('popupEyebrow');
const popupDate = document.getElementById('popupDate');
const eventList = document.getElementById('eventList');
const popupCloseButton = eventPopup ? eventPopup.querySelector('[data-dialog-close]') : null;

const compactQuery = window.matchMedia('(max-width: 780px)');

const state = {
    viewDate: startOfMonth(new Date()),
    payload: null,
    cache: new Map(),
    selectedGroups: new Set(),
    day: null,
    request: null,
    requestToken: 0,
};

/* ------------------------------------------------------------------ loading */

async function fetchMonth(viewDate, signal) {
    const start = firstVisibleMonday(viewDate);
    const end = lastVisibleDay(viewDate);
    const url = `${CALENDAR_ENDPOINT}?start_date=${isoDate(start)}&end_date=${isoDate(end)}`;
    const response = await fetch(url, { signal, headers: { Accept: 'application/json' } });
    if (!response.ok) {
        throw new Error(`Calendar request failed with ${response.status}`);
    }
    return response.json();
}

function cacheMonth(key, payload) {
    state.cache.set(key, payload);
    while (state.cache.size > MAX_CACHED_MONTHS) {
        state.cache.delete(state.cache.keys().next().value);
    }
}

async function loadMonth(viewDate) {
    state.viewDate = startOfMonth(viewDate);
    const key = monthKey(state.viewDate);

    if (state.cache.has(key)) {
        state.payload = state.cache.get(key);
        setError(false);
        render();
        prefetchAdjacentMonths();
        return;
    }

    if (state.request) {
        state.request.abort();
    }
    const controller = new AbortController();
    state.request = controller;
    const token = ++state.requestToken;

    render();
    setLoading(true);

    try {
        const payload = await fetchMonth(state.viewDate, controller.signal);
        cacheMonth(key, payload);
        if (token !== state.requestToken) {
            return;
        }
        state.payload = payload;
        setError(false);
        render();
        prefetchAdjacentMonths();
    } catch (error) {
        if (error.name === 'AbortError' || token !== state.requestToken) {
            return;
        }
        console.error('Error fetching calendar data:', error);
        state.payload = emptyCalendarPayload();
        setError(true);
        render();
    } finally {
        if (token === state.requestToken) {
            state.request = null;
            setLoading(false);
        }
    }
}

function prefetchAdjacentMonths() {
    // The timeout matters: idle callbacks are starved in a backgrounded tab.
    const schedule = window.requestIdleCallback
        ? callback => window.requestIdleCallback(callback, { timeout: PREFETCH_DEADLINE_MS })
        : callback => window.setTimeout(callback, PREFETCH_DEADLINE_MS);
    schedule(() => {
        [addMonths(state.viewDate, -1), addMonths(state.viewDate, 1)].forEach(async neighbour => {
            const key = monthKey(neighbour);
            if (state.cache.has(key)) {
                return;
            }
            try {
                cacheMonth(key, await fetchMonth(neighbour));
            } catch (error) {
                state.cache.delete(key);
            }
        });
    });
}

function setLoading(isLoading) {
    progressElement.hidden = !isLoading;
    weeksElement.classList.toggle('is-loading', isLoading);
}

function setError(hasError) {
    errorElement.hidden = !hasError;
}

/* ------------------------------------------------------------------ filters */

/**
 * Selections survive navigation, but only groups drawn on the current grid can
 * filter it — otherwise stepping into another month would empty the calendar.
 */
function activeGroupKeys(groups) {
    const present = new Set(groups.map(group => group.key));
    return new Set([...state.selectedGroups].filter(key => present.has(key)));
}

function toggleGroupFilter(key) {
    if (state.selectedGroups.has(key)) {
        state.selectedGroups.delete(key);
    } else {
        state.selectedGroups.add(key);
    }
    render();
}

function renderFilters(groups, activeKeys) {
    groupFiltersElement.replaceChildren();
    filtersElement.hidden = groups.length < 2;
    clearFiltersButton.hidden = activeKeys.size === 0;

    groups.forEach(group => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'calendar__chip';
        chip.style.setProperty('--chip-color', group.color);
        chip.style.setProperty('--chip-ink', contrastingInk(group.color));
        chip.setAttribute('aria-pressed', String(activeKeys.has(group.key)));
        chip.title = `${group.name}: ${group.count} ${polishPlural(group.count, 'spotkanie', 'spotkania', 'spotkań')}`;
        chip.textContent = group.label;
        chip.addEventListener('click', () => toggleGroupFilter(group.key));
        groupFiltersElement.appendChild(chip);
    });
}

function splitSeminarsByDay(payload, activeKeys) {
    const shown = new Map();
    const hidden = new Map();

    (payload.seminars || []).forEach(seminar => {
        const key = seminar.date;
        if (activeKeys.size && !activeKeys.has(groupKeyOf(seminar))) {
            hidden.set(key, (hidden.get(key) || 0) + 1);
            return;
        }
        if (!shown.has(key)) {
            shown.set(key, []);
        }
        shown.get(key).push(seminar);
    });

    return { shown, hidden };
}

/* ---------------------------------------------------------------- grid cells */

function buildDayCell(date, column, { hasContent, isOutside, isToday, eventCount }) {
    const cell = document.createElement('button');
    cell.type = 'button';
    cell.className = 'cal-cell';
    cell.style.gridColumn = column;
    cell.style.gridRow = '1 / -1';
    cell.classList.toggle('is-outside', isOutside);
    cell.classList.toggle('is-today', isToday);
    cell.classList.toggle('is-empty', !hasContent);
    cell.disabled = !hasContent;
    cell.setAttribute('aria-label', describeDay(date, eventCount));
    cell.addEventListener('click', () => openDayDialog(date));
    return cell;
}

function buildDayNumber(date, column) {
    const dayNumber = document.createElement('span');
    dayNumber.className = 'cal-daynum';
    dayNumber.style.gridColumn = column;
    dayNumber.style.gridRow = '1';
    dayNumber.textContent = String(date.getDate());
    return dayNumber;
}

/**
 * Chips start under the lowest band covering this day and stretch to the bottom,
 * so a day beside a band is not pushed down by a lane it does not use. The marker
 * costs a row of its own, so it only replaces chips when it stands for two or more.
 */
function buildDayChips(seminars, dayBands, column, maxRows) {
    const chips = document.createElement('div');
    chips.className = 'cal-chips';
    chips.style.gridColumn = column;
    const lowestLane = dayBands.reduce((lowest, band) => Math.max(lowest, band.lane), -1);
    chips.style.gridRow = `${lowestLane + 3} / -1`;

    const shownCount = seminars.length <= maxRows ? seminars.length : maxRows - 1;
    seminars.slice(0, shownCount).forEach(seminar => chips.appendChild(buildSeminarChip(seminar)));
    if (seminars.length > shownCount) {
        chips.appendChild(buildOverflowMarker(seminars.length - shownCount));
    }
    return chips;
}

function buildWeek(weekIndex, layout) {
    const { gridStartDate, bands, laneCount, seminarsByDay, bandsByDay, maxRows, today } = layout;

    const week = document.createElement('div');
    week.className = 'cal-week';
    // repeat(0, ...) is not valid CSS, so months without bands need the short form.
    week.style.gridTemplateRows = laneCount ? `auto repeat(${laneCount}, auto) 1fr` : 'auto 1fr';

    for (let weekday = 0; weekday < 7; weekday += 1) {
        const date = addDays(gridStartDate, weekIndex * 7 + weekday);
        const key = isoDate(date);
        const daySeminars = seminarsByDay.get(key) || [];
        const dayBands = bandsByDay.get(key) || [];
        const column = String(weekday + 1);

        week.append(
            buildDayCell(date, column, {
                hasContent: daySeminars.length > 0 || dayBands.length > 0,
                isOutside: date.getMonth() !== state.viewDate.getMonth(),
                isToday: isSameDay(date, today),
                eventCount: daySeminars.length + dayBands.length,
            }),
            buildDayNumber(date, column),
            buildDayChips(daySeminars, dayBands, column, maxRows),
        );
    }

    bands.forEach(band => {
        const placement = segmentBandForWeek(band, weekIndex);
        if (!placement) {
            return;
        }
        const segment = buildBandSegment(band, { ...placement, onOpen: openBandDialog });
        segment.style.gridColumn = `${placement.firstColumn} / ${placement.lastColumn}`;
        segment.style.gridRow = String(band.lane + 2);
        week.appendChild(segment);
    });

    return week;
}

function render() {
    const payload = state.payload || emptyCalendarPayload();
    const gridStartDate = firstVisibleMonday(state.viewDate);
    const gridEndDate = lastVisibleDay(state.viewDate);

    monthTitle.textContent = formatMonthTitle(state.viewDate);

    const groups = collectVisibleGroups(payload);
    const activeKeys = activeGroupKeys(groups);
    renderFilters(groups, activeKeys);

    const { bands, laneCount } = layOutBands(payload, gridStartDate, gridEndDate);
    const { shown: seminarsByDay, hidden: hiddenByDay } = splitSeminarsByDay(payload, activeKeys);
    const bandsByDay = bandsCoveringEachDay(bands, gridStartDate);

    state.day = { seminarsByDay, hiddenByDay, bandsByDay };

    const layout = {
        gridStartDate,
        bands,
        laneCount,
        seminarsByDay,
        bandsByDay,
        // Read per render: a resize that delivers no change event still lands right.
        maxRows: compactQuery.matches ? MAX_CHIP_ROWS_COMPACT : MAX_CHIP_ROWS_WIDE,
        today: new Date(),
    };

    const weeks = document.createDocumentFragment();
    for (let weekIndex = 0; weekIndex < WEEKS_IN_GRID; weekIndex += 1) {
        weeks.appendChild(buildWeek(weekIndex, layout));
    }
    weeksElement.replaceChildren(weeks);
}

/* ------------------------------------------------------------------- dialog */

function appendCardSection(heading, items, buildCard) {
    if (!items.length) {
        return;
    }
    eventList.appendChild(buildSectionHeader(heading));
    items.forEach(item => eventList.appendChild(buildCard(item)));
}

function openDayDialog(date, { highlightSeminarId = null } = {}) {
    if (!state.day) {
        return;
    }
    const key = isoDate(date);
    const seminars = state.day.seminarsByDay.get(key) || [];
    const bands = state.day.bandsByDay.get(key) || [];
    const events = bands.filter(band => band.kind === 'event');
    const olympiads = bands.filter(band => band.kind === 'olympiad');
    const hidden = state.day.hiddenByDay.get(key) || 0;

    popupEyebrow.textContent = 'Plan dnia';
    popupDate.textContent = formatDayTitle(date);
    eventList.replaceChildren();

    appendCardSection(events.length > 1 ? 'Wydarzenia' : 'Wydarzenie', events, buildEventCard);
    appendCardSection(olympiads.length > 1 ? 'Olimpiady' : 'Olimpiada', olympiads, buildOlympiadCard);
    appendCardSection('Zajęcia', seminars, seminar => buildSeminarCard(seminar, {
        highlighted: seminar.id === highlightSeminarId,
    }));

    if (!eventList.childElementCount) {
        const empty = document.createElement('p');
        empty.className = 'event-popup__empty';
        empty.textContent = hidden
            ? 'Wszystkie zajęcia tego dnia są ukryte przez wybrane filtry.'
            : 'Tego dnia nic nie zaplanowaliśmy.';
        eventList.appendChild(empty);
    } else if (hidden) {
        const note = document.createElement('p');
        note.className = 'event-popup__note';
        note.textContent = `Filtry ukrywają ${hidden} ${polishPlural(hidden, 'spotkanie', 'spotkania', 'spotkań')} tego dnia.`;
        eventList.appendChild(note);
    }

    showDialog();
}

function openBandDialog(band) {
    popupEyebrow.textContent = band.kind === 'olympiad' ? 'Etap olimpiady' : 'Wydarzenie stacjonarne';
    popupDate.textContent = band.title;
    eventList.replaceChildren(band.kind === 'olympiad' ? buildOlympiadCard(band) : buildEventCard(band));
    showDialog();
}

function showDialog() {
    if (eventPopup && typeof eventPopup.showModal === 'function' && !eventPopup.open) {
        eventPopup.showModal();
    }
    const highlighted = eventList.querySelector('.is-highlighted');
    if (highlighted) {
        highlighted.scrollIntoView({ block: 'nearest' });
    }
}

function closeDialog() {
    if (eventPopup && typeof eventPopup.close === 'function' && eventPopup.open) {
        eventPopup.close();
    }
}

/* ------------------------------------------------------------- deep linking */

function getRequestedSeminarId() {
    const raw = new URLSearchParams(window.location.search).get('seminar');
    if (!raw) {
        return null;
    }
    const parsed = Number(raw);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function clearRequestedSeminarId() {
    const url = new URL(window.location.href);
    url.searchParams.delete('seminar');
    window.history.replaceState({}, document.title, url.toString());
}

async function openRequestedSeminar(seminarId) {
    try {
        const response = await fetch(`${SEMINAR_ENDPOINT}${seminarId}/?display_only=1`);
        if (!response.ok) {
            throw new Error(`Failed to load seminar ${seminarId}`);
        }
        const seminar = await response.json();
        const seminarDate = parseLocalDate(seminar.date);
        await loadMonth(seminarDate);
        openDayDialog(seminarDate, { highlightSeminarId: seminarId });
    } catch (error) {
        console.error('Error opening requested seminar:', error);
        await loadMonth(new Date());
    } finally {
        clearRequestedSeminarId();
    }
}

/* ------------------------------------------------------------------ wiring */

function arrowKeysAreBusy(keyEvent) {
    if (keyEvent.altKey || keyEvent.ctrlKey || keyEvent.metaKey || keyEvent.shiftKey) {
        return true;
    }
    if (eventPopup && eventPopup.open) {
        return true;
    }
    const target = keyEvent.target;
    return target instanceof HTMLElement
        && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName));
}

prevMonthButton.addEventListener('click', () => loadMonth(addMonths(state.viewDate, -1)));
nextMonthButton.addEventListener('click', () => loadMonth(addMonths(state.viewDate, 1)));
showCurrentMonthButton.addEventListener('click', () => loadMonth(new Date()));

retryButton.addEventListener('click', () => {
    state.cache.delete(monthKey(state.viewDate));
    loadMonth(state.viewDate);
});

clearFiltersButton.addEventListener('click', () => {
    state.selectedGroups.clear();
    render();
});

if (popupCloseButton) {
    popupCloseButton.addEventListener('click', closeDialog);
}

if (eventPopup) {
    eventPopup.addEventListener('click', clickEvent => {
        if (clickEvent.target === eventPopup) {
            closeDialog();
        }
    });
}

compactQuery.addEventListener('change', () => render());

document.addEventListener('keydown', keyEvent => {
    if (keyEvent.key !== 'ArrowLeft' && keyEvent.key !== 'ArrowRight') {
        return;
    }
    if (arrowKeysAreBusy(keyEvent)) {
        return;
    }
    keyEvent.preventDefault();
    loadMonth(addMonths(state.viewDate, keyEvent.key === 'ArrowRight' ? 1 : -1));
});

document.addEventListener('DOMContentLoaded', () => {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarCenter = document.querySelector('.navbar-center');
    if (navbarToggle && navbarCenter) {
        navbarToggle.addEventListener('click', () => navbarCenter.classList.toggle('active'));
    }

    const requestedSeminarId = getRequestedSeminarId();
    if (requestedSeminarId) {
        openRequestedSeminar(requestedSeminarId);
    } else {
        loadMonth(new Date());
    }
});
