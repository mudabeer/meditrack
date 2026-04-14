const medicine_switch = document.querySelectorAll(".form-check-input");
if(medicine_switch){
    medicine_switch.forEach(e => {
        e.addEventListener('change', function(){
            const card = this.closest('.medicine-card');
            if (card) {
                card.dataset.status = this.checked ? 'active' : 'inactive';
                updateMedicineCardStyles();
            }

            console.log('medicine-id', this.dataset.id, 'checked', this.checked);
            fetch("/medicine",{
                method: 'POST',
                headers: {'Content-Type' : 'application/json'},
                body: JSON.stringify({
                    id: this.dataset.id,
                    status: this.checked
                })
            })
            .then(response => response.json())
            .then(data => console.log('medicine update response', data))
            .catch(err => console.error('medicine update failed', err));
        })
    })
}
   

function updateMedicineCardStyles() {
    document.querySelectorAll('.medicine-card').forEach(card => {
        const input = card.querySelector('.form-check-input');
        if (!input) {
            return;
        }

        if (!input.checked) {
            card.style.backgroundColor = '#21262d4b';
            card.style.color = '#f0f6fc42';
        } else {
            card.style.backgroundColor = 'rgba(255,255,255,0.06)';
            card.style.color = '#f0f6fc';
        }
    });
}

const inter = setInterval(updateMedicineCardStyles, 1000);
updateMedicineCardStyles();

// Notification helpers for reminders
const notifyKey = 'medicineNotifications';

function requestNotificationPermission() {
    if (!('Notification' in window)) {
        return Promise.resolve(false);
    }
    if (Notification.permission === 'default') {
        return Notification.requestPermission().then(permission => permission === 'granted');
    }
    return Promise.resolve(Notification.permission === 'granted');
}

function ensureNotificationPermission() {
    return ('Notification' in window) && Notification.permission === 'granted';
}

requestNotificationPermission().then(granted => {
    if (!granted) {
        console.warn('Notification permission not granted or blocked.');
        
    }
});

function getNotifiedSet() {
    try {
        return new Set(JSON.parse(localStorage.getItem(notifyKey) || '[]'));
    } catch (e) {
        return new Set();
    }
}

function saveNotifiedSet(set) {
    localStorage.setItem(notifyKey, JSON.stringify(Array.from(set)));
}

const notified = getNotifiedSet();

window.testMedicineNotification = function() {
    if (!('Notification' in window)) {
        window.alert('Notifications are not supported by this browser.');
        return;
    }
    if (Notification.permission !== 'granted') {
        window.alert(`Notification permission is ${Notification.permission}`);
        return;
    }
    new Notification('Test Medicine Reminder', {
        body: 'This is a test notification from your medicine reminder app.',
        icon: '/static/icons/medic.png'
    });
};

setInterval(() => {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const todayKey = `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()}`;

    console.debug('Notification check', {
        permission: Notification.permission,
        now: `${hour}:${minute}`,
        cards: document.querySelectorAll('.medicine-card').length
    });

    if (!ensureNotificationPermission()) return;

    document.querySelectorAll('.medicine-card').forEach(card => {
        const status = card.dataset.status;
        const reminderTime = card.dataset.reminderTime;
        const reminderId = card.dataset.reminderId;
        const medicineName = card.dataset.medicineName || 'medication';

        console.debug('Checking medicine card', {status, reminderTime, reminderId, medicineName});

        if (status && status.toLowerCase() !== 'active') return;
        if (!reminderTime || !reminderId) return;

        const [h, m] = reminderTime.split(':').map(v => parseInt(v, 10));
        if (Number.isNaN(h) || Number.isNaN(m)) return;

        if (h === hour && m === minute) {
            const key = `${todayKey}-${reminderId}-${h}-${m}`;
            if (notified.has(key)) return;

            window.alert(`Reminder check passed for ${medicineName} at ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`);

            try {
                new Notification('Medicine Reminder', {
                    body: `Time to take ${medicineName} (${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')})`,
                    icon: '/static/icons/medic.png'
                });
            } catch (err) {
                console.error('Notification creation failed', err);
                window.alert('Notification creation failed: ' + err.message);
            }

            notified.add(key);
            saveNotifiedSet(notified);
        }
    });
}, 15000);

const addTime = document.getElementById("add-time");

if(addTime){
let count = 1;
addTime.addEventListener("click", function(){
    const div = document.createElement("div")
    div.className = `input-group input-time`;
    div.innerHTML = `<input type="number" class="form-control time-font " name="hour" value="00" min="00" max="24">
                    <div class="input-group-text" style="font-size: 30px; font-weight: bold;">:</div>
                    <input type="number" class="form-control time-font" name="mintue" value="00" min="00" max="59">
                    <span class="material-icons time-close  px-1" id="time-1">close</span>`
    medicine_form = document.getElementById("medicine-form");
    medicine_form.insertBefore(div, addTime)
})
}

document.addEventListener("click", function(e) {
    const btn = e.target.closest(".time-close");

    if (btn) {
        btn.parentElement.remove();
    }
});

