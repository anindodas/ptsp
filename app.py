import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, session, jsonify, send_from_directory
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
import speech_recognition as sr

app = Flask(__name__)

# Session configuration
app.config.update(
    SECRET_KEY='your-static-secret-key-123',
    SESSION_COOKIE_NAME='distplot_session',
    PERMANENT_SESSION_LIFETIME=604800,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False
)

STYLE_CONFIG = {
    0: {'primary': '#ff6b6b', 'secondary': '#ff8e8e'},
    1: {'primary': '#4ecdc4', 'secondary': '#45b7af'},
    2: {'primary': '#ff9f43', 'secondary': '#ffbe76'},
    3: {'primary': '#6c5ce7', 'secondary': '#a8a5e6'},
    4: {'primary': '#00b894', 'secondary': '#55efc4'},
    5: {'primary': '#d63031', 'secondary': '#ff7675'},
    6: {'primary': '#0984e3', 'secondary': '#74b9ff'},
    7: {'primary': '#e84393', 'secondary': '#fd79a8'},
    8: {'primary': '#00cec9', 'secondary': '#81ecec'},
    9: {'primary': '#fdcb6e', 'secondary': '#ffeaa7'},
    10: {'primary': '#636e72', 'secondary': '#b2bec3'}
}

def generate_plot(distribution, style):
    plt.figure(figsize=(8, 6))
    
    distributions = {
        'uniform': lambda x: np.ones_like(x) * 0.5,
        'gaussian': lambda x: np.exp(-x**2/2) / np.sqrt(2*np.pi),
        'rayleigh': lambda x: x * np.exp(-x**2/2),
        'binomial': lambda x: np.array([np.math.comb(19, k) * (0.5**19) for k in x]),
        'poisson': lambda x: np.exp(-5) * (5**x) / np.array([np.math.factorial(k) for k in x]),
        'laplacian': lambda x: np.exp(-np.abs(x)) / 2
    }
    
    x = np.linspace(-3, 3, 1000) if distribution not in ['binomial', 'poisson'] else np.arange(0, 20)
    pdf = distributions[distribution](x)
    
    plt.plot(x, pdf, color=style['primary'], linewidth=2)
    plt.fill_between(x, pdf, color=style['secondary'], alpha=0.3)
    plt.gca().set_facecolor('#f5f6fa')
    plt.grid(True, alpha=0.3)
    plt.title(f"{distribution.capitalize()} Distribution", color=style['primary'], fontsize=14)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    return buf

@app.route('/')
def index():
    if 'user_config' not in session:
        return render_template('index.html', show_modal=True, STYLE_CONFIG=STYLE_CONFIG)
    return render_template('index.html',
                         show_modal=False,
                         style_class=f"style-{session['user_config']['style']}",
                         user=session['user_config'],
                         STYLE_CONFIG=STYLE_CONFIG)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        required_fields = ['name', 'roll_no', 'style']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        name = str(data['name']).strip()
        roll_no = str(data['roll_no']).strip()
        if not name or not roll_no:
            return jsonify({'error': 'Name and Roll No. cannot be empty'}), 400

        try:
            style_num = int(data['style'])
            if style_num < 0 or style_num > 10:
                raise ValueError
        except ValueError:
            return jsonify({'error': 'Invalid style number (0-10 only)'}), 400

        session.permanent = True
        session['user_config'] = {
            'name': name,
            'roll_no': roll_no,
            'style': style_num
        }
        return jsonify({'message': 'Configuration saved successfully'})

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get_pdf', methods=['POST'])
def get_pdf():
    try:
        user_config = session.get('user_config', {})
        data = request.get_json()
        distribution = data.get('distribution', 'gaussian')
        style = STYLE_CONFIG.get(user_config.get('style', 0))
        
        buf = generate_plot(distribution, style)
        return jsonify({
            'image': base64.b64encode(buf.getvalue()).decode('utf-8')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/speech_to_pdf', methods=['POST'])
def speech_to_pdf():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=5)
        
        text = r.recognize_google(audio).lower()
        distribution = next((dist for dist in ['uniform', 'rayleigh', 'binomial', 
                                             'poisson', 'laplacian', 'gaussian'] 
                           if dist in text), None)
        
        if not distribution:
            return jsonify({'error': 'No valid distribution detected'}), 400
        
        user_config = session.get('user_config', {})
        style = STYLE_CONFIG.get(user_config.get('style', 0))
        buf = generate_plot(distribution, style)
        
        return jsonify({
            'image': base64.b64encode(buf.getvalue()).decode('utf-8'),
            'distribution': distribution
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)