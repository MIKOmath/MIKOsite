
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
    eventList.innerHTML = '';
    eventsList.forEach(event => {
        const li = document.createElement('li');
        const eventStatus = determineEventStatus(event, warsawTime);
        const levelName = getLevelName(event.level);

        li.innerHTML = `
            <strong>Temat: ${event.theme || 'Brak.'}</strong><br>
            Początek zajęć: ${event.time ? event.time.toLocaleTimeString() : 'Not specified'}<br>
            Czas trwania zajęć: ${event.duration ? `${event.duration.hours}h ${event.duration.minutes}m` : 'Not specified'}<br>
            Prowadzący/a: ${event.tutors.join(', ') || 'None'}<br>
            Opis: ${event.description || 'No description'}<br>
            Poziom zaawansowania: ${levelName}<br>
            Status: ${eventStatus}<br>
            ${event.image ? `<img src="/media/${event.image}" alt="Event image" style="max-width: 100px;">` : ''}
            ${event.file ? `<a href="$/media/{event.file}" download>Download attached file</a>` : ''}
        `;
        eventList.appendChild(li);
    });

    eventPopup.style.display = 'block';
}

function getLevelName(level) {
        switch(level) {
            case 0:
                return 'Grupa początkująca';
            case 1:
                return 'Grupa średnia';
            case 2:
                return 'Grupa Finał++';
            case 3:
                return 'Poziom olimpiad międzynarodowych';
            default:
                return 'Brak poziomu zaawansowania';
        }
    }
function determineEventStatus(event, currentWarsawDate) {
    if (!event.time) {
        return 'Nie określono';
    }
    const eventStartTime = new Date(event.date.getTime());
    eventStartTime.setHours(event.time.getHours(), event.time.getMinutes(), event.time.getSeconds());

    const eventEndTime = new Date(eventStartTime.getTime());
    if (event.duration) {
        eventEndTime.setHours(eventEndTime.getHours() + event.duration.hours, eventEndTime.getMinutes() + event.duration.minutes);
    }

    if (currentWarsawDate < eventStartTime) {
        return 'Nie odbyło się';
    } else if (currentWarsawDate >= eventStartTime && currentWarsawDate <= eventEndTime) {
        return 'W trakcie';
    } else {
        return 'Odbyło się';
    }
}


closeBtn.onclick = function() {
    eventPopup.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == eventPopup) {
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