from flask import Flask, render_template_string
from sense_emu import SenseHat
import sqlite3
import pyrebase
import time
from threading import Thread

# -------------------------------------------
# Cấu hình Firebase
config = {
    "apiKey": "AIzaSyCpbeebwlIeKHOkWwsd-phmbI8DB4DKRw8",
    "authDomain": "testrasp-23267.firebaseapp.com",
    "databaseURL": "https://testrasp-23267-default-rtdb.firebaseio.com",
    "projectId": "testrasp-23267",
    "storageBucket": "testrasp-23267.appspot.com",
    "messagingSenderId": "784549425966",
    "appId": "1:784549425966:web:1f65f04c76d02cff61c0bf",
    "measurementId": "G-Z3P1YSMVM0"
}

# -------------------------------------------
# Khởi tạo Firebase, SenseHat và Flask
firebase = pyrebase.initialize_app(config)
database = firebase.database()
sense = SenseHat()
app = Flask(__name__)


# -------------------------------------------
# SQLite Database Setup
def init_db():
    conn = sqlite3.connect("temperature_data.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS temperatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Hàm lưu nhiệt độ vào SQLite
def save_to_sqlite(t):
    conn = sqlite3.connect("temperature_data.db")
    c = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO temperatures (temperature, timestamp) VALUES (?, ?)', (t, timestamp))
    conn.commit()
    conn.close()


# Hàm tính trung bình TB(A, n)
def calculate_average(A):
    if len(A) == 0:
        return 0
    return round(sum(A) / len(A), 2)


# -------------------------------------------
# Biến toàn cục
temperature = 0.0
humidity = 0.0
pressure = 0.0
joystick_pos = (4, 4)  # Toạ độ joystick
average_temperature = 0.0
A = [ ]  # Mảng lưu lịch sử nhiệt độ
tUpdate = 0.0  # Biến tUpdate


# Hàm đọc dữ liệu từ SenseHat và xử lý
def update_data():
    global temperature, humidity, pressure, joystick_pos, average_temperature, A, tUpdate
    while True:
        # Đọc nhiệt độ, độ ẩm, áp suất từ SenseHat
        temperature = round(sense.get_temperature(), 1)
        humidity = round(sense.get_humidity(), 1)
        pressure = round(sense.get_pressure(), 1)

        # Tính tUpdate theo công thức: tUpdate = (t + TB(A, n)) / 2
        n = len(A)
        tUpdate = round((temperature + calculate_average(A)) / 2, 1)

        # Chỉ gửi dữ liệu lên Firebase khi tUpdate != t
        if tUpdate != temperature:
            # Lưu nhiệt độ vào SQLite
            save_to_sqlite(temperature)

            # Cập nhật mảng A và tính TB(A, n)
            if len(A) >= 5:  # Giới hạn mảng A tối đa 5 phần tử
                A.pop(0)
            A.append(tUpdate)
            average_temperature = calculate_average(A)

            # Gửi tUpdate lên Firebase
            sensor_data = {
                "average_temperature": average_temperature,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            database.child("OptimizedSensorData").set(sensor_data)
            print(
                f"Nhiệt độ hiện tại: {temperature} °C | Trung bình TB(A, n): {average_temperature} °C | tUpdate: {tUpdate}")

        time.sleep(2)  # Cập nhật mỗi 2 giây


# -------------------------------------------
# Giao diện HTML cho Flask
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SenseHat Temperature Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; }
        h1 { color: #333; }
        p { font-size: 1.5em; }
    </style>
</head>
<body>
    <h1>SenseHat Temperature Dashboard</h1>
    <p><strong>Nhiệt độ hiện tại:</strong> {{ temperature }} °C</p>
    <p><strong>Trung bình nhiệt độ (TB):</strong> {{ average_temperature }} °C</p>
    <p><strong>Độ ẩm:</strong> {{ humidity }} %</p>
    <p><strong>Áp suất:</strong> {{ pressure }} hPa</p>
    <p><strong>Trạng thái Joystick:</strong> x={{ joystick_pos[0] }}, y={{ joystick_pos[1] }}</p>
</body>
</html>
"""


# -------------------------------------------
# Flask Route
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE,
                                  temperature=temperature,
                                  average_temperature=average_temperature,
                                  humidity=humidity,
                                  pressure=pressure,
                                  joystick_pos=joystick_pos)


# -------------------------------------------
# Route để hiển thị dữ liệu từ SQLite
@app.route("/view_data")
def view_data():
    conn = sqlite3.connect("temperature_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM temperatures")
    data = c.fetchall()
    conn.close()

    # Tạo HTML hiển thị dữ liệu
    html_data = "<h1>Temperature Data</h1><table border='1'><tr><th>ID</th><th>Temperature</th><th>Timestamp</th></tr>"
    for row in data:
        html_data += f"<tr><td>{row [ 0 ]}</td><td>{row [ 1 ]}</td><td>{row [ 2 ]}</td></tr>"
    html_data += "</table>"

    return html_data


# Chạy các luồng
if __name__ == "__main__":
    init_db()  # Khởi tạo SQLite database
    # Chạy luồng đọc dữ liệu và xử lý
    data_thread = Thread(target=update_data, daemon=True)
    data_thread.start()

    # Chạy Flask
    app.run(host="0.0.0.0", port=5001, debug=True)