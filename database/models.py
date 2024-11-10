from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base


# Enhanced database models
class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, index=True)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    region = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    results = relationship("Results", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.full_name} ({self.tg_id})"


class Tests(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    created_by = Column(BigInteger, ForeignKey('users.tg_id'))

    # Configuration options stored as JSON
    settings = Column(JSON, default={})

    # Relationships
    questions = relationship("TestQuestions", back_populates="test", cascade="all, delete-orphan")
    results = relationship("Results", back_populates="test", cascade="all, delete-orphan")
    creator = relationship("Users", foreign_keys=[created_by])

    def __str__(self):
        return self.title

    @property
    def total_participants(self):
        return len(set(result.participant_id for result in self.results))

    @property
    def average_score(self):
        if not self.results:
            return 0
        correct_answers = sum(1 for result in self.results if result.is_correct)
        return (correct_answers / len(self.results)) * 100


class TestQuestions(Base):
    __tablename__ = 'testquestions'

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(String, nullable=False)  # Store as JSON array
    correct_option = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)  # Optional explanation for the correct answer
    media_content = Column(String, nullable=True)  # Store media details as JSON
    media_type = Column(String, nullable=True)
    poll_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    test = relationship("Tests", back_populates="questions")
    results = relationship("Results", back_populates="question", cascade="all, delete-orphan")

    def __str__(self):
        return f"Q{self.order}: {self.question[:50]}..."

    @property
    def success_rate(self):
        if not self.results:
            return 0
        correct_answers = sum(1 for result in self.results if result.is_correct)
        return (correct_answers / len(self.results)) * 100


class Results(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('testquestions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Link to Participants.id
    selected_option = Column(Integer, nullable=True)
    is_correct = Column(Boolean, default=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    test = relationship("Tests", back_populates="results")
    question = relationship("TestQuestions", back_populates="results")
    user = relationship('Users', back_populates='results')
