
const currentMonthElement = document.getElementById('currentMonth');
const calendarDaysElement = document.getElementById('calendarDays');
const prevMonthButton = document.getElementById('prevMonth');
const nextMonthButton = document.getElementById('nextMonth');
const eventPopup = document.getElementById('eventPopup');
const popupDate = document.getElementById('popupDate');
const eventList = document.getElementById('eventList');
const closeBtn = document.querySelector('.close-btn');

let currentDate = new Date();
let events = {};

function addEvent(eventDetails) {
    if (!eventDetails.date) {
        console.warn("Event skipped: No date specified");
        return;
    }
    const key = eventDetails.date.toDateString();
    if (!events[key]) {
        events[key] = [];
    }
    events[key].push(eventDetails);
}

function updateCalendar() {
    currentMonthElement.textContent = currentDate.toLocaleString('pl', { month: 'long', year: 'numeric' });
    calendarDaysElement.innerHTML = '';

    const dayNames = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nie'];
    dayNames.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.textContent = day;
        dayElement.classList.add('day-name');
        calendarDaysElement.appendChild(dayElement);
    });

    const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

    let startIndex = firstDayOfMonth.getDay() - 1;
    if (startIndex === -1) startIndex = 6;

    for (let i = 0; i < startIndex; i++) {
        calendarDaysElement.appendChild(document.createElement('div'));
    }

    for (let day = 1; day <= lastDayOfMonth.getDate(); day++) {
        const dayElement = document.createElement('div');
        const linkElement = document.createElement('a');
        linkElement.textContent = day;
        linkElement.className = "day-number";
        dayElement.appendChild(linkElement);
        dayElement.className = "day-nuberw"
        const currentDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
        const key = currentDay.toDateString();

        if (events[key]) {
            dayElement.classList.add('event-day');
            const eventIndicator = document.createElement('span');
            eventIndicator.className = 'event-indicator';
            eventIndicator.title = events[key].join(', ');
            dayElement.appendChild(eventIndicator);
            dayElement.addEventListener('click', () => showEventPopup(currentDay, events[key]));
        }

        if (day === new Date().getDate() &&
            currentDate.getMonth() === new Date().getMonth() &&
            currentDate.getFullYear() === new Date().getFullYear()) {
            dayElement.classList.add('current-day');
        }

        calendarDaysElement.appendChild(dayElement);
    }

    const totalCells = 42;
    const filledCells = calendarDaysElement.children.length;
    for (let i = filledCells; i < totalCells; i++) {
        calendarDaysElement.appendChild(document.createElement('div'));
    }
}

function showEventPopup(date, eventsList) {
    const warsawTime = new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Warsaw' }));
    popupDate.textContent = date.toLocaleDateString('pl', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    popupDate.style.fontWeight = "bold"
    eventList.innerHTML = '';

    eventsList.forEach(event => {
        const li = document.createElement('li');
        const timeDisplay = getTimeDisplay(event);

        li.style.color = '#06313E';
        li.style.fontFamily = '"Rubik", sans-serif';

        li.innerHTML = `
            <span style="color: var(--r1)"><strong>${timeDisplay}</strong></span>
            <h3 class="seminar-theme"><strong> ${event.theme} </strong></h3>
           
            <div class="badge-container">
                ${event.featured ? `
                    <div class="badge badge-featured">
                        <span class="material-symbols-rounded badge-icon">verified</span>
                        polecane
                    </div>` : ''}
                ${event.special_guest ? `
                    <div class="badge badge-featured">
                        <span class="material-symbols-rounded badge-icon">person_alert</span>
                        gość specjalny
                    </div>` : ''}
                ${event.group_name ? `
                    <div class="badge badge-dark">
                        <span class="material-symbols-rounded badge-icon">group</span>
                        ${event.group_name}
                    </div>` : ''}
                ${event.difficulty_label ? `
                    <div class="badge badge-light">
                        <span class="material-symbols-rounded badge-icon">${event.difficulty_icon}</span>
                        ${event.difficulty_label}
                    </div>` : ''}
            </div>
    
            <div class="event-info">
                ${event.tutors.length ? `
                    <p>
                        <strong>${event.tutors.length > 1 ? 'Prowadzą: ' : 'Prowadzi: '}</strong>${event.tutors.join(", ")}
                    </p>` : ''}
                ${event.description ? `
                    <p>
                        <strong>${'Opis: '}</strong>${event.description}<br>
                    </p>` : ''}
            </div>
    
            ${event.image ? `
                <div class="event-image">
                    <img src="${event.image}" alt="${event.theme}" style="max-width: 250px;">
                </div>` : ''}
            ${event.file ? `
                <div style="display: flex;">
                    <a href="${event.file}" style="text-decoration: none"><div class="badge badge-light">
                        <span class="material-symbols-rounded badge-icon">download</span>
                        załącznik</div></a>
                </div>` : ''}
        `;

        eventList.appendChild(li);
    });

    eventPopup.style.display = 'block';
}

function getTimeDisplay(event) {
    if (!event.time) {
        return 'Brak danych';
    }

    let startTime = event.time.toLocaleTimeString('pl', { hour: '2-digit', minute: '2-digit' });

    if (!event.duration) {
        return `${startTime} (nieznany czas trwania)`;
    }

    let endTime = new Date(event.time.getTime() + (event.duration.hours * 60 + event.duration.minutes) * 60000);
    endTime = endTime.toLocaleTimeString('pl', { hour: '2-digit', minute: '2-digit' });

    return `${startTime}-${endTime}`;
}


closeBtn.onclick = function() {
    eventPopup.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target === eventPopup) {
        eventPopup.style.display = 'none';
    }
}

prevMonthButton.addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    updateCalendar();
});

nextMonthButton.addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    updateCalendar();
});


updateCalendar();


document.addEventListener('DOMContentLoaded', function() {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarCenter = document.querySelector('.navbar-center');
    const eventPopup = document.getElementById('eventPopup');

    navbarToggle.addEventListener('click', function() {
        navbarCenter.classList.toggle('active');
    });

    // close popup when Escape is pressed
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' || event.key === 'Esc') {
            if (eventPopup && eventPopup.style.display === 'block') {
                eventPopup.style.display = 'none';
            }
        }
    });
});


// jump to current month
const showCurrentMonthButton = document.getElementById('showCurrentMonth');

function showCurrentMonth() {
    currentDate = new Date();
    updateCalendar();
}

showCurrentMonthButton.addEventListener('click', showCurrentMonth);