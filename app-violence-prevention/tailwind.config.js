/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#1E3A8A', // Azul oscuro para botones y encabezados
                secondary: '#3B82F6', // Azul más claro para hover y detalles
                background: '#F3F4F6', // Fondo gris claro
                textPrimary: '#1F2937', // Texto oscuro
                error: '#EF4444', // Rojo para errores
            },
        },
    },
    plugins: [],
}