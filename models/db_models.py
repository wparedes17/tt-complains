import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class HighwayClassification(enum.Enum):
    HIGHWAY = "highway"
    FREEWAY = "freeway"
    LOCAL = "local"
    RURAL = "rural"

class HighwayCondition(enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class HighwayDifficult(enum.Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"

class UnloadingDifficult(enum.Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"

class Node(Base):
    __tablename__ = 'nodes'
    node_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    node_difficult = Column(Enum(UnloadingDifficult), nullable=False)

class Topic(Base):
    __tablename__ = 'topics'
    topic_id = Column(Integer, primary_key=True)
    topic_name = Column(String(100), nullable=False)

class Route(Base):
    __tablename__ = 'routes'
    route_id = Column(Integer, primary_key=True)
    start_node = Column(Integer, ForeignKey('nodes.node_id'), nullable=False)
    end_node = Column(Integer, ForeignKey('nodes.node_id'), nullable=False)
    price = Column(Float, nullable=False)
    distance = Column(Float, nullable=False)
    min_completion_time = Column(Float, nullable=False)  # in hours
    max_completion_time = Column(Float, nullable=False)  # in hours
    intermediate_nodes = Column(String(500))

class SimpleConnection(Base):
    __tablename__ = 'simple_connections'
    connection_id = Column(Integer, primary_key=True)
    start_node = Column(Integer, ForeignKey('nodes.node_id'), nullable=False)
    end_node = Column(Integer, ForeignKey('nodes.node_id'), nullable=False)
    highway_classification = Column(Enum(HighwayClassification), nullable=False)
    highway_condition = Column(Enum(HighwayCondition), nullable=False)
    highway_difficult = Column(Enum(HighwayDifficult), nullable=False)
    assault_risk = Column(Float, nullable=False)  # Scale from 0 to 1

class TrailerDriver(Base):
    __tablename__ = 'trailer_drivers'
    driver_id = Column(Integer, primary_key=True)
    age = Column(Integer, nullable=False)
    sex = Column(String(1), nullable=False)  # 'M' or 'F'
    location_id = Column(Integer, ForeignKey('nodes.node_id'), nullable=False)
    route_list = Column(String(500))
    number_routes = Column(Integer, default=0)
    trip_list = Column(String(1500))
    number_trips = Column(Integer, default=0)
    number_complains = Column(Integer, default=0)
    most_common_complain_topic = Column(Integer, ForeignKey('topics.topic_id'))
    most_common_route = Column(Integer, ForeignKey('routes.route_id'))
    status = Column(String(20), nullable=False)  # 'active', 'inactive', 'quit'
    salary = Column(Float, nullable=False)
    experience = Column(Integer, nullable=False)

class Complain(Base):
    __tablename__ = 'complains'
    complain_id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('trailer_drivers.driver_id'), nullable=False)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    connection_id = Column(Integer, ForeignKey('simple_connections.connection_id'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.topic_id'), nullable=False)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    comment = Column(String(5000))
    severity = Column(Integer, nullable=False)  # Scale from 1 to 5

class Trips(Base):
    __tablename__ = 'trips'
    trip_id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('trailer_drivers.driver_id'), nullable=False)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    complete = Column(Boolean, default=False)
    has_complain = Column(Boolean, default=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime)
    total_payment = Column(Float, nullable=False)