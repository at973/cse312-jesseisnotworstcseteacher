from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

@app.route('/') #Returns templates/index.html
def index():
    return render_template('index.html')

@app.route('/css/<css>') #Returns any file from css directory
def giveCSS(css):
    return send_from_directory('css', css)

@app.route('/js/<js>') #Returns any file from js directory
def giveJS(js):
    return send_from_directory('js', js)

@app.route('/images/<images>') #Returns any file from images directory
def giveJS(images):
    return send_from_directory('images', images)

if __name__ == '__main__':
    app.run(debug=True)
