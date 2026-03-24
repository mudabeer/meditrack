const medicine_switch = document.querySelectorAll(".form-check-input");
if(medicine_switch){
         medicine_switch.forEach( e => {
        e.addEventListener('change', function(){
            fetch("/medicine",{
                method: 'POST',
                headers: {'Content-Type' : 'application/json'},
                body: JSON.stringify({
                    id: this.dataset.id,
                    status: this.checked
                })
            })
        })
    })
}
   

const inter = setInterval(() => {
    let i = 1
    while(true){
    const card = document.getElementById(`card-${i}`);
    if(card == null){
        break;
    }
    
    const input = document.getElementById(`input-${i}`)
    if(!input.checked){
        card.style.backgroundColor = "#21262d4b"
        card.style.color = "#f0f6fc42"
    }
    else {
        card.style.backgroundColor = "rgba(255,255,255,0.06)"
        card.style.color = "#f0f6fc"
    }
    i++;
}},1000)

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

