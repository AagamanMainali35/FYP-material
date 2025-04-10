const submit = document.getElementById('submit');
    const text = document.getElementById('contacttext'); 
    const form = document.querySelector('form'); 
    submit.addEventListener('click', (e) => {
      e.preventDefault(); 
      function getCSRFToken() {
        const cookieValue = document.cookie
            .split(';')
            .find(cookie => cookie.trim().startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || ''; 
    }
      const form = document.querySelector('form');
      if (!form.checkValidity()) {
          form.reportValidity(); 
          return;  
      }
      text.textContent = "Thank you for contacting us. We will get back to you shortly";
      text.style.color = "green"; 
      setTimeout(() => {
        text.textContent = "Let us help you get back on track"; 
        text.style.color = "black";
      }, 3000);
        const name = document.getElementById("name");
        const email = document.getElementById("email");
        const subject = document.getElementById("subject");
        const message = document.getElementById("message");
        const fileInput = document.getElementById("fileInput");
        console.log(name.value)
        const formData = new FormData();
        formData.append('name', name.value);
        formData.append('email', email.value);
        formData.append('subject', subject.value);
        formData.append('message', message.value);
        formData.append('file', fileInput.files[0]);
    
      fetch('http://127.0.0.1:8000/contact/', {
        method: 'POST',
        headers: {
          "x-csrftoken": getCSRFToken(), 
        },
        body: formData,
      })
      .then(response => response.json())    
      .catch(error => {
        console.error('Error:', error);
      });
      form.reset(); 
      
    });