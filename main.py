import requests
import time

def send_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Pingged", url, "at", time.strftime("%H:%M:%S"))
        else:
            print("Failed to send request to", url, ". Status code:", response.status_code)
    except requests.RequestException as e:
        print("Error:", e)

if __name__ == "__main__":
    print("Script made by jashgro (https://bit.ly/jashgro)\nUpdates on https://github.com/BlackHatDevX/Render-Pinger")

    option = input("Do you want to enter multiple URLs? (yes/no): ").lower()

    if option == "yes":
        urls = input("Enter the URLs separated by space: ").split()
    else:
        url = input("Enter the URL: ")
        urls = [url]

    interval = int(input("Enter the time interval between requests (in seconds): "))

    while True:
        for url in urls:
            send_request(url)
        time.sleep(interval)

# https://quikeyfy.onrender.com/ https://chotu-ly.onrender.com/ https://upi-payment-gateway-demo.onrender.com/ https://authsystems.onrender.com/