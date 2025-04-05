document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const togglePassword = document.getElementById('toggle-password');
    const passwordForm = document.getElementById('password-form');
    const responseMessage = document.getElementById('response-message');
    let isPasswordVisible = false; // Estado del ícono de visibilidad
    
    const rules = {
        length: document.getElementById('length-rule'),
        uppercase: document.getElementById('uppercase-rule'),
        lowercase: document.getElementById('lowercase-rule'),
        special: document.getElementById('special-rule')
    };

    // Validar la contraseña mientras el usuario escribe
    passwordInput.addEventListener('input', () => {
        validatePassword(passwordInput.value);
    });

    // Alternar visibilidad de la contraseña
    togglePassword.addEventListener('click', () => {
        isPasswordVisible = !isPasswordVisible;
        passwordInput.type = isPasswordVisible ? 'text' : 'password';
        confirmPasswordInput.type = isPasswordVisible ? 'text' : 'password';
    });

    // Función para validar reglas de contraseña
    function validatePassword(value) {
        rules.length.style.color = value.length >= 6 ? 'green' : 'red';
        rules.uppercase.style.color = /[A-Z]/.test(value) ? 'green' : 'red';
        rules.lowercase.style.color = /[a-z]/.test(value) ? 'green' : 'red';
        rules.special.style.color = /[!@#$%^&*(),.?":{}|<>]/.test(value) ? 'green' : 'red';
    }

    // Manejar el envío del formulario
    passwordForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Evita envío automático

        // Verificar que las contraseñas coincidan
        if (passwordInput.value !== confirmPasswordInput.value) {
            showMessage('Las contraseñas no coinciden', 'red');
            return;
        }

        // Verificar que la contraseña cumpla con los requisitos
        if (passwordInput.value.length < 8) {
            showMessage('La contraseña debe tener al menos 8 caracteres', 'red');
            return;
        }

        // Enviar los datos al servidor
        const formData = new FormData(passwordForm);
        try {
            const response = await fetch(passwordForm.action, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorMessage = await response.text();
                showMessage(errorMessage || 'Error al procesar la solicitud.', 'red');
            } else {
                showMessage('Contraseña actualizada con éxito', 'green');
                setTimeout(() => window.location.href = '/', 2000);
            }
        } catch (error) {
            showMessage('Error al procesar la solicitud.', 'red');
        }
    });

    // Función para mostrar mensajes de respuesta
    function showMessage(message, color) {
        responseMessage.style.display = 'block';
        responseMessage.style.backgroundColor = color;
        responseMessage.style.color = 'white';
        responseMessage.textContent = message;
    }
});