import atexit
import pydantic

from typing import Union
from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import Column, Integer, String, DateTime, create_engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask("app")
DSN = "postgresql://app:1234@127.0.0.1:5431/netology"
engine = create_engine(DSN)
Session = sessionmaker(bind=engine)
Base = declarative_base()

atexit.register(lambda: engine.dispose())


class Advertisement(Base):
    __tablename__ = "adverts"

    id = Column(Integer, primary_key=True)
    title = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    owner = Column(String(128), nullable=False)

    @classmethod
    def register(cls, session: Session, title: str, description: str, owner: str):
        new_advert = Advertisement(
            title=title,
            description=description,
            owner=owner,
        )
        session.add(new_advert)
        try:
            session.commit()
            return new_advert
        except IntegrityError:
            session.rollback()

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "creation_time": int(self.creation_time.timestamp()),
            "owner": self.owner,
            "id": self.id,
        }


Base.metadata.create_all(engine)


class HTTPError(Exception):
    def __init__(self, status_code: int, message: Union[str, list, dict]):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HTTPError)
def handle_invalid_usage(error):
    response = jsonify({"message": error.message})
    response.status_code = error.status_code
    return response


class CreateAdvertModel(pydantic.BaseModel):
    title: str
    description: str
    owner: str

    @pydantic.validator("title")
    def is_empty_title(cls, value: str):
        if len(value) == 0:
            raise ValueError("title can not be empty")
        return value

    @pydantic.validator("description")
    def is_empty_description(cls, value: str):
        if len(value) > 8:
            raise ValueError("description is too short")
        return value

    @pydantic.validator("owner")
    def is_empty_owner(cls, value: str):
        if len(value) == 0:
            raise ValueError("owner can not be empty")
        return value


def validate(unvalidated_data: dict, validation_model):
    try:
        return validation_model(**unvalidated_data).dict()
    except pydantic.ValidationError as er:
        raise HTTPError(400, er.errors())


def get_advert(advert_id: int, session: Session):
    advert = session.query(Advertisement).get(advert_id)
    if advert is None:
        raise HTTPError(404, 'advert_not_found')
    return advert


class AdvertView(MethodView):
    def get(self, advert_id: int):
        with Session() as session:
            advert = get_advert(advert_id, session)
            return jsonify({"title": advert.title, "owner": advert.owner, "date": advert.creation_time.isoformat()})

    def post(self):
        with Session() as session:
            register_data = validate(request.json, CreateAdvertModel)
            return Advertisement.register(session, **register_data).to_dict()

    def delete(self, advert_id):
        with Session() as session:
            advert = get_advert(advert_id, session)
            session.delete(advert)
            session.commit()
        return jsonify({"status": "success"})


app.add_url_rule("/advert/<int:advert_id>/", view_func=AdvertView.as_view("get_advert"), methods=["GET", "DELETE"])
app.add_url_rule("/advert/", view_func=AdvertView.as_view("register_advert"), methods=["POST"])

app.run()
