from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import cross_origin
from flask_marshmallow import Marshmallow
import json
import os
from glob import glob
import shutil

JSON_DATA_DIR = "json_data"

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json.dumps(data))


def read_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
    return data


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)

 
class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    participants = db.Column(db.String(500), nullable=False)


class ClassOnVideo(db.Model):
    __tablename__ = 'classes_on_video'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=False)
    counts = db.Column(db.Integer, nullable=False, unique=False)


class YoloTeamResults(db.Model):
    __tablename__ = 'yolo_team_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=False)
    score = db.Column(db.Float, nullable=False, unique=False)
    params = db.Column(db.String, nullable=False, unique=False)



class ClassOnVideoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ClassOnVideo

class TeamSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Team


class YoloTeamResultsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = YoloTeamResults



@app.route('/register_team', methods=["POST"])
@cross_origin()
def register_team():
    data = request.get_json()
    name = data["name"]
    participants = data["participants"]

    team_exists = len(Team.query.filter_by(name=name).all()) > 0
    if team_exists:
        return {
        "status": "fail",
        "message": "Команда с таким названием уже существует! Проявите фантазию и придуймайте новое название"
    }
    else:
        team = Team(
            name=name,
            participants=participants
        )
        db.session.add(team)
        db.session.commit()

        return {
            "status": "ok"
        }


@app.route('/get_classes', methods=["GET"])
@cross_origin()
def get_classes():
    classes = ClassOnVideoSchema(many=True).dump(ClassOnVideo.query.all())
    return {
        "status": "ok",
        "classes": classes
    }


@app.route('/get_teams', methods=["GET"])
@cross_origin()
def get_teams():
    teams = TeamSchema(many=True).dump(Team.query.all())
    return {
        "status": "ok",
        "teams": teams
    }


@app.route('/save_class_counts', methods=["POST"])
@cross_origin()
def save_class_counts():
    data = request.get_json()
    filename = f"{JSON_DATA_DIR}/{data['team']}.json"
    save_json(filename, data)
    return {
        "status": "ok"
    }
    

@app.route('/get_teams_class_counts', methods=["GET"])
@cross_origin()
def get_teams_class_counts():
    json_files = glob(f"{JSON_DATA_DIR}/*.json")
    teams_class_counts = {}
    classes = ClassOnVideo.query.all()
    for c in classes:
        teams_class_counts[c.name] = {
            "ground_truth": c.counts
        }
    for c in classes:
        for file in json_files:
            file_contents = read_json(file)
            teams_class_counts[c.name][file_contents["team"]] = file_contents[c.name]

    return {
        "status": "ok",
        "teams_class_counts": teams_class_counts
    }
    

@app.route('/commit_yolo_results', methods=["POST"])
@cross_origin()
def commit_yolo_results():
    data = request.get_json()
    name = data["name"]
    score = data["score"]
    params = data["params"]

    try:
        yoloTeamResults = YoloTeamResults(
            name=name,
            score=score,
            params=params
        )
        db.session.add(yoloTeamResults)
        db.session.commit()

        return {
            "status": "ok"
        }
    except:
        return {
            "status": "ok",
            "message": "К сожалению данные не отправились на сервер, попробуйте еще раз!"
        }
    

@app.route('/get_teams_yolo_results', methods=["GET"])
@cross_origin()
def get_teams_yolo_results():
    yolo_results = YoloTeamResultsSchema(many=True).dump(YoloTeamResults.query.all())

    return {
        "status": "ok",
        "teams_yolo_results": yolo_results
    }



if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        _classes = (("cat", 2), ("dog", 3), ("pep", 1))
        for c in _classes:
            c = ClassOnVideo(
                name=c[0],
                counts=c[1]
            )
            db.session.add(c)
            db.session.commit()
        if os.path.exists(JSON_DATA_DIR):
            shutil.rmtree(JSON_DATA_DIR)
        os.mkdir(JSON_DATA_DIR)
    app.run(host="0.0.0.0", port=5000)
