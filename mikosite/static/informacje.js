
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
        const levelName = getLevelName(event.level);
        const timeDisplay = getTimeDisplay(event);

        li.style.color = '#06313E';
        li.style.fontFamily = '"Rubik", sans-serif';

        li.innerHTML = `
            <a style="font-size: 20px; font-weight: bold">Temat:</a> ${event.theme || 'Brak.'}<br>
            <span style="font-size: 20px;">
                <a style="font-weight: bold">Czas zajęć:</a> ${timeDisplay}<br>
                <a style="font-weight: bold">
                ${event.tutors.length > 1 ? 'Prowadzą' : 'Prowadzi'}:</a> <span>${event.tutors ? event.tutors.join(', ') : 'Brak danych'}</span><br>
                <a style="font-weight: bold">Opis:</a> ${event.description || 'Brak opisu'}<br>
                <a style="font-weight: bold">Poziom zaawansowania:</a> ${levelName}<br>
                ${event.image ? `<img src="/media/${event.image}" alt="Event image" style="max-width: 100px;">` : ''}
                ${event.file ? `<a href="/media/${event.file}" download>Download attached file</a>` : ''}
            </span>
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
        return `${startTime} (czas trwania: brak danych)`;
    }

    let endTime = new Date(event.time.getTime() + (event.duration.hours * 60 + event.duration.minutes) * 60000);
    endTime = endTime.toLocaleTimeString('pl', { hour: '2-digit', minute: '2-digit' });

    return `${startTime} - ${endTime}`;
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


document.addEventListener('DOMContentLoaded', function() {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarCenter = document.querySelector('.navbar-center');
    const eventPopup = document.getElementById('eventPopup');

    navbarToggle.addEventListener('click', function() {
        navbarCenter.classList.toggle('active');
    });

    // Add event listener for keydown events
    document.addEventListener('keydown', function(event) {
        // Check if the pressed key is Escape (key code 27)
        if (event.key === 'Escape' || event.key === 'Esc') {
            // Close the popup if it's open
            if (eventPopup && eventPopup.style.display === 'block') {
                eventPopup.style.display = 'none';
            }
        }
    });
});


const showCurrentMonthButton = document.getElementById('showCurrentMonth');

// Add this function to reset the calendar to the current month
function showCurrentMonth() {
    currentDate = new Date();
    updateCalendar();
}

// Add this event listener with your other event listeners
showCurrentMonthButton.addEventListener('click', showCurrentMonth);