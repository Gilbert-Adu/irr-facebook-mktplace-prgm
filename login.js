let loginForm = document.getElementById('login-form');

let registerLink = document.getElementById('register-link');

loginForm.onsubmit = async function(event) {
    event.preventDefault();

    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let payload = await eel.irr_user_sign_in(email, password)();
    console.log(payload);
    if (payload["message"] == "SUCCESS") {
        console.log(payload["tasks"])
        window.location.href = 'index.html';
    }else {
        window.location.href = 'error.html';
    }

}


function registerUser() {
    window.location.href = 'register.html';
}

function loginPage() {
    window.location.href = 'login.html';
}