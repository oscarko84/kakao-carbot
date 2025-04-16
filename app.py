from flask import Flask, request, jsonify
import gzip
import json

app = Flask(__name__)

# Load and normalize car data from .json.gz
with gzip.open("cardata.json.gz", "rt", encoding="utf-8") as f:
    raw_data = json.load(f)

# Build nested dictionary
car_tree = {}
for brand in raw_data:
    brand_name = brand["brandName"]
    car_tree[brand_name] = {}
    for model in brand["models"]:
        model_name = model["modelName"]
        car_tree[brand_name][model_name] = {}
        for trim in model["trims"]:
            trim_name = trim["trimName"]
            car_tree[brand_name][model_name][trim_name] = {}
            for year in trim["years"]:
                year_name = year["yearName"]
                parts = year.get("parts", [])
                car_tree[brand_name][model_name][trim_name][year_name] = parts

@app.route("/select", methods=["POST"])
def select():
    body = request.get_json(force=True, silent=True)
    if body is None:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "요청 형식이 올바르지 않습니다. [JSON 파싱 실패]"
                        }
                    }
                ]
            }
        }), 400

    action = body.get("action", {})
    params = action.get("params", {})

    step = params.get("step")
    brand = params.get("brand")
    model = params.get("model")
    trim = params.get("trim")
    year = params.get("year")

    buttons = []

    if step == "brand":
        buttons = list(car_tree.keys())

    elif step == "model" and brand in car_tree:
        buttons = list(car_tree[brand].keys())

    elif step == "trim" and brand in car_tree and model in car_tree[brand]:
        buttons = list(car_tree[brand][model].keys())

    elif step == "year" and brand and model and trim:
        buttons = list(car_tree[brand][model][trim].keys())

    elif step == "part" and brand and model and trim and year:
        part_list = car_tree[brand][model][trim][year]
        parts_text = "\n".join([f"{part['partName']}: {part['url']}" for part in part_list])
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": parts_text or "부품 정보가 없습니다."
                        }
                    }
                ]
            }
        })

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": f"{step.capitalize()} 선택",
                        "buttons": [{"action": "message", "label": b, "messageText": b} for b in buttons[:10]]
                    }
                }
            ]
        }
    })

if __name__ == "__main__":
    app.run(port=5000)
