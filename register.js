let registerForm = document.getElementById('register-form');


function fetchData(callback = null) {
        setTimeout(() => {
            const data = eel.irr_user_sign_up(firstName, lastName, email, password);

            if (callback) {
                callback(data);

            }else {
                return Promise.resolve(data)
            }

        }, 4000)
    
}
document.addEventListener('DOMContentLoaded', function() {
    registerForm.onsubmit = async function(event) {
        event.preventDefault();
    
        let firstName = document.getElementById("firstName").value;
        let lastName = document.getElementById("lastName").value;
        let email = document.getElementById("email").value;
        let password = document.getElementById("password").value;

        
        let response = await eel.irr_user_sign_up(firstName, lastName, email, password)();

        if (response["message"] == "success") {
            window.location.href = "index.html";
        }else {
            window.location.href = "error.html";
        }
        
        /**
         * console.log("firstName: ", response["data"]["firstName"]);
        
         */
 
    }
})
