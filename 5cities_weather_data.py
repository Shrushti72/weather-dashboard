import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def get_weather_data(city_name):
    url = f"https://www.timeanddate.com/weather/?query={city_name}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to find the first city link directly
    first_result_link = soup.select_one('.zebra.tb-theme a')
    if first_result_link and first_result_link.has_attr('href'):
        city_link = "https://www.timeanddate.com" + first_result_link['href']
        city_response = requests.get(city_link, headers=headers)
        city_soup = BeautifulSoup(city_response.text, 'html.parser')

        temp = city_soup.select_one('.h2').text.strip()
        condition = city_soup.select_one('.bk-focus__qlook span').text.strip()
        details = city_soup.select('.bk-focus__info tr')

        if "°F" in temp:
            f = float(temp.replace("°F", "").strip())
            celsius = round((f - 32) * 5/9, 1)
        else:
            celsius = float(temp.replace("°C", "").strip())
            
        weather_data = {
            "City": city_name,
            "Temperature (°C)": celsius,
            "Condition": condition
            }
        for row in details:
            tds = row.find_all('td')
            if len(tds) == 2:
                label = tds[0].text.strip().replace(":", "")
                value = tds[1].text.strip()
                if "Humidity" in label:
                    try:
                        weather_data["Humidity (%)"] = int(value.replace("%", "").strip())
                    except:
                        weather_data["Humidity (%)"] = None

        return weather_data
    else:
        return None
# ----------- Streamlit UI -----------

st.set_page_config(page_title="Weather Dashboard", layout="centered")
st.title("🌦️ Real-Time Weather Dashboard")

default_cities = ["Pune", "Mumbai", "Delhi", "Bangalore", "Chennai"]
cities = st.text_input("Enter 5 cities separated by comma:", ", ".join(default_cities))

if st.button("Fetch Weather"):
    city_list = [c.strip() for c in cities.split(",")][:5]
    all_weather = []

    for city in city_list:
        data = get_weather_data(city)
        if data:
            all_weather.append(data)
        else:
            st.warning(f"No data found for {city}.")

    if all_weather:
        df = pd.DataFrame(all_weather)
        st.subheader("📋 Weather Data")
        st.dataframe(df)

        # Ensure Humidity column exists for all rows
        if "Humidity (%)" not in df.columns:
            df["Humidity (%)"] = None
        df["Humidity (%)"] = df["Humidity (%)"].fillna(0)

        # Save to CSV
        df.to_csv("weather_data_5_cities.csv", index=False)

        # --- Plotting ---
        st.subheader("📊 Temperature & Humidity Comparison")
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        cities = df["City"]
        temps = df["Temperature (°C)"]
        humidity = df["Humidity (%)"]

        ax1.bar(cities, temps, color='skyblue', label="Temp (°C)", width=0.4, align='edge')
        ax2.bar(cities, humidity, color='orange', label="Humidity (%)", width=-0.4, align='edge')

        ax1.set_ylabel("Temperature (°C)", color='skyblue')
        ax2.set_ylabel("Humidity (%)", color='orange')
        plt.title("Temperature & Humidity for Selected Cities")

        ax1.tick_params(axis='y', labelcolor='skyblue')
        ax2.tick_params(axis='y', labelcolor='orange')

        st.pyplot(fig)

        # Download button (unique key)
        st.download_button("Download CSV", df.to_csv(index=False), "weather_data.csv", "text/csv", key="download_csv")