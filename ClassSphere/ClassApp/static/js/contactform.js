window.onload = function () {
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");

    // Handle file input change event
    fileInput.addEventListener("change", function () {
        const fileName = this.files[0]?.name;
        if (fileName) {
            const maxLength = 15;
            const truncatedName = fileName.length > maxLength
                ? fileName.substring(0, maxLength - 1) + "..."
                : fileName;

            uploadButton.innerHTML =` File: ${truncatedName}`;
        }
    });

    uploadButton.addEventListener("click", function () {
        fileInput.click();
    });
};




