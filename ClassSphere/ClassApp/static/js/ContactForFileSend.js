const submit = document.getElementById('submit');
    const text = document.getElementById('contacttext'); 
    const form = document.querySelector('form'); 
    submit.addEventListener('click', (e) => {
      e.preventDefault(); 
      text.textContent = "Thank you for contacting us. We will get back to you shortly";
      text.style.color = "green"; 
      setTimeout(() => {
        text.textContent = "Let us help you get back on track"; 
        text.style.color = "black";
      }, 3000);
        form.reset(); 
      const name = document.getElementById('name');
      const email = document.getElementById('email');
      const subject = document.getElementById('subject');
      const message = document.getElementById('message');
      const fileInput = document.getElementById('fileInput');
      const formData = new FormData();
      formData.append('name', name.value);
      formData.append('email', email.value);
      formData.append('subject', subject.value);
      formData.append('message', message.value);
      formData.append('file', fileInput.files[0]); 
      fetch('http://127.0.0.1:8000/contact/', {
        method: 'POST',
        headers: {
          "x-csrftoken": '{{ csrf_token }}', 
        },
        body: formData,
      })
      .then(response => response.json())    
      .catch(error => {
        console.error('Error:', error);
      });
      
    });