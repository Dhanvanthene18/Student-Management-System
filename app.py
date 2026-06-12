from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            return "Login Successful"

        return "Invalid Credentials"

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)