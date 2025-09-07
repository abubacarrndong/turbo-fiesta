# Gambia AI Inventory Forecast

This is a Streamlit web app for Gambian shops to upload sales data and get AI-powered inventory forecasts.

## How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run streamlit_inventory_app.py
   ```
3. Open the local URL shown in your browser.

## How to Deploy on Streamlit Cloud
1. Create a GitHub repo and upload these files.
2. Go to https://share.streamlit.io/ and deploy the app.
3. Your shopkeepers can then use the public URL to access the app.

## Input Format
CSV file with columns:
- Date
- Product
- Units_Sold
- Current_Stock (optional)

