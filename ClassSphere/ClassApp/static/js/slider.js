const initSlider = () => {
    const imageList = document.querySelector(".slider-wrapper .image-list");
    const slideButtons = document.querySelectorAll(".slider-wrapper .slide-button");
    const maxScrollLeft = imageList.scrollWidth - imageList.clientWidth;

    // Function to slide images on button click
    const slide = (direction) => {
      const scrollAmount = imageList.clientWidth * direction;
      imageList.scrollBy({ left: scrollAmount, behavior: "smooth" });
    };

    // Update visibility of navigation buttons
    const updateButtonVisibility = () => {
      slideButtons[0].style.display = imageList.scrollLeft <= 0 ? "none" : "flex";
      slideButtons[1].style.display = imageList.scrollLeft >= maxScrollLeft ? "none" : "flex";
    };

    // Attach click events to the buttons
    slideButtons[0].addEventListener("click", () => {
      slide(-1);
    });
    slideButtons[1].addEventListener("click", () => {
      slide(1);
    });

    // Update button visibility on scroll
    imageList.addEventListener("scroll", updateButtonVisibility);

    // Initial button visibility
    updateButtonVisibility();
  };

  // Initialize slider on page load
  window.addEventListener("load", initSlider);