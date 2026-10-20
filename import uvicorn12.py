import math
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Gриша Controller")

# ============================================================
#  СОСТОЯНИЕ РОБОТА
# ============================================================
FIELD_MIN = -10      # поле 20x20, робот стартует в центре (0,0)
FIELD_MAX = 10
STEP = 1.0           # шаг движения в единицах поля

robot = {
    "x": 0.0,
    "y": 0.0,
    "direction": 0.0,   # градусы: 0=север, 90=восток, 180=юг, 270=запад
}


# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------
def _in_bounds(x, y):
    return FIELD_MIN <= x <= FIELD_MAX and FIELD_MIN <= y <= FIELD_MAX


def _direction_name(angle):
    """Возвращает буквенное обозначение или пустую строку."""
    angle = angle % 360
    for a, n in [(0, "N"), (45, "NE"), (90, "E"), (135, "SE"),
                 (180, "S"), (225, "SW"), (270, "W"), (315, "NW")]:
        if abs((angle - a + 180) % 360 - 180) < 22.5:
            return n
    return ""


def _status_dict(status="ok", message=None):
    angle = robot["direction"] % 360
    d = {
        "status": status,
        "position": {"x": round(robot["x"], 2), "y": round(robot["y"], 2)},
        "direction": round(angle, 2),
        "direction_name": _direction_name(angle),
        "field": {"min": FIELD_MIN, "max": FIELD_MAX},
    }
    if message:
        d["message"] = message
    return d


def _try_move(sign):
    rad = math.radians(robot["direction"])
    dx = math.sin(rad) * STEP * sign   # 0° -> (0,+1) север
    dy = math.cos(rad) * STEP * sign
    nx, ny = robot["x"] + dx, robot["y"] + dy
    if not _in_bounds(nx, ny):
        return _status_dict("error", "Достигнута граница поля")
    robot["x"], robot["y"] = nx, ny
    return _status_dict()


# ---------- КОМАНДЫ ----------
def move_forward():
    print(f"Гриша: ВПЕРЁД -> ({robot['x']:.2f}, {robot['y']:.2f})")
    return _try_move(+1)


def move_backward():
    print(f"Гриша: НАЗАД -> ({robot['x']:.2f}, {robot['y']:.2f})")
    return _try_move(-1)


def turn_left(angle=90.0):
    """Поворот НАЛЕВО (против часовой) на angle градусов."""
    robot["direction"] = (robot["direction"] - angle) % 360
    print(f"Гриша: ПОВОРОТ НАЛЕВО на {angle}° -> {robot['direction']:.1f}°")
    return _status_dict()


def turn_right(angle=90.0):
    """Поворот НАПРАВО (по часовой) на angle градусов."""
    robot["direction"] = (robot["direction"] + angle) % 360
    print(f"Гриша: ПОВОРОТ НАПРАВО на {angle}° -> {robot['direction']:.1f}°")
    return _status_dict()


def set_direction(angle):
    """Установить абсолютное направление (0..360)."""
    robot["direction"] = float(angle) % 360
    print(f"Гриша: НАПРАВЛЕНИЕ = {robot['direction']:.1f}°")
    return _status_dict()


def stop_robot():
    return _status_dict()


# ============================================================
#  API
# ============================================================
@app.get("/forward")
def api_forward():
    return move_forward()


@app.get("/backward")
def api_backward():
    return move_backward()


@app.get("/left")
def api_left(angle: float = 90.0):
    """Поворот НАЛЕВО (против часовой) на N градусов. По умолчанию 90."""
    angle = max(0.0, min(360.0, angle))
    return turn_left(angle)


@app.get("/right")
def api_right(angle: float = 90.0):
    """Поворот НАПРАВО (по часовой) на N градусов. По умолчанию 90."""
    angle = max(0.0, min(360.0, angle))
    return turn_right(angle)


@app.get("/set_direction")
def api_set_direction(angle: float = 0.0):
    """Установить абсолютное направление (0..360)."""
    angle = max(0.0, min(360.0, angle))
    return set_direction(angle)


@app.get("/stop")
def api_stop():
    return stop_robot()


@app.get("/status")
def api_status():
    return _status_dict()


@app.get("/reset")
def api_reset():
    robot["x"], robot["y"], robot["direction"] = 0.0, 0.0, 0.0
    print("Гриша: РЕСЕТ -> (0,0), 0°")
    return _status_dict()


