# 📄 AI Resume Parser & Job Matcher 🚀  

Smart Resume Match is an AI-powered application that helps streamline the job search process by analyzing a user’s resume to extract key information such as skills, job titles, and location.
It then finds relevant job listings from LinkedIn based on the extracted data and ranks them using a combination of keyword matching and AI-based similarity scoring.
The goal is to assist users in discovering job opportunities that align closely with their background and experience — all in a single, easy-to-use interface.


[![Database](https://img.shields.io/badge/LLM-Claude%20Haiku-4b0082?style=for-the-badge)](https://www.anthropic.com/index/claude)
[![Frontend](https://img.shields.io/badge/Frontend-Streamlit-ff4b4b?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![Language](https://img.shields.io/badge/Language-Python-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Project](https://img.shields.io/badge/Project-AI%20NLP-grey?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-Completed-brightgreen?style=for-the-badge)]()


---


## 🌟 Features  
✅ **Extracts Resume Data**: Key skills, job titles, and contact details  
✅ **AI-powered Resume Summary & Improvement Suggestions** (Claude AI)  
✅ **Fetches Live Job Listings**   
✅ **Ranks Jobs Based on Resume Match**  
✅ **Supports Multiple Locations**  

📸 **Demo Screenshots**  

<img width="1380" alt="Screenshot 2025-03-16 at 10 47 32 PM" src="https://github.com/user-attachments/assets/098c5378-26d4-4285-bb4c-27bccbb5ab8d" />

<img width="1353" alt="Screenshot 2025-03-16 at 10 49 17 PM" src="https://github.com/user-attachments/assets/23d4d3c7-7fd3-4d6d-8528-5691a4c188b6" />

<img width="1495" alt="Screenshot 2025-03-16 at 10 49 50 PM" src="https://github.com/user-attachments/assets/3223eccc-34be-4809-9e84-28339567b8e0" />

<img width="1476" alt="Screenshot 2025-03-16 at 10 50 14 PM" src="https://github.com/user-attachments/assets/a34be1b9-5f26-404f-b63d-acd6a918a414" />

<img width="1275" alt="Screenshot 2025-03-16 at 10 50 23 PM" src="https://github.com/user-attachments/assets/7067a2a5-19e0-45c4-bdc5-1791eed05c17" />


---

## 🛠️ Tech Stack

-  **Python** – Core programming language
-  **pdfminer.six** – For extracting text from uploaded PDF resumes
-  **Claude Haiku (Anthropic API)** – Used for:
    - Summarizing resumes
    - Suggesting improvements
    - Extracting structured info with LLM
- 🖥️ **Streamlit** – For building the frontend web interface

---


Run the following commands in your terminal to **set up and run the application**:  


# Set Up API Key (Ensure you replace 'your-api-key-here' with your actual key)
export ANTHROPIC_API_KEY="your-api-key-here"

# Run the Application
streamlit run Smart\ Resume\ Match.py
