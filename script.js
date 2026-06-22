document.addEventListener("DOMContentLoaded", () => {
  const slider = document.querySelector("[data-reviews-slider]");

  if (slider) {
    const slides = Array.from(slider.querySelectorAll("[data-review-slide]"));
    const previousButton = document.querySelector("[data-review-prev]");
    const nextButton = document.querySelector("[data-review-next]");
    let currentIndex = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));

    const createPreview = (className) => {
      const preview = document.createElement("article");
      preview.className = `review-card review-card--preview ${className}`;
      preview.setAttribute("aria-hidden", "true");
      slider.append(preview);
      return preview;
    };

    const leftPreview = slides.length > 1 ? createPreview("is-prev") : null;
    const rightPreview = slides.length > 1 ? createPreview("is-next") : null;

    const fillPreview = (preview, source) => {
      if (!preview || !source) return;
      preview.innerHTML = source.innerHTML;
      preview.querySelectorAll("button, [data-review-full]").forEach((element) => element.remove());
    };

    const updateReviews = () => {
      if (!slides.length) return;
      slides.forEach((slide, index) => {
        const active = index === currentIndex;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", String(!active));
      });
      if (slides.length > 1) {
        fillPreview(leftPreview, slides[(currentIndex - 1 + slides.length) % slides.length]);
        fillPreview(rightPreview, slides[(currentIndex + 1) % slides.length]);
      }
    };

    previousButton?.addEventListener("click", () => {
      currentIndex = (currentIndex - 1 + slides.length) % slides.length;
      updateReviews();
    });
    nextButton?.addEventListener("click", () => {
      currentIndex = (currentIndex + 1) % slides.length;
      updateReviews();
    });
    updateReviews();
  }

  const modal = document.querySelector("[data-review-modal]");
  let modalTrigger = null;
  const closeModal = () => {
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    modalTrigger?.focus();
  };

  document.addEventListener("click", (event) => {
    const openButton = event.target.closest("[data-review-open]");
    if (openButton && modal) {
      const card = openButton.closest("[data-review-slide]");
      modalTrigger = openButton;
      modal.querySelector("[data-modal-title]").textContent = card.querySelector("h3").textContent;
      modal.querySelector("[data-modal-author]").textContent = `${card.querySelector(".review-card__person strong").textContent}, ${card.querySelector(".review-card__person span").textContent}`;
      modal.querySelector("[data-modal-text]").textContent = card.querySelector("[data-review-full]").textContent;
      modal.hidden = false;
      document.body.classList.add("modal-open");
      modal.querySelector(".review-modal__close").focus();
      return;
    }
    if (event.target.closest("[data-review-close]")) closeModal();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal && !modal.hidden) closeModal();
  });

  const orderSection = document.querySelector("#order");
  const selectedProduct = document.querySelector("[data-selected-product]");
  document.querySelectorAll("[data-order-product]").forEach((button) => {
    button.addEventListener("click", () => {
      if (selectedProduct) selectedProduct.value = button.dataset.orderProduct || "";
      orderSection?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  const form = document.querySelector("[data-order-form]");
  const message = document.querySelector("[data-form-message]");

  if (form) {
    const phone = form.elements.phone;
    const consent = form.elements.consent;
    const submitButton = form.querySelector("[type='submit']");

    const updateButton = () => {
      submitButton.disabled = !phone.validity.valid || !consent.checked;
    };

    phone.addEventListener("input", updateButton);
    consent.addEventListener("change", updateButton);
    updateButton();

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.reportValidity() || submitButton.disabled) return;

      submitButton.disabled = true;
      message.textContent = "Отправляем заявку...";
      message.classList.remove("is-success");

      try {
        const response = await fetch("/send-phone", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            phone: phone.value,
            consent: consent.checked,
            product: selectedProduct?.value || "",
          }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.message);

        message.textContent = result.message;
        message.classList.add("is-success");
        form.reset();
      } catch (error) {
        message.textContent = error.message || "Не удалось отправить заявку";
      }

      updateButton();
    });
  }
});
