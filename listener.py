from flask import Flask, request, send_file
app = Flask(__name__)

@app.route("/listener", methods = ["POST"])
def apiListener():
    newEvent = (list(request.form.keys())[0])
    printer = request.headers["Printer"]
    print(newEvent)
    match newEvent:
        case "serverStartup":
            print(f"Server has started up on {printer}")
        case "printStarted":
            print(f"Print has started on  {printer}")
        case "printFailed":
            print(f"Print has failed on {printer}")
        case "printDone":
            print(f"Print has finished on {printer}")
        case "printCancelled":
            print(f"Print has been cancelled on {printer}")
    return "ack"

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port= 8000)