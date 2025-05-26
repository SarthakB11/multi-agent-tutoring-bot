"""
Configuration settings for the Multi-Agent AI Tutoring System.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Server Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

# Database Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/tutoring_bot")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "tutoring_bot")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Agent Configuration
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
HIGH_CONFIDENCE_THRESHOLD = 0.9
LOW_CONFIDENCE_THRESHOLD = 0.5

# Tool Configuration
CALCULATOR_TIMEOUT_SECONDS = 5
LOOKUP_TIMEOUT_SECONDS = 5

# Gemini API Configuration
GEMINI_MODEL = "gemini-pro"
GEMINI_MAX_TOKENS = 1024
GEMINI_TEMPERATURE = 0.7

# Constants for Physics Lookup Tool
PHYSICS_CONSTANTS = {
    "g": {"value": 9.81, "unit": "m/s²", "description": "Acceleration due to gravity on Earth"},
    "c": {"value": 299792458, "unit": "m/s", "description": "Speed of light in vacuum"},
    "G": {"value": 6.67430e-11, "unit": "m³/(kg·s²)", "description": "Gravitational constant"},
    "h": {"value": 6.62607015e-34, "unit": "J·s", "description": "Planck constant"},
    "e": {"value": 1.602176634e-19, "unit": "C", "description": "Elementary charge"},
    "me": {"value": 9.1093837015e-31, "unit": "kg", "description": "Electron mass"},
    "mp": {"value": 1.67262192369e-27, "unit": "kg", "description": "Proton mass"},
    "k": {"value": 1.380649e-23, "unit": "J/K", "description": "Boltzmann constant"},
    "NA": {"value": 6.02214076e23, "unit": "mol⁻¹", "description": "Avogadro constant"},
    "R": {"value": 8.31446261815324, "unit": "J/(mol·K)", "description": "Gas constant"},
}

# Physics Formulas
PHYSICS_FORMULAS = {
    "newton_second_law": {
        "formula": "F = m·a",
        "description": "Newton's Second Law: Force equals mass times acceleration",
        "variables": {"F": "Force (N)", "m": "Mass (kg)", "a": "Acceleration (m/s²)"}
    },
    "kinetic_energy": {
        "formula": "KE = 0.5·m·v²",
        "description": "Kinetic Energy: The energy of motion",
        "variables": {"KE": "Kinetic Energy (J)", "m": "Mass (kg)", "v": "Velocity (m/s)"}
    },
    "potential_energy_gravitational": {
        "formula": "PE = m·g·h",
        "description": "Gravitational Potential Energy: Energy due to position in a gravitational field",
        "variables": {"PE": "Potential Energy (J)", "m": "Mass (kg)", "g": "Gravitational acceleration (m/s²)", "h": "Height (m)"}
    },
    "momentum": {
        "formula": "p = m·v",
        "description": "Momentum: Product of mass and velocity",
        "variables": {"p": "Momentum (kg·m/s)", "m": "Mass (kg)", "v": "Velocity (m/s)"}
    },
    "uniform_acceleration": {
        "formula": "v = v₀ + a·t",
        "description": "Velocity with uniform acceleration",
        "variables": {"v": "Final velocity (m/s)", "v₀": "Initial velocity (m/s)", "a": "Acceleration (m/s²)", "t": "Time (s)"}
    },
    "uniform_acceleration_distance": {
        "formula": "d = v₀·t + 0.5·a·t²",
        "description": "Distance with uniform acceleration",
        "variables": {"d": "Distance (m)", "v₀": "Initial velocity (m/s)", "a": "Acceleration (m/s²)", "t": "Time (s)"}
    },
    "work": {
        "formula": "W = F·d·cos(θ)",
        "description": "Work done by a constant force",
        "variables": {"W": "Work (J)", "F": "Force (N)", "d": "Distance (m)", "θ": "Angle between force and displacement (rad)"}
    },
    "power": {
        "formula": "P = W/t",
        "description": "Power: Rate of doing work",
        "variables": {"P": "Power (W)", "W": "Work (J)", "t": "Time (s)"}
    },
    "ohms_law": {
        "formula": "V = I·R",
        "description": "Ohm's Law: Relationship between voltage, current, and resistance",
        "variables": {"V": "Voltage (V)", "I": "Current (A)", "R": "Resistance (Ω)"}
    },
    "universal_gravitation": {
        "formula": "F = G·(m₁·m₂)/r²",
        "description": "Newton's Law of Universal Gravitation",
        "variables": {"F": "Force (N)", "G": "Gravitational constant (m³/(kg·s²))", "m₁": "Mass 1 (kg)", "m₂": "Mass 2 (kg)", "r": "Distance between centers (m)"}
    }
}
