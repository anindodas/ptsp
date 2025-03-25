import matplotlib
matplotlib.use('Agg')  # Required for headless environments
from flask import Flask, render_template, request, session, jsonify, send_from_directory
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os

app = Flask(__name__)

# Session configuration
app.config.update(
    SECRET_KEY='your-secret-key-123',  # Replace with your secret key
    SESSION_COOKIE_NAME='distplot_session',
    PERMANENT_SESSION_LIFETIME=604800,  # 1 week
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True  # Requires HTTPS
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
    """Generate plot image for the specified distribution"""
    plt.figure(figsize=(8, 6))
    
    # Configure plot based on distribution
    distributions = {
        'uniform': {
            'x': np.linspace(-3, 3, 1000),
            'pdf': lambda x: np.ones_like(x) * 0.5
        },
        'gaussian': {
            'x': np.linspace(-3, 3, 1000),
            'pdf': lambda x: np.exp(-x**2/2) / np.sqrt(2*np.pi)
        },
        'rayleigh': {
            'x': np.linspace(0, 3, 1000),
            'pdf': lambda x: x * np.exp(-x**2/2)
        },
        'binomial': {
            'x': np.arange(0, 20),
            'pdf': lambda x: np.array([np.math.comb(19, k) * (0.5**19) for k in x])
        },
        'poisson': {
            'x': np.arange(0, 20),
            'pdf': lambda x: np.exp(-5) * (5**x) / np.array([np.math.factorial(k) for k in x])
        },
        'laplacian': {
            'x': np.linspace(-3, 3, 1000),
            'pdf': lambda x: np.exp(-np.abs(x)) / 2
        }
    }

    config = distributions[distribution]
    x = config['x']
    pdf = config['pdf'](x)

    plt.plot(x, pdf, color=style['primary'], linewidth=2)
    plt.fill_between(x, pdf, color=style['secondary'], alpha=0.3)
    plt.gca().set_facecolor('#f5f6fa')
    plt.grid(True, alpha=0.3)
    plt.title(f"{distribution.capitalize()} Distribution", 
             color=style['primary'], fontsize=14)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    return buf

@app.route('/')
def index():
    """Main application route"""
    if 'user_config' not in session:
        return render_template('index.html', 
                            show_modal=True, 
                            STYLE_CONFIG=STYLE_CONFIG)
    
    return render_template('index.html',
                         show_modal=False,
                         style_class=f"style-{session['user_config']['style']}",
                         user=session['user_config'],
                         STYLE_CONFIG=STYLE_CONFIG)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', 
                             mimetype='image/vnd.microsoft.icon')

@app.route('/save_config', methods=['POST'])
def save_config():
    """Save user configuration to session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        # Validate required fields
        required_fields = ['name', 'roll_no', 'style']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        # Validate content
        name = str(data['name']).strip()
        roll_no = str(data['roll_no']).strip()
        if not name or not roll_no:
            return jsonify({'error': 'Name and Roll No. cannot be empty'}), 400

        # Validate style number
        try:
            style_num = int(data['style'])
            if style_num < 0 or style_num > 10:
                raise ValueError
        except ValueError:
            return jsonify({'error': 'Invalid style number (0-10 only)'}), 400

        # Save to persistent session
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
    """Generate and return PDF plot"""
    try:
        user_config = session.get('user_config', {})
        data = request.get_json()
        distribution = data.get('distribution', 'gaussian')
        style = STYLE_CONFIG.get(user_config.get('style', 0))
        
        if distribution not in ['uniform', 'gaussian', 'rayleigh', 
                               'binomial', 'poisson', 'laplacian']:
            raise ValueError('Invalid distribution')

        buf = generate_plot(distribution, style)
        return jsonify({
            'image': base64.b64encode(buf.getvalue()).decode('utf-8')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