# ============================================================
#  ВЕБ-ИНТЕРФЕЙС
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def control_panel():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Управление роботом Гриша</title>
  <style>
    body { font-family: Arial, sans-serif; background: #eef1f4; margin: 0; padding: 20px; }
    h1 { text-align: center; color: #333; margin: 0 0 20px; }
    .layout {
      display: flex; gap: 24px; justify-content: center; align-items: flex-start;
      flex-wrap: wrap;
    }
    .card {
      background: #fff; padding: 16px; border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,.08);
    }
    canvas { display: block; background: #fafafa; border-radius: 8px; }

    .controls { display: grid; grid-template-columns: repeat(3, 110px); gap: 10px; }
    button {
      padding: 14px; font-size: 15px; border: none; border-radius: 8px;
      background: #4CAF50; color: #fff; cursor: pointer; transition: background .15s;
    }
    button:hover { background: #43a047; }
    .stop-btn { background: #f44336; }
    .stop-btn:hover { background: #e53935; }
    .reset-btn { background: #607d8b; }
    .reset-btn:hover { background: #546e7a; }

    .slider-block {
      margin-top: 14px; padding: 10px 12px; background: #fff8e1; border-radius: 10px;
    }
    .slider-block .head {
      display: flex; justify-content: space-between; align-items: center;
      font-size: 14px; color: #6d4c00; font-weight: bold; margin-bottom: 6px;
    }
    .slider-block .head .val {
      color: #e65100; font-size: 17px; font-weight: bold;
    }
    .slider-block input[type="range"] {
      width: 100%; accent-color: #ff9800; cursor: pointer;
    }
    .slider-block .hint {
      font-size: 12px; color: #8d6e63; margin-top: 4px;
    }

    .rotate-block {
      margin-top: 14px; padding: 10px 12px; background: #f5f7fa; border-radius: 10px;
    }
    .rotate-block .head {
      font-size: 14px; color: #37474f; font-weight: bold; margin-bottom: 6px;
    }
    .rotate-block .row {
      display: flex; align-items: center; gap: 8px;
    }
    .rotate-block input[type="number"] {
      width: 80px; padding: 8px; font-size: 15px; border: 1px solid #ccc;
      border-radius: 8px; text-align: center;
    }
    .rotate-block input.invalid { border-color: #e53935; background: #ffebee; }
    .turn-btn { background: #ff9800; flex: 1; padding: 12px; }
    .turn-btn:hover { background: #fb8c00; }

    .info {
      margin-top: 16px; padding: 12px 16px; background: #f5f7fa; border-radius: 8px;
      font-size: 15px; line-height: 1.6;
    }
    .info .row { margin: 4px 0; color: #444; }
    .info .row b {
      color: #2e7d32; font-size: 18px; min-width: 75px; display: inline-block;
    }
    .error { color: #e53935; font-weight: bold; display: block; margin-top: 6px; }
  </style>
</head>
<body>
  <h1>🤖 Управление роботом «Гриша»</h1>
  <div class="layout">
    <div class="card">
      <canvas id="field" width="440" height="440"></canvas>
    </div>
    <div class="card">
      <div class="controls">
        <div></div>
        <button onclick="send('forward')">⬆️ Вперёд</button>
        <div></div>
        <div></div>
        <button onclick="send('backward')">⬇️ Назад</button>
        <div></div>
        <button onclick="send('stop')" class="stop-btn" style="grid-column: span 3;">⏹️ СТОП</button>
        <button onclick="send('reset')" class="reset-btn" style="grid-column: span 3;">🔄 Сброс в центр</button>
      </div>

      <!-- Ползунок: абсолютное направление -->
      <div class="slider-block">
        <div class="head">
          <span>Направление робота (0–360°)</span>
          <span class="val" id="slider-value">0°</span>
        </div>
        <input id="angle-slider" type="range" min="0" max="360" step="1" value="0">
        <div class="hint">Двигайте — робот поворачивается сразу</div>
      </div>

      <!-- Относительный поворот кнопками -->
      <div class="rotate-block">
        <div class="head">Повернуть кнопками на N°</div>
        <div class="row">
          <input id="angle" type="number" value="45" step="1" min="0" max="360">
          <span>°</span>
          <button class="turn-btn" onclick="turn('left')">⟲ Налево</button>
          <button class="turn-btn" onclick="turn('right')">⟳ Направо</button>
        </div>
      </div>

      <div class="info">
        <div class="row">X относительно старта: <b id="rel-x">0.00</b></div>
        <div class="row">Y относительно старта: <b id="rel-y">0.00</b></div>
        <div class="row">Угол относительно старта: <b id="rel-a">0.00°</b></div>
        <span id="msg" class="error"></span>
      </div>
    </div>
  </div>

<script>
const canvas = document.getElementById('field');
const ctx = canvas.getContext('2d');
const SIZE = 20;
const FIELD_MIN = -10, FIELD_MAX = 10;
const ANGLE_MIN = 0, ANGLE_MAX = 360;

const slider = document.getElementById('angle-slider');
const sliderValue = document.getElementById('slider-value');
const angleInput = document.getElementById('angle');

let lastStatus = {
  position: { x: 0, y: 0 },
  direction: 0,
  direction_name: '',
  status: 'ok'
};

const toX = wx => ((wx - FIELD_MIN) / SIZE) * canvas.width;
const toY = wy => ((FIELD_MAX - wy) / SIZE) * canvas.height;

function draw(st) {
  const W = canvas.width, H = canvas.height;

  ctx.fillStyle = '#fafafa';
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = '#e0e0e0';
  ctx.lineWidth = 1;
  for (let i = FIELD_MIN; i <= FIELD_MAX; i += 5) {
    const x = toX(i), y = toY(i);
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }

  ctx.strokeStyle = '#c0c0c0';
  ctx.beginPath();
  ctx.moveTo(toX(0), 0); ctx.lineTo(toX(0), H);
  ctx.moveTo(0, toY(0)); ctx.lineTo(W, toY(0));
  ctx.stroke();

  ctx.strokeStyle = '#333';
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, W - 2, H - 2);

  ctx.fillStyle = '#999';
  ctx.font = 'bold 12px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('N', W / 2, 16);
  ctx.fillText('S', W / 2, H - 6);
  ctx.textAlign = 'left';
  ctx.fillText('E', W - 16, H / 2 - 6);
  ctx.textAlign = 'right';
  ctx.fillText('W', 16, H / 2 - 6);

  const rx = toX(st.position.x);
  const ry = toY(st.position.y);
  const angleRad = (st.direction - 90) * Math.PI / 180;
  const dx = Math.cos(angleRad), dy = Math.sin(angleRad);

  const arrowLen = 30;
  ctx.strokeStyle = '#f44336';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(rx, ry);
  ctx.lineTo(rx + dx * arrowLen, ry + dy * arrowLen);
  ctx.stroke();

  const hl = 9, ha = 0.5;
  ctx.beginPath();
  ctx.moveTo(rx + dx * arrowLen, ry + dy * arrowLen);
  ctx.lineTo(rx + dx * arrowLen - Math.cos(angleRad - ha) * hl,
             ry + dy * arrowLen - Math.sin(angleRad - ha) * hl);
  ctx.moveTo(rx + dx * arrowLen, ry + dy * arrowLen);
  ctx.lineTo(rx + dx * arrowLen - Math.cos(angleRad + ha) * hl,
             ry + dy * arrowLen - Math.sin(angleRad + ha) * hl);
  ctx.stroke();

  ctx.fillStyle = '#4CAF50';
  ctx.strokeStyle = '#2e7d32';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(rx, ry, 10, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = '#333';
  ctx.font = 'bold 12px Arial';
  ctx.textAlign = 'left';
  ctx.fillText(`(${st.position.x}, ${st.position.y})`, rx + 16, ry - 16);
}

function updateFromStatus(st) {
  lastStatus = st;
  draw(st);

  document.getElementById('rel-x').textContent = st.position.x.toFixed(2);
  document.getElementById('rel-y').textContent = st.position.y.toFixed(2);
  document.getElementById('rel-a').textContent = st.direction.toFixed(2) + '°';

  document.getElementById('msg').textContent =
    st.status === 'error' ? (st.message || '') : '';

  // Ползунок всегда отражает текущее направление робота
  const dir = Math.round(st.direction) % 360;
  slider.value = dir;
  sliderValue.textContent = dir + '°';
}

async function send(cmd) {
  try {
    const r = await fetch('/' + cmd);
    updateFromStatus(await r.json());
  } catch (e) { console.error(e); }
}

async function setDirection(angle) {
  try {
    const r = await fetch(`/set_direction?angle=${angle}`);
    updateFromStatus(await r.json());
  } catch (e) { console.error(e); }
}

async function turn(side) {
  const angle = parseFloat(angleInput.value);
  if (isNaN(angle) || angle < ANGLE_MIN || angle > ANGLE_MAX) {
    angleInput.classList.add('invalid');
    alert(`Угол должен быть числом от ${ANGLE_MIN} до ${ANGLE_MAX}°`);
    return;
  }
  angleInput.classList.remove('invalid');

  try {
    const r = await fetch(`/${side}?angle=${angle}`);
    updateFromStatus(await r.json());
  } catch (e) { console.error(e); }
}

// --- Ползунок: живой поворот ---
// 'input' — пока пользователь тянет ползунок, обновляем только локально (canvas + подпись).
slider.addEventListener('input', () => {
  const v = parseFloat(slider.value);
  sliderValue.textContent = v + '°';
  draw({ ...lastStatus, direction: v });
});

// 'change' — срабатывает на отпускание ползунка (или Enter).
// Отправляем на сервер и получаем актуальное состояние.
slider.addEventListener('change', () => {
  setDirection(parseFloat(slider.value));
});

// Числовое поле ввода: подсветка ошибки при выходе за 0–360
angleInput.addEventListener('input', () => {
  const v = parseFloat(angleInput.value);
  if (!isNaN(v) && v >= ANGLE_MIN && v <= ANGLE_MAX) {
    angleInput.classList.remove('invalid');
  }
});

// начальное состояние
send('status');
</script>
</body>
</html>
    """


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)