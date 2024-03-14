from flask import Flask, url_for, redirect, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "Katia": generate_password_hash("hello"),
    "susan": generate_password_hash("bye")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route('/')
@auth.login_required
def index():
    body = "Hello, {}!".format(auth.current_user())
    body += f"""
                <form style="color:white" action="{url_for('endpoint')}" method="post", enctype="multipart/form-data">
                <input type="hidden" name="payload" value="shhh">
                <input type="text" name="inputTxt" value="alo">
                <button type="submit">Submit</button>
                </form>
                """
    return body

@app.route('/sneak')
def sneak():
    body = "Hello, {}!".format(auth.current_user())
    body += f"""
                <form style="color:white" action="{url_for('endpoint')}" method="post", enctype="multipart/form-data">
                <input type="hidden" name="payload" value="shhh">
                <input type="text" name="inputTxt" value="alo">
                <button type="submit">Submit</button>
                </form>
                """
    return body
@app.route('/endpoint',methods = ["POST"])
@auth.login_required()
def endpoint():
    print(request.form.get("payload"))
    print(request.form.get("inputTxt"))
    return redirect(url_for("index"))
if __name__ == '__main__':
    app.run()