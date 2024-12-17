### HoanggHuuChinh
### K215480106007 
# Bài 1 (app1.py)
### Hiển thị độ ẩm và nhiệt độ, áp suất, vị trí joystick trên web dùng flask
![image](https://github.com/user-attachments/assets/cd5ff7ea-2d4a-4b98-bcaf-d4277338e94f)


```python
from flask import Flask, render_template_string
from sense_emu import SenseHat
import time
from threading import Thread

# Khởi tạo Flask và SenseHat
app = Flask(__name__)
sense = SenseHat()

# Biến toàn cục
temperature, humidity, pressure, joystick_pos = 0.0, 0.0, 0.0, (4, 4)
x, y = 4, 4  # Toạ độ joystick

# Hàm giới hạn giá trị trong phạm vi (0, 7)
def clamp(value, min_value=0, max_value=7):
    return min(max_value, max(min_value, value))

# Hàm di chuyển con trỏ joystick
def move_dot(event):
    global x, y
    if event.action in ('pressed', 'held'):
        x = clamp(x + {
            'left': -1,
            'right': 1,
        }.get(event.direction, 0))
        y = clamp(y + {
            'up': -1,
            'down': 1,
        }.get(event.direction, 0))

# Hàm cập nhật dữ liệu SenseHat
def update_data():
    global temperature, humidity, pressure, joystick_pos
    while True:
        temperature = round(sense.get_temperature(), 1)
        humidity = round(sense.get_humidity(), 1)
        pressure = round(sense.get_pressure(), 1)
        joystick_pos = (x, y)
        for event in sense.stick.get_events():
            move_dot(event)
        time.sleep(1)  # Cập nhật dữ liệu mỗi 1 giây

# Chạy luồng cập nhật dữ liệu
update_thread = Thread(target=update_data, daemon=True)
update_thread.start()

# Template HTML tích hợp sẵn trong code
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SenseHat Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f8f9fa;
            margin-top: 20px;
        }
        h1, h2 {
            color: #333;
        }
        table {
            margin: 0 auto;
            border-collapse: collapse;
        }
        td {
            width: 20px;
            height: 20px;
            text-align: center;
        }
        .black {
            background-color: black;
        }
        .green {
            background-color: green;
        }
        .metrics {
            margin: 20px 0;
        }
        .metrics p {
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <h1>SenseHat Dashboard</h1>
    
    <div class="metrics">
        <h2>Thông tin môi trường</h2>
        <p><strong>Nhiệt độ:</strong> {{ temperature }} °C</p>
        <p><strong>Độ ẩm:</strong> {{ humidity }} %</p>
        <p><strong>Áp suất:</strong> {{ pressure }} hPa</p>
    </div>

    <div class="metrics">
        <h2>Trạng thái Joystick</h2>
        <p>Toạ độ joystick: x={{ joystick_pos[0] }}, y={{ joystick_pos[1] }}</p>
    </div>

    <h2>LED Matrix</h2>
    <table>
        {% for row in led_matrix %}
        <tr>
            {% for pixel in row %}
            <td class="{{ 'green' if pixel == '🟩' else 'black' }}"></td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# Route chính
@app.route("/")
def index():
    led_matrix = [["⬛" for _ in range(8)] for _ in range(8)]
    led_matrix[joystick_pos[1]][joystick_pos[0]] = "🟩"  # Màu xanh lá cho joystick

    return render_template_string(
        HTML_TEMPLATE,
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        joystick_pos=joystick_pos,
        led_matrix=led_matrix
    )

# Chạy ứng dụng Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
```
# Bài 2 (app2.py)
### Gửi thêm dữ liệu lên web
![image](https://github.com/user-attachments/assets/9b7d38ca-1168-4d9e-81b9-bc6982a3e73b)
![image](https://github.com/user-attachments/assets/5ec84750-cbdf-4f61-9926-c9033551c98e)
### Lưu t vào db, tạo 1 html hiển thị dữ liệu
![image](https://github.com/user-attachments/assets/52684a30-4d28-4ded-8eb3-3a360705224e)




```python
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
A = []  # Mảng lưu lịch sử nhiệt độ
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
            print(f"Nhiệt độ hiện tại: {temperature} °C | Trung bình TB(A, n): {average_temperature} °C | tUpdate: {tUpdate}")

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
        html_data += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
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
```
