/* Builders for the elements the calendar draws: grid chips, day bands and dialog cards. */

function buildBadge(iconName, text, modifier) {
    const element = document.createElement('div');
    element.className = `badge ${modifier}`;
    if (iconName) {
        const icon = document.createElement('span');
        icon.className = 'material-symbols-rounded badge-icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = iconName;
        element.appendChild(icon);
    }
    element.appendChild(document.createTextNode(text));
    return element;
}

function buildBadgeLink(href, iconName, text, modifier, { external = false } = {}) {
    const link = document.createElement('a');
    link.className = 'badge-link';
    link.href = href;
    if (external) {
        link.target = '_blank';
        link.rel = 'noopener';
    }
    link.appendChild(buildBadge(iconName, text, modifier));
    return link;
}

function hostLabel(url, fallback) {
    try {
        return new URL(url, window.location.origin).hostname.replace(/^www\./, '');
    } catch (error) {
        return fallback;
    }
}

function buildSectionHeader(text) {
    const header = document.createElement('h3');
    header.className = 'event-popup__section';
    header.textContent = text;
    return header;
}

function buildSeminarChip(seminar) {
    const chip = document.createElement('span');
    chip.className = 'cal-chip';
    chip.style.setProperty('--chip-color', groupColorOf(seminar));

    const dot = document.createElement('span');
    dot.className = 'cal-chip__dot';

    const time = document.createElement('span');
    time.className = 'cal-chip__time';
    time.textContent = seminar.time;

    chip.append(dot, time);
    chip.title = seminar.group
        ? `${seminar.time_label} ${seminar.theme} (${seminar.group.name})`
        : `${seminar.time_label} ${seminar.theme}`;
    return chip;
}

function buildOverflowMarker(count) {
    const marker = document.createElement('span');
    marker.className = 'cal-more';
    marker.textContent = `+${count}`;
    marker.title = `Jeszcze ${count} ${polishPlural(count, 'spotkanie', 'spotkania', 'spotkań')} tego dnia`;
    return marker;
}

function buildBandSegment(band, { clippedStart, clippedEnd, onOpen }) {
    const segment = document.createElement('button');
    segment.type = 'button';
    segment.className = `cal-band cal-band--${band.kind}`;
    segment.classList.toggle('is-clipped-start', clippedStart);
    segment.classList.toggle('is-clipped-end', clippedEnd);

    if (band.kind === 'olympiad' && band.olympiad.logo) {
        const logo = document.createElement('img');
        logo.className = 'cal-band__logo';
        logo.src = band.olympiad.logo;
        logo.alt = '';
        segment.appendChild(logo);
    } else {
        const icon = document.createElement('span');
        icon.className = 'material-symbols-rounded cal-band__icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = band.kind === 'olympiad' ? 'trophy' : 'local_activity';
        segment.appendChild(icon);
    }

    const label = document.createElement('span');
    label.className = 'cal-band__label';
    label.textContent = band.title;
    segment.appendChild(label);

    if (band.kind === 'event' && band.registration_open) {
        const openBadge = document.createElement('span');
        openBadge.className = 'cal-band__badge';
        openBadge.textContent = 'zapisy';
        segment.appendChild(openBadge);
    }

    segment.title = `${band.title}, ${band.date_range}`;
    segment.addEventListener('click', clickEvent => {
        clickEvent.stopPropagation();
        onOpen(band);
    });
    return segment;
}

function appendBadges(card, badges) {
    if (badges.childElementCount) {
        card.appendChild(badges);
    }
}

function buildEventCard(event) {
    const card = document.createElement('article');
    card.className = 'event-card event-card--event';

    const eyebrow = document.createElement('p');
    eyebrow.className = 'event-card__eyebrow';
    eyebrow.textContent = event.date_range;

    const title = document.createElement('h4');
    title.className = 'event-card__title';
    title.textContent = event.title;
    card.append(eyebrow, title);

    const badges = document.createElement('div');
    badges.className = 'badge-container';
    if (event.location) {
        badges.appendChild(buildBadge('location_on', event.location, 'badge-featured'));
    }
    badges.appendChild(buildBadge(
        event.registration_open ? 'how_to_reg' : 'event_busy',
        event.registration_open ? `zapisy: ${event.registration_range}` : 'zapisy zamknięte',
        event.registration_open ? 'badge-yellow' : 'badge-dark',
    ));
    appendBadges(card, badges);

    if (event.registration_url && event.registration_open) {
        const call = document.createElement('a');
        call.className = 'event-card__cta';
        call.href = event.registration_url;
        call.target = '_blank';
        call.rel = 'noopener';
        call.textContent = 'Biorę udział!';
        card.appendChild(call);
    }

    return card;
}

