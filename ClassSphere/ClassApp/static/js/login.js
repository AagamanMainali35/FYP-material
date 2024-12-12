const forms = document.querySelector(".forms"),
      pwShowHide = document.querySelectorAll(".eye-icon"),
      links = document.querySelectorAll(".link");

pwShowHide.forEach(eyeIcon => {
    eyeIcon.addEventListener("click", () => {
        let pwFields = eyeIcon.parentElement.parentElement.querySelectorAll(".password");
        
        pwFields.forEach(password => {
            if(password.type === "password"){
                password.type = "text";
                eyeIcon.classList.replace("bx-hide", "bx-show");
                return;
            }
            password.type = "password";
            eyeIcon.classList.replace("bx-show", "bx-hide");
        })
        
    })
})      

links.forEach(link => {
    link.addEventListener("click", e => {
       e.preventDefault(); 
       forms.classList.toggle("show-signup");
    })
})


setTimeout(function () {
    const messageElement = document.getElementById("message");
    if (messageElement) {
        messageElement.innerHTML = "Please enter login details below.";  
        messageElement.style.color = "#7f7f7f";  
    }
}, 3000);  
const backButton = document.querySelector("button[name='back']");
backButton.addEventListener("click", (e) => {
        e.preventDefault(); 
        location.reload(); 

});



