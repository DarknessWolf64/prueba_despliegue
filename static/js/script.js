document.addEventListener("DOMContentLoaded", function () {
    const inputs = document.querySelectorAll(".inp input");
    const pinHidden = document.getElementById("pinHidden");

    // Moverse automáticamente al siguiente input al escribir
    inputs.forEach((input, index) => {
        input.addEventListener("input", (e) => {
            if (e.inputType !== "deleteContentBackward" && input.value.length === 1 && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
            updateHiddenPin();
        });

        // Permitir borrar y retroceder
        input.addEventListener("keydown", (e) => {
            if (e.key === "Backspace" && index > 0 && input.value === "") {
                inputs[index - 1].focus();
            }
        });
    });

    // Pegar un PIN completo en las casillas
    document.querySelector(".inp").addEventListener("paste", function (e) {
        e.preventDefault();
        const pin = e.clipboardData.getData("text").trim();
        if (pin.length === 6 && /^\d{6}$/.test(pin)) {
            inputs.forEach((input, index) => {
                input.value = pin[index] || "";
            });
            inputs[5].focus();  // Focalizar el último campo
            updateHiddenPin();
        }
    });

    // Actualizar el campo oculto con el PIN completo
    function updateHiddenPin() {
        pinHidden.value = Array.from(inputs).map(input => input.value).join("");
    }
});