function buildOlympiadCard(stage) {
    const card = document.createElement('article');
    card.className = 'event-card event-card--olympiad';

    const head = document.createElement('div');
    head.className = 'event-card__head';
    if (stage.olympiad.logo) {
        const logo = document.createElement('img');
        logo.className = 'event-card__logo';
        logo.src = stage.olympiad.logo;
        logo.alt = stage.olympiad.name;
        head.appendChild(logo);
    }

    const heading = document.createElement('div');
    const eyebrow = document.createElement('p');
    eyebrow.className = 'event-card__eyebrow';
    eyebrow.textContent = stage.date_range;
    const title = document.createElement('h4');
    title.className = 'event-card__title';
    title.textContent = `${stage.olympiad.name} – ${stage.stage_label}`;
    heading.append(eyebrow, title);
    head.appendChild(heading);
    card.appendChild(head);

    const badges = document.createElement('div');
    badges.className = 'badge-container';
    if (stage.location) {
        badges.appendChild(buildBadge('location_on', stage.location, 'badge-light'));
    }
    if (stage.url) {
        badges.appendChild(buildBadgeLink(
            stage.url, 'language', hostLabel(stage.url, 'strona olimpiady'), 'badge-dark', { external: true },
        ));
    }
    if (stage.note) {
        badges.appendChild(buildBadge('info', stage.note, 'badge-light'));
    }
    appendBadges(card, badges);

    return card;
}

function buildSeminarBadges(seminar) {
    const badges = document.createElement('div');
    badges.className = 'badge-container';

    if (seminar.featured) {
        badges.appendChild(buildBadge('verified', 'polecane', 'badge-featured'));
    }
    if (seminar.special_guest) {
        badges.appendChild(buildBadge('person_alert', 'gość specjalny', 'badge-featured'));
    }
    if (seminar.group) {
        const color = groupColorOf(seminar);
        const groupBadge = buildBadge('group', seminar.group.name, 'badge-group');
        groupBadge.style.backgroundColor = color;
        groupBadge.style.color = contrastingInk(color);
        badges.appendChild(groupBadge);
    }
    if (seminar.difficulty_label) {
        badges.appendChild(buildBadge(seminar.difficulty_icon, seminar.difficulty_label, 'badge-light'));
    }
    if (seminar.file) {
        badges.appendChild(buildBadgeLink(seminar.file, 'download', 'załącznik', 'badge-dark'));
    }
    return badges;
}

function buildSeminarDetails(seminar) {
    const info = document.createElement('div');
    info.className = 'event-card__info';

    if (seminar.tutors.length) {
        const tutors = document.createElement('p');
        const label = document.createElement('strong');
        label.textContent = seminar.tutors.length > 1 ? 'Prowadzą: ' : 'Prowadzi: ';
        tutors.append(label, document.createTextNode(seminar.tutors.join(', ')));
        info.appendChild(tutors);
    }
    if (seminar.description) {
        const description = document.createElement('p');
        description.textContent = seminar.description;
        info.appendChild(description);
    }
    return info;
}

function buildSeminarCard(seminar, { highlighted = false } = {}) {
    const card = document.createElement('article');
    card.className = 'event-card event-card--seminar';
    card.classList.toggle('is-highlighted', highlighted);

    const time = document.createElement('p');
    time.className = 'event-card__time';
    time.textContent = seminar.time_label;

    const title = document.createElement('h4');
    title.className = 'event-card__title';
    title.textContent = seminar.theme;
    card.append(time, title);

    appendBadges(card, buildSeminarBadges(seminar));

    const details = buildSeminarDetails(seminar);
    if (details.childElementCount) {
        card.appendChild(details);
    }

    if (seminar.image) {
        const figure = document.createElement('div');
        figure.className = 'event-card__image';
        const image = document.createElement('img');
        image.src = seminar.image;
        image.alt = seminar.theme;
        image.loading = 'lazy';
        figure.appendChild(image);
        card.appendChild(figure);
    }

    return card;
}
