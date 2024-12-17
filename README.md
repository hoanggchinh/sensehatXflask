### HoanggHuuChinh
### K215480106007 
# Bài 1
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
