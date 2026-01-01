# ✈️ Luxe AI Travel Agent

A sophisticated, AI-powered travel planning application built with **Python**, **Streamlit**, and **OpenAI**. This tool generates highly detailed, visually rich travel itineraries in PDF format, complete with daily schedules, logistics, food recommendations, and Google Maps links. It then automatically emails the PDF to the user and saves a local copy.

---

## ✨ Features

- **AI-Generated Itineraries**  
  Uses GPT-4 to create realistic, day-by-day travel plans based on your budget, vibe, and duration.

- **Visual Richness**  
  Dynamically fetches high-quality images for every destination using the **Unsplash API**.

- **Professional PDF Export**  
  Generates a “Travel Brochure” style PDF with:
  - Summary table  
  - Side-by-side text and image layout  
  - Clickable Google Maps links  

- **Smart Logistics**  
  Provides specific transport advice (e.g., *“Take Metro Line 1”*) and *Best Time to Visit* suggestions.

- **Foodie Guide**  
  Suggests curated **Veg 🥗** and **Non-Veg 🍗** restaurants near every stop.

- **Email Automation**  
  Instantly emails the itinerary PDF to the user.

- **Local Backup**  
  Automatically saves a copy of the PDF to your local machine.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **AI Core:** OpenAI API (GPT-4)  
- **Image Sourcing:** Unsplash API  
- **PDF Engine:** ReportLab  
- **Email:** Python `smtplib`

---

## 🚀 Setup Instructions

### 1. Prerequisites

- Python **3.8+**
- OpenAI API Key
- Unsplash Access Key
- Gmail App Password

---

### 2. Installation

Create a project folder and install dependencies:

```bash
pip install streamlit openai requests reportlab python-dotenv pillow



🔐 Environment Variables Setup (.env file)

Create a file named .env in the root of your project directory.

⚠️ Important:

Do NOT commit this file to GitHub

Add .env to .gitignore

# OpenAI API Key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx

# Unsplash API Key
UNSPLASH_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Email configuration (Gmail)
SENDER_EMAIL=your.email@gmail.com

# Gmail App Password (NOT your Gmail login password)
# Generate here: https://myaccount.google.com/apppasswords
SENDER_PASSWORD=xxxx xxxx xxxx xxxx

▶️ How to Run the Application

Open your terminal in the project directory

Start the Streamlit app:

streamlit run travel_agent.py


The application will open automatically in your browser
(usually at http://localhost:8501
)

Enter:

Source location

Destination

Number of days

Budget

Email address

Click “Generate My Dream Itinerary”

📂 Output

After successful execution:

📧 Email Output
The user receives the itinerary PDF as an email attachment.

💾 Local Output
A PDF file named:

Destination_Luxury_Itinerary.pdf


will be saved in the project directory.

⚠️ Troubleshooting
❌ Email Authentication Error

Use a Google App Password, not your Gmail login password

Ensure 2-Step Verification is enabled in your Google account

❌ OpenAI API Error

Check if your API key is valid

Verify billing is enabled

Ensure you have sufficient API credits

❌ Images Not Loading

Confirm your Unsplash API key is correct

Check Unsplash API rate limits

Ensure internet connectivity

❌ App Not Starting

Verify Python version:

python --version


Ensure all dependencies are installed:

pip install -r requirements.txt

📄 License

This project is open-source.
Feel free to fork, customize, and enhance it for your own use 🚀
