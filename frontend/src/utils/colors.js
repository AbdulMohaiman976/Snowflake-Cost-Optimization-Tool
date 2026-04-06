/**
 * SnowAdvisor "Crystal Ice" - Modern Glassmorphism Theme
 * 
 * A high-end, futuristic theme using your triad (#A9D6E5, #2C7DA0, #FFFFFF).
 * Features layered transparency, glowing borders, and soft blue gradients.
 */

export const colors = {
    // ❄️ Core Foundations
    background: "#A9D6E5",     // Base Light Blue
    surface:    "#FFFFFF",     // Pure White
    sidebar:    "#2C7DA0",     // Contrast Dark Blue
    topbar:     "#FFFFFF",     // Floating White
    
    // 🧊 Glassmorphism Components
    glass: {
        base:    "rgba(255, 255, 255, 0.7)",   // Translucent White
        border:  "rgba(255, 255, 255, 0.5)",   // Glowing White Border
        shadow:  "rgba(44, 125, 160, 0.15)",   // Soft Blue Shadow
        dark:    "rgba(44, 125, 160, 0.9)",    // Translucent Dark Blue (for sidebar)
    },
    
    // 💎 Brand Accents
    primary: {
        light:   "#46A6C9",    
        DEFAULT: "#2C7DA0",    // Primary Brand Blue
        dark:    "#1B5E7A",    
    },

    // ✨ Functional States
    success:    "#059669",     
    warning:    "#D97706",     
    danger:     "#DC2626",     
    
    // ✍️ Typography
    text: {
        DEFAULT: "#1E3D4A",    // Deep Navy Slate (Ultra-readable)
        body:    "#3A606E",    
        muted:   "#5F8B9C",    
        white:   "#FFFFFF",    
    },

    // 🌊 Gradients
    gradients: {
        main:  "linear-gradient(135deg, #A9D6E5 0%, #FFFFFF 100%)",
        glass: "linear-gradient(135deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.4))",
        brand: "linear-gradient(90deg, #2C7DA0, #46A6C9)",
    }
};

export default colors;
