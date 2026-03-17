const addTime = document.getElementById("add-time");


addTime.addEventListener("click", function(){
    const div = document.createElement("div")
    div.className = "input-group"
    div.innerHTML = `<input type="number" class="form-control time-font " name="hour" value="00" min="00" max="24">
                    <div class="input-group-text" style="font-size: 30px; font-weight: bold;">:</div>
                    <input type="number" class="form-control time-font" name="mintue" value="00" min="00" max="59">
                    <span class="material-icons time-close  px-1" id="time-1">close</span>`
    medicine_form = document.getElementById("medicine-form");
    medicine_form.insertBefore(div, addTime)
})