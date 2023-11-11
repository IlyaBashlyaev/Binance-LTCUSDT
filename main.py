from flask import Flask, render_template
import requests, json
import numpy as np
import pandas as pd

app = Flask(__name__)
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'accept': '*/*'
}

@app.route('/')
def index():
    return render_template('index.html', limit = 1000)

@app.route('/<int:limit>')
def limit(limit):
    return render_template('index.html', limit = limit)

@app.route('/chart/<int:limit>')
def chart(limit):
    data = requests.get('https://www.binance.com/fapi/v1/klines?symbol=LTCUSDT&interval=5m&limit=' + str(limit), headers = headers)
    data = json.loads(data.text)

    newData = []
    markers = []
    trend = ''
    rsiFlag = False
    rsi0 = -1

    for i in range(0, len(data)):
        newData.append(float(data[i][4]))

    pdData = {}
    pdData['close'] = newData
    pdData = pd.DataFrame(data = pdData)
    
    delta = pdData['close'].diff()
    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha = 1 / 14).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha = 1 / 14).mean()

    rsi = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))
    rsi = np.round(rsi, 2)

    rsi = pd.Series(rsi)
    stochrsi = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min())

    stochrsi_K = stochrsi.rolling(3).mean()
    stochrsi_D = stochrsi_K.rolling(3).mean()

    new_rsi = []
    new_stochrsi_K = []
    new_stochrsi_D = []

    for i in range(18, len(data)):
        stochrsi_K[i] *= 100
        stochrsi_D[i] *= 100

        if stochrsi_K[i] > 20 and stochrsi_K[i - 1] <= 20 and (not trend or trend == 'Sell'):
            trend = 'Buy'

            markers.append({
                'time': data[i][0] / 1000,
                'position': 'belowBar',
                'color': '#26a69a',
                'shape': 'arrowUp',
                'text': 'Buy'
            })

        elif stochrsi_K[i] < 80 and stochrsi_K[i - 1] >= 80 and (not trend or trend == 'Buy'):
            trend = 'Sell'

            markers.append({
                'time': data[i][0] / 1000,
                'position': 'aboveBar',
                'color': '#ef5350',
                'shape': 'arrowDown',
                'text': 'Sell'
            })
        
        elif stochrsi_D[i] > stochrsi_K[i] and trend == 'Buy' or stochrsi_K[i] > stochrsi_D[i] and trend == 'Sell':
            if not rsiFlag:
                rsi0 = rsi[i]
                rsiFlag = True
            
            elif rsi[i] - rsi0 >= 5 and trend == 'Sell':
                trend = 'Buy'
                rsiFlag = False

                markers.append({
                    'time': data[i][0] / 1000,
                    'position': 'belowBar',
                    'color': '#26a69a',
                    'shape': 'arrowUp',
                    'text': 'Buy'
                })

            elif rsi0 - rsi[i] >= 5 and trend == 'Buy':
                trend = 'Sell'
                rsiFlag = False

                markers.append({
                    'time': data[i][0] / 1000,
                    'position': 'aboveBar',
                    'color': '#ef5350',
                    'shape': 'arrowDown',
                    'text': 'Sell'
                })
        
        else:
            rsiFlag = False
        
        new_rsi.append([data[i][0] / 1000, rsi[i]])
        new_stochrsi_K.append([data[i][0] / 1000, stochrsi_K[i]])
        new_stochrsi_D.append([data[i][0] / 1000, stochrsi_D[i]])

    return render_template('chart.html', data = data, rsi = new_rsi, stochrsi_K = new_stochrsi_K, stochrsi_D = new_stochrsi_D, markers = markers)

app.run(debug = True)