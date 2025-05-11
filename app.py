from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add_shift', methods=['POST'])
def add_shift():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # Предположим, что здесь ты записываешь в базу
    print("Полученные данные:", data)

    return jsonify({"message": "Shift added"}), 201

if __name__ == "__main__":
    app.run(debug=True)
