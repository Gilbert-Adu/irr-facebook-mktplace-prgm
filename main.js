
let months = [
    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
];
let days = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
];

let currentDate = new Date();
let day = days[currentDate.getDay()];
let dayOfMonth = currentDate.getDate();
let month = months[currentDate.getMonth()];
let year = currentDate.getFullYear();

let thisMonth = document.getElementById("month");
let thisGreeting = document.getElementById("today_greeting");

thisMonth.innerText = month;
thisGreeting.innerText = `Today is ${day}, ${month} ${dayOfMonth}, ${year}`;



let searchForm = document.getElementById("fb-search");
let botForm = document.getElementById('bot-trainer-form');

function processCondition(newCondition=false, used_like_new=false, used_good=false, used_fair=false) {
    let condition = [];

    if (newCondition) {
        condition.push("new");
    }
    if (used_like_new) {
        condition.push("used_like_new")
    }
    if (used_good) {
        condition.push("used_good");
    }
    if (used_fair) {
        condition.push("used_fair");
    }

    return condition;

}

let successNotif = document.getElementById("success");
let messagEval = document.getElementById("message-eval");
botForm.onsubmit = async function(event) {
    event.preventDefault();
    let question = document.getElementById("question").value;
    let answer = document.getElementById("answer").value;
    await eel.teach_bot(question, answer)();
    messagEval.innerText = "You trained the bot with 1 Q&A";
    successNotif.style.display = "block";




}
function delete_task_url(url) {
    let item = document.getElementById(url);
    item.style.display = none;

}
searchForm.onsubmit = async function(event) {
    event.preventDefault();
    let query = document.getElementById("query").value;
    let city = document.getElementById("city").value;
    let minPrice = document.getElementById("minPrice").value;
    let maxPrice = document.getElementById("maxPrice").value;

    let brand = document.getElementById("brand").value;
    let productLine = document.getElementById("productLine").value;
    let network = document.getElementById("network").value;

    let newCondition = document.getElementById("new").checked;
    let used_like_new = document.getElementById("used_like_new").checked;
    let used_good = document.getElementById("used_good").checked;
    let used_fair = document.getElementById("used_fair").checked;

    let condition = processCondition(newCondition=newCondition, used_like_new=used_like_new, used_good=used_good, used_fair=used_fair);

    let url = await eel.expose_url(
        city=city,
        query=query,
        condition=condition,
        minPrice=minPrice,
        maxPrice=maxPrice,
        brandInput=brand,
        product=productLine,
        networkInput=network
    )();
    
    let AllTasks = document.getElementById("all-tasks");
    let aTask = document.createElement("div");
    aTask.classList.add("a-task");
    let taskDetails = `

        <div class="task-details" id="${url}">

            <p class="task-title" style="font-size: 14px;font-family: Inter, sans-serif;font-weight: bold;margin-top: 1vh;">${query}</p>
            <p>
                <span class="task-city" style="font-size: 10px;font-family: Inter, sans-serif;"><strong>Location</strong>: ${city}</span>,
                <span class="task-max" style="font-size: 10px;font-family: Inter, sans-serif;"> <strong>Max</strong>: $${minPrice}</span>,
                <span class="task-min" style="font-size: 10px;font-family: Inter, sans-serif;"> <strong>Min</strong>: $${maxPrice}</span>
            </p>
        </div>
        <span class="bot-close" id="delete-task">&times;</span>

     `
     aTask.innerHTML = taskDetails;
     let firstChild = AllTasks.firstChild;
     AllTasks.insertBefore(aTask, firstChild);
    let payload = await eel.get_user_info()();
    let user = payload["user"];
    user_id = user["UserId"];
    

    /**
     * call eel function to create and save task
     */
    await eel.expose_create_task(
        user_id=user_id,
        url=url, 
        query=query, 
        city=city, 
        minPrice=minPrice, 
        maxPrice=maxPrice, 
        brandInput=brand, 
        product=product, 
        networkInput=network, 
        condition=condition
    )();
 
    eel.login_to_facebook(city, query, condition, minPrice, maxPrice, brand, productLine, network)();
    messagEval.innerText = "You created 1 task";
    successNotif.style.display = "block";



}

let btn = document.getElementById("create-task-button");
let modal = document.getElementById("modal");
let span = document.getElementsByClassName("close")[0];

let botModal = document.getElementById("bot-modal");
let bot = document.getElementById("schedule");
let botClose = document.getElementsByClassName("bot-close")[0];

bot.onclick = function() {
    botModal.style.display = "block";
};

botClose.onclick = function() {
    botModal.style.display = "none";
};




btn.onclick = function() {
    modal.style.display = "block";
}
span.onclick = function() {
    modal.style.display = "none";
}

let personName = document.getElementById("person-name");
let personEmail = document.getElementById("person-email");
let userName = document.getElementById("user-name");



async function user_details() {
    let payload = await eel.get_user_info()();
    let user = payload["user"];
    let tasks = payload["tasks"];
    //console.log("tasks: ", tasks)
    personName.innerText = `${user["firstName"]} ${user["lastName"]}`;
    personEmail.innerText = `${user["Email"]}`;
    userName.innerText = `${user["firstName"]} ${user["lastName"]}`;

    for (let i=0; i < tasks.length; i++) {
        let totalTasks = document.getElementById("all-tasks");
        let tempTask = document.createElement("div");
        tempTask.classList.add("a-task");

        let thisTask = `


        <div class="task-details"  data-index="${tasks[i].TaskId}">
            <p class="task-title" style="font-size: 14px;font-family: Inter, sans-serif;font-weight: bold;margin-top: 1vh;">${tasks[i].query}</p>
            <p>
                <span class="task-city" style="font-size: 10px;font-family: Inter, sans-serif;"><strong>Location</strong>: ${tasks[i].city}</span>,
                <span class="task-max" style="font-size: 10px;font-family: Inter, sans-serif;"> <strong>Max</strong>: $${tasks[i].minPrice}</span>,
                <span class="task-min" style="font-size: 10px;font-family: Inter, sans-serif;"> <strong>Min</strong>: $${tasks[i].maxPrice}</span>
            </p>
        </div>
        <span class="bot-close" id="task-close"   data-id="${tasks[i].TaskId}">&times;</span>

     `
     tempTask.innerHTML = thisTask;
     let firstChild = totalTasks.firstChild;
     totalTasks.insertBefore(tempTask, firstChild);

     document.getElementById('task-close').onclick = async function(){
        let dataId = this.getAttribute("data-id");
        //let taskElement = document.querySelector('[data-index="dataId"]')
        //taskElement.style.display = 'none';
        await eel.delete_task_by_id(dataId);
        console.log(dataId, " deleted")
     }
     

    }

}

window.onload = function() {
    user_details();
  

};


