document.addEventListener("DOMContentLoaded", function () {
    // Mostrar mensaje de carga en las tablas
    document.getElementById("tablaUsuarios").innerHTML = "<tr><td colspan='3'>Cargando datos...</td></tr>";
    document.getElementById("tablaPagos").innerHTML = "<tr><td colspan='5'>Cargando datos...</td></tr>";
    document.getElementById("tablaReservas").innerHTML = "<tr><td colspan='4'>Cargando datos...</td></tr>";

    // Función para formatear fechas al formato estándar (DD/MM/YYYY)
    const formatFechaEstandar = (fechaStr) => {
        const fecha = new Date(fechaStr);
        return fecha.toLocaleDateString("es-MX", { day: "2-digit", month: "2-digit", year: "numeric" });
    };

    fetch("/datos_dashboard")
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error("Error en la API: ", data.error);
                return;
            }

            const safeNumber = (num) => Number(num) || 0;

            // Limpiar mensajes de carga
            document.getElementById("tablaUsuarios").innerHTML = "";
            document.getElementById("tablaPagos").innerHTML = "";
            document.getElementById("tablaReservas").innerHTML = "";

            // Llenar tabla de usuarios
            const tablaUsuarios = document.getElementById("tablaUsuarios");
            data.usuarios.forEach(u => {
                const fila = `<tr><td>${formatFechaEstandar(u.fecha)}</td><td>${safeNumber(u.total_usuarios)}</td><td>0</td></tr>`;
                tablaUsuarios.innerHTML += fila;
            });
            data.usuarios_google.forEach(ug => {
                const fila = `<tr><td>${formatFechaEstandar(ug.fecha)}</td><td>0</td><td>${safeNumber(ug.total_usuarios_google)}</td></tr>`;
                tablaUsuarios.innerHTML += fila;
            });

            // Llenar tabla de pagos
            const tablaPagos = document.getElementById("tablaPagos");
            data.pagos.forEach(p => {
                const fila = `<tr><td>${formatFechaEstandar(p.fecha)}</td><td>${safeNumber(p.normales_consumidos)}</td><td>${safeNumber(p.normales_no_consumidos)}</td><td>${safeNumber(p.google_consumidos)}</td><td>${safeNumber(p.google_no_consumidos)}</td></tr>`;
                tablaPagos.innerHTML += fila;
            });

            // Llenar tabla de reservas
            const tablaReservas = document.getElementById("tablaReservas");
            data.reservas.forEach(r => {
                const fila = `<tr><td>${formatFechaEstandar(r.fecha)}</td><td>${safeNumber(r.usuarios_normales)}</td><td>${safeNumber(r.usuarios_google)}</td><td>${r.estado_reserva}</td></tr>`;
                tablaReservas.innerHTML += fila;
            });

            // Configurar gráficos
            new Chart(document.getElementById("usuariosChart"), {
                type: "line",
                data: {
                    labels: data.usuarios.map(u => formatFechaEstandar(u.fecha)),
                    datasets: [
                        {
                            label: "Usuarios Normales",
                            data: data.usuarios.map(u => safeNumber(u.total_usuarios)),
                            borderColor: "blue",
                            fill: false
                        },
                        {
                            label: "Usuarios Google",
                            data: data.usuarios_google.map(ug => safeNumber(ug.total_usuarios_google)),
                            borderColor: "red",
                            fill: false
                        }
                    ]
                }
            });

            new Chart(document.getElementById("pagosChart"), {
                type: "bar",
                data: {
                    labels: data.pagos.map(p => formatFechaEstandar(p.fecha)),
                    datasets: [
                        {
                            label: "Normales Consumidos",
                            data: data.pagos.map(p => safeNumber(p.normales_consumidos)),
                            backgroundColor: "green"
                        },
                        {
                            label: "Normales No Consumidos",
                            data: data.pagos.map(p => safeNumber(p.normales_no_consumidos)),
                            backgroundColor: "orange"
                        },
                        {
                            label: "Google Consumidos",
                            data: data.pagos.map(p => safeNumber(p.google_consumidos)),
                            backgroundColor: "blue"
                        },
                        {
                            label: "Google No Consumidos",
                            data: data.pagos.map(p => safeNumber(p.google_no_consumidos)),
                            backgroundColor: "red"
                        }
                    ]
                }
            });

            new Chart(document.getElementById("reservasChart"), {
                type: "bar",
                data: {
                    labels: data.reservas.map(r => formatFechaEstandar(r.fecha)),
                    datasets: [
                        {
                            label: "Usuarios Normales",
                            data: data.reservas.map(r => safeNumber(r.usuarios_normales)),
                            backgroundColor: "blue"
                        },
                        {
                            label: "Usuarios Google",
                            data: data.reservas.map(r => safeNumber(r.usuarios_google)),
                            backgroundColor: "red"
                        }
                    ]
                }
            });
        })
        .catch(error => console.error("Error al obtener datos: ", error));
});
